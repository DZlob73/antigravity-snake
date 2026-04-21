import msvcrt
import sys

def main():
    print("Hello World!")
    print("Нажмите клавишу 'Y' (или 'y') для завершения работы.")
    
    while True:
        # Check if a key was pressed
        if msvcrt.kbhit():
            # Get the key pressed
            char = msvcrt.getch()
            try:
                # Try to decode the key
                key = char.decode('utf-8').lower()
                if key == 'y':
                    print("\nЗавершение программы...")
                    sys.exit(0)
            except UnicodeDecodeError:
                continue

if __name__ == "__main__":
    main()
