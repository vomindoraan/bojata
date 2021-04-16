#!/usr/bin/env python3
import logging
import os
import re
import tkinter as tk
import tkinter.font

import cups
from cups_notify import Subscriber
from PIL import Image, ImageDraw
from serial import Serial, SerialException
from serial.tools.list_ports import comports

BAUD_RATE = 115200
TASK_DELAY = 0
RECONNECT_DELAY = 1000

COMPORT_PATTERN = re.compile(r'/dev/ttyACM\d+|COM\d+')
PRINT_FLAG = "@"
RGB_PATTERN = re.compile(rf'(\d+),(\d+),(\d+)(?:;(\d+))?({PRINT_FLAG})?\r?\n')  # R,G,B[;I]["@"]

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
conn = cups.Connection()

# Initialize GUI
root = tk.Tk()
root.title('bojata')
root.attributes('-fullscreen', True)
tk.font.nametofont('TkDefaultFont').configure(size=36)
canvas = tk.Canvas(root, borderwidth=0, highlightthickness=0)
canvas.pack(expand=True, fill=tk.BOTH)

# Draw RGB swatches on the right edge
w = root.winfo_screenwidth()
h = root.winfo_screenheight()
w_rgb = w - w / 16
h_rgb = h / 3
colors = ('#ff0000', '#00ff00', '#0000ff')
for i, c in enumerate(colors):
    canvas.create_rectangle(w_rgb, i*h_rgb, w, (i+1)*h_rgb,
                            width=0, fill=c)

def create_outlined_text(x, y, *args, **kw):
    """Draw white-on-black outlined text."""
    kw['fill'] = 'black'
    canvas.create_text(x+2, y+2, *args, **kw)
    kw['fill'] = 'white'
    canvas.create_text(x, y, *args, **kw)

is_printing = False  # Global printing state flag

def task():
    """Read RGB value from serial and display it on the screen."""
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
            canvas.create_rectangle(0, 0, w_rgb, h,
                                    width=0, fill=color)

            # If print flag is present, start printing the color
            if pf is not None:
                assert pf == PRINT_FLAG
                create_outlined_text(w_rgb/2, h/2,
                                     text=f"Printing...\n{color}")
                start_printing(color)

            root.update()
    except (SerialException, OSError):
        ser.close()
        logging.warning("Serial device disconnected!")
        if not is_printing:
            logging.info("Retrying in %g s...", RECONNECT_DELAY / 1000)
            root.after(RECONNECT_DELAY, task)
    else:
        if not is_printing:
            root.after(TASK_DELAY, task)

def start_printing(color):
    with Image.open('template.png') as im:
        x0 = (im.size[0] - w_rgb) / 2
        x1 = x0 + w_rgb
        y0 = (im.size[1] - h) / 2
        y1 = y0 + h

        draw = ImageDraw.Draw(im)
        draw.rectangle((x0, x1, y0, y1), fill=color)

        im.save('template_test1.png', 'PNG')

        for printer_name in conn.getPrinters().keys():
            conn.printFile(printer_name, 'template_test1.png', '', {})

    global is_printing
    is_printing = True

def on_print_done(evt):

    is_printing = False

def on_close():
    """Close serial connection and exit script."""
    ser.close()
    exit()

root.after(TASK_DELAY, task)  # Schedule first task
root.protocol('WM_DELETE_WINDOW', on_close)
root.mainloop()
