import tkinter as tk
import pygame
import os
from threading import Thread, Event


# Function to initialize the embedded Pygame
def embed_pygame(root, frame):
    # Set up the frame's ID for embedding
    os.environ['SDL_WINDOWID'] = str(frame.winfo_id())
    os.environ['SDL_VIDEODRIVER'] = 'windib'  # This might be needed for Windows

    # Initialize Pygame and create a display surface
    pygame.init()
    screen = pygame.display.set_mode((frame.winfo_width(), frame.winfo_height()))
    screen.fill((255, 255, 255))  # Fill with white background
    pygame.display.update()

    return screen


# Function to update Pygame's display and handle events
def pygame_event_loop(screen, stop_event):
    # Run the Pygame loop until `stop_event` is set
    while not stop_event.is_set():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_event.set()  # Set the event if Pygame is closed

        # Draw a circle at the center for demonstration
        screen.fill((255, 255, 255))  # Clear screen
        pygame.draw.circle(screen, (255, 0, 0), (screen.get_width() // 2, screen.get_height() // 2), 50)
        pygame.display.update()

    pygame.quit()  # Quit Pygame when the loop ends


# Main Tkinter window setup
root = tk.Tk()
root.title("Pygame in Tkinter Example")

# Set up a frame within Tkinter to embed the Pygame display
embed_frame = tk.Frame(root, width=500, height=500)
embed_frame.pack()

# Wait for the frame to be fully created and embedded before initializing Pygame
root.update_idletasks()
pygame_screen = embed_pygame(root, embed_frame)

# Create a `stop_event` to signal the Pygame thread when to stop
stop_event = Event()

# Start the Pygame loop in a separate thread
pygame_thread = Thread(target=pygame_event_loop, args=[pygame_screen, stop_event])
pygame_thread.start()


# Function to handle window close event
def on_closing():
    stop_event.set()  # Signal the Pygame thread to stop
    pygame_thread.join()  # Wait for the thread to finish
    root.destroy()  # Close the Tkinter window


# Override the Tkinter window close event
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the Tkinter main loop
root.mainloop()