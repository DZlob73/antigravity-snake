import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import time
import json
import os

# Game Constants
GAME_WIDTH = 600
GAME_HEIGHT = 600
SPACE_SIZE = 25
BODY_PARTS = 3
SNAKE_COLOR = "#2ECC71"    # Emerald Green
FOOD_COLOR = "#E74C3C"     # Alizarin Red
BACKGROUND_COLOR = "#0F172A" # Deep Navy Blue
TEXT_COLOR = "#FFFFFF"
OBSTACLE_COLOR = "#475569"
SPEED = 120

class Snake:
    def __init__(self, canvas):
        self.body_size = BODY_PARTS
        self.coordinates = []
        self.squares = []
        self.canvas = canvas

        # Initial position: centered and visible
        start_x = (GAME_WIDTH // (2 * SPACE_SIZE)) * SPACE_SIZE
        start_y = (GAME_HEIGHT // (2 * SPACE_SIZE)) * SPACE_SIZE

        for i in range(0, BODY_PARTS):
            self.coordinates.append([start_x - i * SPACE_SIZE, start_y])

        for i, (x, y) in enumerate(self.coordinates):
            if i == 0:
                # Round Head
                segment = canvas.create_oval(x, y, x + SPACE_SIZE, y + SPACE_SIZE, 
                                            fill=SNAKE_COLOR, outline="#27AE60", width=2, tag="snake")
            elif i == len(self.coordinates) - 1:
                # Triangular Tail (Initial points Right for start alignment)
                points = [x, y, x, y + SPACE_SIZE, x + SPACE_SIZE, y + SPACE_SIZE // 2]
                segment = canvas.create_polygon(points, fill=SNAKE_COLOR, outline="#27AE60", tag="snake")
            else:
                # Square Body
                segment = canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, 
                                               fill=SNAKE_COLOR, outline="#27AE60", tag="snake")
            self.squares.append(segment)

    def draw_tail(self, x, y, px, py):
        # Draw a triangle at x, y pointing away from px, py
        s = SPACE_SIZE
        if x < px: # Tail is left of body, point Left
            points = [x + s, y, x + s, y + s, x, y + s // 2]
        elif x > px: # Tail is right of body, point Right
            points = [x, y, x, y + s, x + s, y + s // 2]
        elif y < py: # Tail is above body, point Up
            points = [x, y + s, x + s, y + s, x + s // 2, y]
        else: # Tail is below body, point Down
            points = [x, y, x + s, y, x + s // 2, y + s]
        
        return self.canvas.create_polygon(points, fill=SNAKE_COLOR, outline="#27AE60", tag="snake")

class Food:
    def __init__(self, canvas, obstacles_coords, snake_coords):
        while True:
            x = random.randint(0, (GAME_WIDTH // SPACE_SIZE) - 1) * SPACE_SIZE
            y = random.randint(0, (GAME_HEIGHT // SPACE_SIZE) - 1) * SPACE_SIZE
            self.coordinates = [x, y]
            if self.coordinates not in obstacles_coords and self.coordinates not in snake_coords:
                break
        canvas.create_oval(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=FOOD_COLOR, tag="food")

class Obstacles:
    def __init__(self, canvas, snake_coords):
        self.coordinates = []
        self.canvas = canvas
        for _ in range(8):
            while True:
                x = random.randint(0, (GAME_WIDTH // SPACE_SIZE) - 1) * SPACE_SIZE
                y = random.randint(0, (GAME_HEIGHT // SPACE_SIZE) - 1) * SPACE_SIZE
                coord = [x, y]
                # Avoid snake and other obstacles
                if coord not in snake_coords and coord not in self.coordinates:
                    # Keep safe distance from snake head at start
                    if abs(x - snake_coords[0][0]) > SPACE_SIZE * 3 or abs(y - snake_coords[0][1]) > SPACE_SIZE * 3:
                        self.coordinates.append(coord)
                        break
        
        for x, y in self.coordinates:
            rect = canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, 
                                    fill=OBSTACLE_COLOR, outline="#334155", width=2, tag="obstacle")
            # Store rectangles to be able to delete them
            if not hasattr(self, 'squares'): self.squares = {}
            self.squares[(x, y)] = rect

    def delete_at(self, x, y):
        if (x, y) in self.squares:
            self.canvas.delete(self.squares[(x, y)])
            del self.squares[(x, y)]
            self.coordinates.remove([x, y])

class Projectile:
    def __init__(self, canvas, x, y, direction):
        self.canvas = canvas
        self.coordinates = [x, y]
        self.direction = direction
        # Bullet looks like a small glowing square
        offset = SPACE_SIZE // 4
        self.shape = canvas.create_rectangle(x + offset, y + offset, 
                                             x + SPACE_SIZE - offset, y + SPACE_SIZE - offset, 
                                             fill="#F1C40F", outline="#F39C12", tag="bullet")

    def move(self):
        if self.direction == "up":
            self.coordinates[1] -= SPACE_SIZE
        elif self.direction == "down":
            self.coordinates[1] += SPACE_SIZE
        elif self.direction == "left":
            self.coordinates[0] -= SPACE_SIZE
        elif self.direction == "right":
            self.coordinates[0] += SPACE_SIZE
        
        self.canvas.coords(self.shape, 
                           self.coordinates[0] + SPACE_SIZE//4, self.coordinates[1] + SPACE_SIZE//4,
                           self.coordinates[0] + SPACE_SIZE*3//4, self.coordinates[1] + SPACE_SIZE*3//4)

class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Antigravity Snake")
        self.root.configure(bg=BACKGROUND_COLOR)
        self.root.resizable(False, False)

        self.score = 0
        self.direction = 'right'
        self.start_time = time.time()
        self.is_game_over = False



        # Header layout: Player Name and Record
        self.header_frame = tk.Frame(root, bg="#1E293B")
        self.header_frame.pack(fill="x")

        self.name_label = tk.Label(self.header_frame, text="PLAYER: ...", 
                 font=('consolas', 12, 'bold'), bg="#1E293B", fg="#94A3B8")
        self.name_label.pack(side="left", padx=20, pady=5)
        
        self.record_label = tk.Label(self.header_frame, 
                                     text="RECORD: ...", 
                                     font=('consolas', 12, 'bold'), bg="#1E293B", fg="#F59E0B")
        self.record_label.pack(side="right", padx=20, pady=5)

        # Stats layout: Score, Length, and Time in one row
        self.stats_frame = tk.Frame(root, bg=BACKGROUND_COLOR)
        self.stats_frame.pack(pady=10, fill="x", padx=20)

        self.label = tk.Label(self.stats_frame, text="SCORE: 0", 
                              font=('consolas', 18, 'bold'), bg=BACKGROUND_COLOR, fg=SNAKE_COLOR)
        self.label.pack(side="left", expand=True)

        self.length_label = tk.Label(self.stats_frame, text="LENGTH: 3", 
                                   font=('consolas', 18, 'bold'), bg=BACKGROUND_COLOR, fg="#3498DB")
        self.length_label.pack(side="left", expand=True)

        self.time_label = tk.Label(self.stats_frame, text="TIME: 0s", 
                                 font=('consolas', 18, 'bold'), bg=BACKGROUND_COLOR, fg="#F1C40F")
        self.time_label.pack(side="left", expand=True)

        self.canvas = tk.Canvas(root, bg="#0F172A", height=GAME_HEIGHT, width=GAME_WIDTH, 
                                highlightthickness=2, highlightbackground="#1E293B")
        self.canvas.pack(padx=20)

        self.exit_button = tk.Button(root, text="EXIT GAME", command=self.confirm_exit, 
                                     font=('consolas', 12, 'bold'), bg="#C0392B", fg="white",
                                     activebackground="#E74C3C", activeforeground="white",
                                     relief="flat", width=15, height=2)
        self.exit_button.pack(pady=20)


        self.root.bind('<Left>', lambda event: self.change_direction('left'))
        self.root.bind('<Right>', lambda event: self.change_direction('right'))
        self.root.bind('<Up>', lambda event: self.change_direction('up'))
        self.root.bind('<Down>', lambda event: self.change_direction('down'))
        self.root.bind('<Escape>', lambda event: self.confirm_exit())
        self.root.bind('<Return>', lambda event: self.restart_game())
        self.root.bind('<space>', lambda event: self.fire_projectile())

        self.projectiles = []
        self.head_details = [] # Eyes and tongue

        # Load High Score and Ask for Player Name (AFTER centering the real-sized window)
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.update()

        self.high_score_data = self.load_high_score()
        self.player_name = simpledialog.askstring("Name", "Enter your name:", parent=root)
        if not self.player_name or self.player_name.strip() == "":
            self.player_name = "Player"

        # Update name displays
        self.name_label.config(text=f"PLAYER: {self.player_name.upper()}")
        self.record_label.config(text=f"RECORD: {self.high_score_data['name'].upper()} ({self.high_score_data['score']})")

        self.snake = Snake(self.canvas)
        self.obstacles = Obstacles(self.canvas, self.snake.coordinates)
        self.food = Food(self.canvas, self.obstacles.coordinates, self.snake.coordinates)

        self.update_ui()
        self.update_projectiles() # Start separate projectile loop
        self.next_turn()

    def next_turn(self):
        x, y = self.snake.coordinates[0]

        if self.direction == "up":
            y -= SPACE_SIZE
        elif self.direction == "down":
            y += SPACE_SIZE
        elif self.direction == "left":
            x -= SPACE_SIZE
        elif self.direction == "right":
            x += SPACE_SIZE

        self.snake.coordinates.insert(0, (x, y))

        # Convert old head to body segment (square)
        if self.snake.squares:
            old_x, old_y = self.snake.coordinates[1]
            self.canvas.delete(self.snake.squares[0])
            body_segment = self.canvas.create_rectangle(old_x, old_y, old_x + SPACE_SIZE, old_y + SPACE_SIZE, 
                                                        fill=SNAKE_COLOR, outline="#27AE60", tag="snake")
            self.snake.squares[0] = body_segment

        head = self.canvas.create_oval(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=SNAKE_COLOR, outline="#27AE60", width=2, tag="snake")
        self.snake.squares.insert(0, head)

        # Draw eyes and tongue
        self.draw_head_details(x, y, self.direction)

        if x == self.food.coordinates[0] and y == self.food.coordinates[1]:
            self.score += 1
            self.label.config(fg="#F1C40F")
            self.root.after(200, lambda: self.label.config(fg=SNAKE_COLOR))
            
            self.canvas.delete("food")
            self.food = Food(self.canvas, self.obstacles.coordinates, self.snake.coordinates)
        else:
            self.canvas.delete(self.snake.squares[-1])
            del self.snake.squares[-1]
            del self.snake.coordinates[-1]
            
            # Now update the NEW tail to be triangular
            tx, ty = self.snake.coordinates[-1]
            px, py = self.snake.coordinates[-2] # Segment before tail
            self.canvas.delete(self.snake.squares[-1])
            self.snake.squares[-1] = self.snake.draw_tail(tx, ty, px, py)

        if self.check_collisions():
            self.is_game_over = True
            self.game_over()
        else:
            self.loop_id = self.root.after(SPEED, self.next_turn)

    def restart_game(self):
        if hasattr(self, 'loop_id'):
            self.root.after_cancel(self.loop_id)
        if hasattr(self, 'ui_loop_id'):
            self.root.after_cancel(self.ui_loop_id)
        if hasattr(self, 'projectile_loop_id'):
            self.root.after_cancel(self.projectile_loop_id)
        
        self.score = 0
        self.direction = 'right'
        self.start_time = time.time()
        self.is_game_over = False
        self.label.config(fg=SNAKE_COLOR)
        self.canvas.delete(tk.ALL)
        self.projectiles = []
        self.snake = Snake(self.canvas)
        self.obstacles = Obstacles(self.canvas, self.snake.coordinates)
        self.food = Food(self.canvas, self.obstacles.coordinates, self.snake.coordinates)
        self.update_ui()
        self.update_projectiles()
        self.next_turn()

    def fire_projectile(self):
        if not self.is_game_over:
            # Fire from snake head in current direction
            head_x, head_y = self.snake.coordinates[0]
            self.projectiles.append(Projectile(self.canvas, head_x, head_y, self.direction))

    def draw_head_details(self, x, y, direction):
        # Clear old details
        for detail in self.head_details:
            self.canvas.delete(detail)
        self.head_details = []

        s = SPACE_SIZE
        # Eye and Tongue positions based on direction
        tx, ty = (x+s/2 if direction in ["up", "down"] else (x+s if direction=="right" else x)), \
                 (y+s/2 if direction in ["left", "right"] else (y+s if direction=="down" else y))

        if direction == "right":
            e1 = (x + s*0.7, y + s*0.3); e2 = (x + s*0.7, y + s*0.7)
            mx, my = tx + 8, ty
            forks = [(mx + 6, my - 4), (mx + 6, my + 4)]
        elif direction == "left":
            e1 = (x + s*0.3, y + s*0.3); e2 = (x + s*0.3, y + s*0.7)
            mx, my = tx - 8, ty
            forks = [(mx - 6, my - 4), (mx - 6, my + 4)]
        elif direction == "up":
            e1 = (x + s*0.3, y + s*0.3); e2 = (x + s*0.7, y + s*0.3)
            mx, my = tx, ty - 8
            forks = [(mx - 4, my - 6), (mx + 4, my - 6)]
        else: # down
            e1 = (x + s*0.3, y + s*0.7); e2 = (x + s*0.7, y + s*0.7)
            mx, my = tx, ty + 8
            forks = [(mx - 4, my + 6), (mx + 4, my + 6)]

        # Eyes (black dots)
        eye_size = 2
        for ex, ey in [e1, e2]:
            eye = self.canvas.create_oval(ex-eye_size, ey-eye_size, ex+eye_size, ey+eye_size, fill="black", tag="detail")
            self.head_details.append(eye)
        
        # Tongue (red forked line)
        s1 = self.canvas.create_line(tx, ty, mx, my, fill="red", width=2, tag="detail")
        t1 = self.canvas.create_line(mx, my, forks[0][0], forks[0][1], fill="red", width=2, tag="detail")
        t2 = self.canvas.create_line(mx, my, forks[1][0], forks[1][1], fill="red", width=2, tag="detail")
        self.head_details.extend([s1, t1, t2])

    def update_projectiles(self):
        new_projectiles = []
        for p in self.projectiles:
            p.move()
            px, py = p.coordinates

            # Hit obstacle?
            hit_obstacle = False
            for ox, oy in list(self.obstacles.coordinates):
                if px == ox and py == oy:
                    self.obstacles.delete_at(ox, oy)
                    self.canvas.delete(p.shape)
                    hit_obstacle = True
                    break
            
            if hit_obstacle:
                continue

            # Out of bounds?
            if px < 0 or px >= GAME_WIDTH or py < 0 or py >= GAME_HEIGHT:
                self.canvas.delete(p.shape)
                continue
            
            new_projectiles.append(p)
        
        self.projectiles = new_projectiles

        # Faster loop for projectiles (e.g., 30ms)
        if not self.is_game_over:
            self.projectile_loop_id = self.root.after(30, self.update_projectiles)

    def update_ui(self):
        if not self.is_game_over:
            elapsed_time = int(time.time() - self.start_time)
            self.label.config(text="SCORE: {}".format(self.score))
            self.length_label.config(text="LENGTH: {}".format(len(self.snake.coordinates)))
            self.time_label.config(text="TIME: {}s".format(elapsed_time))
            # Schedule the next UI update (twice a second is plenty for the timer)
            self.ui_loop_id = self.root.after(500, self.update_ui) 

    def change_direction(self, new_direction):
        if new_direction == 'left':
            if self.direction != 'right':
                self.direction = new_direction
        elif new_direction == 'right':
            if self.direction != 'left':
                self.direction = new_direction
        elif new_direction == 'up':
            if self.direction != 'down':
                self.direction = new_direction
        elif new_direction == 'down':
            if self.direction != 'up':
                self.direction = new_direction

    def check_collisions(self):
        x, y = self.snake.coordinates[0]

        if x < 0 or x >= GAME_WIDTH:
            return True
        elif y < 0 or y >= GAME_HEIGHT:
            return True

        for body_part in self.snake.coordinates[1:]:
            if x == body_part[0] and y == body_part[1]:
                return True

        for obstacle in self.obstacles.coordinates:
            if x == obstacle[0] and y == obstacle[1]:
                return True

        return False

    def game_over(self):
        self.is_game_over = True
        self.canvas.delete(tk.ALL)
        elapsed_time = int(time.time() - self.start_time)

        # Check for new high score
        new_record = False
        if self.score > self.high_score_data['score']:
            self.high_score_data = {'name': self.player_name, 'score': self.score}
            self.save_high_score(self.high_score_data)
            self.record_label.config(text=f"RECORD: {self.player_name.upper()} ({self.score})")
            new_record = True
        
        self.canvas.create_text(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2 - 100,
                                font=('consolas', 50, 'bold'), text="GAME OVER", fill="#E74C3C", tag="gameover")
        
        if new_record:
            self.canvas.create_text(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2 - 30,
                                    font=('consolas', 20, 'italic'), text="!!! NEW RECORD !!!", fill="#F1C40F", tag="gameover")

        stats_text = f"SCORE: {self.score}  |  LENGTH: {len(self.snake.coordinates)}  |  TIME: {elapsed_time}s"
        self.canvas.create_text(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2 + 30,
                                font=('consolas', 20), text=stats_text, fill="white", tag="gameover")
        
        self.canvas.create_text(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2 + 110,
                                font=('consolas', 18, 'bold'), text="Press ENTER to Restart", fill="#F1C40F", tag="gameover")
        self.canvas.create_text(self.canvas.winfo_width()/2, self.canvas.winfo_height()/2 + 150,
                                font=('consolas', 12), text="Press ESC or Click Exit to Close", fill="#95A5A6", tag="gameover")

    def load_high_score(self):
        try:
            if os.path.exists("highscores.json"):
                with open("highscores.json", "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"name": "None", "score": 0}

    def save_high_score(self, data):
        try:
            with open("highscores.json", "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def confirm_exit(self):
        if messagebox.askokcancel("Exit", "Do you really want to exit?"):
            self.root.destroy()

def main():
    root = tk.Tk()
    SnakeGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
