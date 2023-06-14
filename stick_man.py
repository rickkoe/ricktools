import time
import sys
import threading
import termios
import tty


# Function to clear the console screen
def clear_screen():
    print("\033c", end="")


# Function to animate the stickman dance
def animate_dance():
    frames = [
        '''
            o
           /|\\
           / \\
        ''',
        '''
            o
           /|\\
           / 
        ''',
        '''
            o
           /|\\
           
        ''',
        '''
            o
           /|
           
        ''',
        '''
            o
            |
           
        ''',
        '''
            o
            
           
        '''
    ]

    # Variables to track the stickman's limbs positions
    left_arm = "/"
    right_arm = "\\"
    left_leg = "/"
    right_leg = "\\"

    # Loop through the frames
    start_time = time.time()
    while time.time() - start_time < 60:
        clear_screen()
        print(frames[0])
        print(f"Left arm: {left_arm} | Right arm: {right_arm} | Left leg: {left_leg} | Right leg: {right_leg}")
        time.sleep(0.5)  # Adjust the sleep time to change the animation speed

        # Rotate the limbs based on keyboard input
        if kbhit():
            key = getch()
            if key == 'a':
                left_arm, right_arm = right_arm, left_arm
            elif key == 's':
                left_leg, right_leg = right_leg, left_leg

        # Rotate the frames
        frames.append(frames.pop(0))


# Function to check if a key has been pressed
def kbhit():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch != ''


# Function to get a single character from input
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


# Start the dance animation
animation_thread = threading.Thread(target=animate_dance)
animation_thread.start()

# Wait for the animation thread to finish
animation_thread.join()
