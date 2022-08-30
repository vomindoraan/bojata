#!/usr/bin/env python3
import logging
import os
import re
import tkinter as tk
import tkinter.font

from PIL import Image, ImageDraw, ImageFont
from cups import Connection as CupsConnection
from serial import Serial, SerialException
from serial.tools.list_ports import comports


logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(message)s',
                    level=os.getenv('LOGLEVEL', 'INFO').upper())

SERIAL_BAUD_RATE = 115200
SERIAL_BUFFER_LIMIT = 12
TASK_DELAY = 0
RECONNECT_DELAY = 1000
PRINT_DELAY = 10000

PRINT_FILENAME = 'print.png'
PRINT_FONT = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf', 96)
PRINT_FLAG = '@'
RGB_PATTERN = re.compile(fr'(\d+),(\d+),(\d+)(?:;(\d+))?({PRINT_FLAG})?\r?\n')  # R,G,B[;I]["@"]
COMPORT_PATTERN = re.compile(r'/dev/ttyACM\d+|COM\d+')

SWATCH_COLORS = ('#ff0000', '#00ff00', '#0000ff')

# Globals
serial:     Serial
cups:       CupsConnection
frame:      tk.Tk
canvas:     tk.Canvas
curr_color: str


def serial_connect():
    """Open a serial connection on the first available matching port."""
    ports = [cp.device for cp in comports()]
    matching_ports = [p for p in ports if COMPORT_PATTERN.match(p)]
    logging.debug("All available ports: %s", ports)
    logging.debug("Matching ports: %s", matching_ports)
    if not matching_ports:
        raise SerialException("No serial device available")

    serial.port = matching_ports[0]
    serial.open()
    logging.info("Connected to serial device on %s at %d baud",
                 serial.port, SERIAL_BAUD_RATE)


def task():
    """Read RGB value from serial, display it in the frame, and (optionally)
    send it to be printed.
    """
    try:
        if not serial.is_open:
            serial_connect()

        # Discard buffered bytes if they are arriving too quickly
        if serial.in_waiting > SERIAL_BUFFER_LIMIT:
            logging.info("Discarding %d buffered bytes", serial.in_waiting)
            serial.reset_input_buffer()
            # os.execv(sys.executable, ['python'] + sys.argv)

        # Read the upcoming line and check if it's a valid RGB message
        line = serial.readline().decode('utf8')
        logging.debug("%sbuffer: %d", line, serial.in_waiting)
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
            global curr_color
            curr_color = f'#{r:02x}{g:02x}{b:02x}'
            canvas.create_rectangle(0, 0, canvas.draw_x, canvas.draw_y,
                                    width=0, fill=curr_color)
            frame.update()

            # If print flag is present, start printing the color
            if pf is not None:
                assert pf == PRINT_FLAG
                create_outlined_text(canvas.draw_x/2, canvas.draw_y/2,
                                     text=f"Printing...\n{curr_color}")
                frame.update()
                frame.after(0, start_printing, curr_color)
                frame.after(PRINT_DELAY, task)
                return

        frame.after(TASK_DELAY, task)

    except (SerialException, OSError):
        serial.close()
        logging.warning("Serial device disconnected! Retrying in %g s...",
                        RECONNECT_DELAY / 1000)
        frame.after(RECONNECT_DELAY, task)


def create_outlined_text(x, y, *args, **kw):
    """Draw white-on-black outlined text."""
    kw['fill'] = 'black'
    canvas.create_text(x+2, y+2, *args, **kw)
    kw['fill'] = 'white'
    canvas.create_text(x, y, *args, **kw)


# TODO: Add x, y, w, h as parameters
def start_printing(color):
    """Generate and print the image containing the selected color."""
    logging.debug("Generating image for %s...", color)
    img = Image.new(mode='RGB', size=(874, 1240), color='white')  # A5 @ 150 PPI
    img_draw_swatch(img, 600, 56, 256, 168, color)
    img.save(PRINT_FILENAME, 'PNG')

    logging.info("Starting printing for %s...", color)
    for printer in cups.getPrinters().keys():
        title = f'bojata-{color}'
        options = {'media': 'A5'}
        cups.printFile(printer, PRINT_FILENAME, title, options)


def img_draw_swatch(img, x, y, w, h, color):
    d = ImageDraw.Draw(img)
    w_color, w_rgb, h_rgb = swatch_bounds(w, h)
    d.rectangle((x, y, x+w_color, y+h), fill=color)
    for i, sc in enumerate(SWATCH_COLORS):
        d.rectangle((x+w_color, y+i*h_rgb, x+w, y+(i+1)*h_rgb), fill=sc)
    d.text((96, 96), color, font=PRINT_FONT, fill=color)


def swatch_bounds(w, h):
    w_color = w * 15 / 16
    w_rgb = w - w_color
    h_rgb = h / 3
    return w_color, w_rgb, h_rgb


def init(*, serial_init: Serial = None, cups_init: CupsConnection = None,
         frame_init: tk.Tk = None):
    """Initialize connections to serial device and CUPS server, and create a
    canvas in which colors will be displayed.
    """
    global serial
    if (serial := serial_init) is None:
        serial = Serial(baudrate=SERIAL_BAUD_RATE)
    serial_connect()

    global cups
    if (cups := cups_init) is None:
        cups = CupsConnection()

    global frame
    if (frame := frame_init) is None:
        frame = tk.Tk()
        frame.title('bojata')
        frame.geometry('{}x{}'.format(frame.winfo_screenwidth(),
                                      frame.winfo_screenheight()))
        frame.attributes('-fullscreen', True)
        frame.protocol('WM_DELETE_WINDOW', exit)
        frame.update()
        tk.font.nametofont('TkDefaultFont').configure(size=36)

    # Create canvas in which colors will be drawn
    global canvas
    canvas = tk.Canvas(frame, borderwidth=0, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    # Draw RGB swatches on the right edge
    w, h = frame.winfo_width(), frame.winfo_height()
    w_color, w_rgb, h_rgb = swatch_bounds(w, h)
    for i, sc in enumerate(SWATCH_COLORS):
        canvas.create_rectangle(w_color, i*h_rgb, w, (i+1)*h_rgb,
                                width=0, fill=sc)
    canvas.draw_x = w_color
    canvas.draw_y = h

    frame.after(TASK_DELAY, task)  # Schedule first task


def main():
    init()
    frame.mainloop()


if __name__ == '__main__':
    main()
