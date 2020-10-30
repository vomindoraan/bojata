import logging
import re
import tkinter as tk

from serial import Serial, SerialException
from serial.tools.list_ports import comports

BAUD_RATE = 9600
COMPORT_PATTERN = re.compile(r'/dev/ttyACM\d+|COM\d+')
RGB_PATTERN = re.compile(r'(\d+),(\d+),(\d+)(?:,(\d+))?\r?\n')  # R,G,B[;I]
TASK_DELAY = 0
RECONNECT_DELAY = 1000

logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)

# Initialize serial connection
ser = Serial(baudrate=BAUD_RATE)

def serial_connect():
    """Open a serial connection on the first available appropriate comport."""
    ports = [p.device for p in comports() if COMPORT_PATTERN.match(p.device)]
    if not ports:
        raise SerialException("No serial device available")
    ser.port = ports[0]
    ser.open()
    logging.info("Connected to serial device on %s at %d baud",
                 ser.port, BAUD_RATE)

serial_connect()

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

def task():
    """Read RGB value from serial and display it on the screen."""
    try:
        if not ser.is_open:
            serial_connect()

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
    except SerialException:
        ser.close()
        root.after(RECONNECT_DELAY, task)
        logging.warning("Serial device disconnected! Retrying in %g s...",
                        RECONNECT_DELAY / 1000)
    else:
        root.after(TASK_DELAY, task)

def on_close():
    """Close serial connection and exit script."""
    ser.close()
    exit()

root.after(TASK_DELAY, task)  # Schedule first task
root.protocol('WM_DELETE_WINDOW', on_close)
root.mainloop()
