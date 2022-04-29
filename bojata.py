#!/usr/bin/env python3
import logging
import os
import re
import tkinter as tk
import tkinter.font

import cups
from PIL import Image, ImageDraw
from serial import Serial, SerialException
from serial.tools.list_ports import comports

BAUD_RATE = 115200
TASK_DELAY = 0
RECONNECT_DELAY = 1000
PRINT_DELAY = 10000

COMPORT_PATTERN = re.compile(r'/dev/ttyACM\d+|COM\d+')
PRINT_FLAG = '@'
RGB_PATTERN = re.compile(rf'(\d+),(\d+),(\d+)(?:;(\d+))?({PRINT_FLAG})?\r?\n')  # R,G,B[;I]["@"]
PRINT_FILENAME = 'print.png'

logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s',
                    level=os.getenv('LOGLEVEL', 'INFO').upper())

# Initialize serial connection
ser = Serial(baudrate=BAUD_RATE)

def serial_connect():
    """Open a serial connection on the first available matching port."""
    ports = [cp.device for cp in comports()]
    matching_ports = [p for p in ports if COMPORT_PATTERN.match(p)]
    logging.debug("All available ports: %s", ports)
    logging.debug("Matching ports: %s", matching_ports)
    if not matching_ports:
        raise SerialException("No serial device available")
    ser.port = matching_ports[0]
    ser.open()
    logging.info("Connected to serial device on %s at %d baud",
                 ser.port, BAUD_RATE)

serial_connect()

# Initialize connection to CUPS server
cups_conn = cups.Connection()

# Initialize GUI
root = tk.Tk()
root.title('bojata')
root.attributes('-fullscreen', True)
tk.font.nametofont('TkDefaultFont').configure(size=36)
canvas = tk.Canvas(root, borderwidth=0, highlightthickness=0)
canvas.pack(expand=True, fill=tk.BOTH)

def swatch_bounds(w, h):
    w_color = int(w * 15 / 16)
    h_rgb = int(h / 3)
    return w_color, h_rgb

# Draw RGB swatches on the right edge
w = root.winfo_screenwidth()
h = root.winfo_screenheight()
w_color, h_rgb = swatch_bounds(w, h)
for i, c in enumerate(('#ff0000', '#00ff00', '#0000ff')):
    canvas.create_rectangle(w_color, i*h_rgb, w, (i+1)*h_rgb,
                            width=0, fill=c)

def create_outlined_text(x, y, *args, **kw):
    """Draw white-on-black outlined text."""
    kw['fill'] = 'black'
    canvas.create_text(x+2, y+2, *args, **kw)
    kw['fill'] = 'white'
    canvas.create_text(x, y, *args, **kw)

def task():
    """Read RGB value from serial, display it on the screen, and (optionally)
    send it for printing.
    """
    try:
        if not ser.is_open:
            serial_connect()

        # Discard buffered bytes if they are arriving too quickly
        if ser.in_waiting > 0:
            logging.info("Discarding %d buffered bytes", ser.in_waiting)
            ser.reset_input_buffer()

        # Read the upcoming line and check if it's a valid RGB message
        line = ser.readline().decode('utf8')
        logging.debug("%sbuffer: %d", line, ser.in_waiting)
        if m := RGB_PATTERN.match(line):
            r, g, b, i, pf = m.groups()
            r, g, b = map(int, (r, g, b))

            # If ambient light intensity is present, adjust color accordingly
            if i is not None:
                total = int(i) or 1
                r = int(r / total * 255)
                g = int(g / total * 255)
                b = int(b / total * 255)

            # Draw colored area
            color = f'#{r:02x}{g:02x}{b:02x}'
            canvas.create_rectangle(0, 0, w_color, h,
                                    width=0, fill=color)
            root.update()

            # If print flag is present, start printing the color
            if pf is not None:
                assert pf == PRINT_FLAG
                create_outlined_text(w_color/2, h/2,
                                     text=f"Printing...\n{color}")
                root.update()

                root.after(0, start_printing, color)
                root.after(PRINT_DELAY, task)
                return

        root.after(TASK_DELAY, task)

    except (SerialException, OSError):
        ser.close()
        logging.warning("Serial device disconnected! Retrying in %g s...",
                        RECONNECT_DELAY / 1000)
        root.after(RECONNECT_DELAY, task)

def start_printing(color):
    logging.debug("Generating image for %s...", color)
    img = Image.new(mode='RGB', size=(874, 1240), color='white')  # A5 @ 150 PPI
    img_draw_swatch(img, 600, 56, 256, 168, color)
    img.save(PRINT_FILENAME, 'PNG')

    logging.info("Starting printing for %s...", color)
    for printer in cups_conn.getPrinters().keys():
        title = f'bojata-{color}'
        options = {'media': 'A5'}
        cups_conn.printFile(printer, PRINT_FILENAME, title, options)

def img_draw_swatch(img, x, y, w, h, color):
    d = ImageDraw.Draw(img)
    w_color, h_rgb = swatch_bounds(w, h)
    d.rectangle((x,         y,         x+w_color, y+h),       fill=color)
    d.rectangle((x+w_color, y,         x+w,       y+h_rgb),   fill='#ff0000')
    d.rectangle((x+w_color, y+h_rgb,   x+w,       y+2*h_rgb), fill='#00ff00')
    d.rectangle((x+w_color, y+2*h_rgb, x+w,       y+3*h_rgb), fill='#0000ff')

def on_close():
    """Close serial connection and exit script."""
    ser.close()
    exit()

root.after(TASK_DELAY, task)  # Schedule first task
root.protocol('WM_DELETE_WINDOW', on_close)
root.mainloop()
