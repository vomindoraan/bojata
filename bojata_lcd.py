import threading
import time

import numpy as np
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
        pixels = np.asarray(img, dtype=np.uint16)  # shape (h, w, 3), little-endian RGB565
        r, g, b = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b & 0xF8) >> 3)
        with open(fb_filename, 'wb') as fb:
            fb.write(rgb565.astype('H').tobytes())


def init():
    global thread
    thread = threading.Thread(target=render_color_frame)
    thread.start()
    logging.debug("Started LCD rendering thread")

    global initialized
    initialized = True
