import struct
import threading
import time

from PIL import Image, ImageDraw

import bojata
from bojata import logging


LCD_W, LCD_H = 480, 320
LCD_FB = '/dev/fb1'

# Globals
thread:      threading.Thread
initialized: bool = False


def render_color_frame(w=LCD_W, h=LCD_H, fb_filename=LCD_FB, delay=bojata.LCD_DELAY):
    img = Image.new(mode='RGB', size=(w, h), color='black')
    draw = ImageDraw.Draw(img)

    while True:
        time.sleep(delay / 1000)

        color = bojata.curr_color  # TODO: Lock?
        if color is None:
            continue

        logging.debug("Rendering %s to LCD...", color)
        bojata.draw_swatch(draw, color, x=0, y=0, w=w, h=h)
        # TODO: Draw hex value as text

        # Write raw RGB565 to framebuffer
        raw = img.convert('RGB')
        pixels: list[bytes] = []  # Little-endian RGB565
        for r, g, b in raw.get_flattened_data():
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b & 0xF8) >> 3)
            pixels.append(struct.pack('H', rgb565))

        with open(fb_filename, 'wb') as fb:
            fb.write(b''.join(pixels))


def init():
    global thread
    thread = threading.Thread(target=render_color_frame)
    thread.start()
    logging.debug("Started LCD rendering thread")

    global initialized
    initialized = True
