import logging
import re
import tkinter as tk

import serial
from serial.tools.list_ports import comports

BAUD_RATE = 9600
RGB_PATTERN = re.compile(r'(\d+),(\d+),(\d+)(?:,(\d+))?\r?\n')  # R,G,B[;I]
TASK_DELAY = 0

logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)

# Connect to serial device
try:
    port = comports()[0].device
    ser = serial.Serial(port, BAUD_RATE)
    logging.info("Connected to serial device on %s at %d baud", port, BAUD_RATE)
except (IndexError, serial.SerialException) as e:
    raise FileNotFoundError("No serial device found") from e

# Initialize GUI
root = tk.Tk()
root.title('bojata')
root.attributes('-fullscreen', True)
canvas = tk.Canvas(root, borderwidth=0, highlightthickness=0)
canvas.pack(expand=True, fill=tk.BOTH)

# Draw RGB swatches on the right edge
w = root.winfo_screenwidth()
h = root.winfo_screenheight()
w_rgb = w - w / 16
h_rgb = h / 3
colors = ('#ff0000', '#00ff00', '#0000ff')
for i, c in enumerate(colors):
    canvas.create_rectangle(w_rgb, i*h_rgb,
                            w, (i+1)*h_rgb,
                            width=0, fill=c)
root.update()


def task():
    """Read RGB value from serial and display it on the screen."""
    try:
        line = ser.readline().decode('utf8')
        logging.debug(line)

        if m := RGB_PATTERN.match(line):
            r, g, b, i = m.groups()
            r, g, b = map(int, (r, g, b))

            # If ambient light intensity is present, adjust color accordingly
            if i is not None:
                total = int(i) or 1
                r = int(r / total * 255)
                g = int(g / total * 255)
                b = int(b / total * 255)

            # Draw colored area
            color = f'#{r:02x}{g:02x}{b:02x}'
            canvas.create_rectangle(0, 0,
                                    w_rgb, h,
                                    width=0, fill=color)
            root.update()
    except Exception as e:
        logging.exception(e)
    finally:
        root.after(TASK_DELAY, task)

root.after(TASK_DELAY, task)  # Schedule first task
root.protocol('WM_DELETE_WINDOW', exit)  # Exit on close
root.mainloop()  # Start main GUI loop
