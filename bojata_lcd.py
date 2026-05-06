#!/usr/bin/env python3
import struct
import threading
import time

from PIL import Image, ImageDraw

import bojata
from bojata import logging


FB_DEVICE = '/dev/fb1'  # LCD4C framebuffer
LCD_W, LCD_H = 480, 320

# Globals
thread: threading.Thread


def render_color_frame():
    img = Image.new(mode='RGB', size=(LCD_W, LCD_H), color='black')
    draw = ImageDraw.Draw(img)

    while True:
        time.sleep(bojata.LCD_DELAY / 1000)

        color = bojata.curr_color  # Race condition?
        if color is None:
            continue

        logging.debug("[LCD] Rendering %s to LCD...", color)
        bojata.draw_swatch(draw, color, x=0, y=0, w=LCD_W, h=LCD_H)
        # TODO: Draw hex value as text

        # Write raw RGB565 to framebuffer
        raw = img.convert('RGB')
        pixels: list[bytes] = []  # Little-endian RGB565
        for r, g, b in raw.get_flattened_data():
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b & 0xF8) >> 3)
            pixels.append(struct.pack('H', rgb565))

        with open(FB_DEVICE, 'wb') as fb:
            fb.write(b''.join(pixels))


def init():
    global thread
    thread = threading.Thread(target=render_color_frame)
    thread.start()
    logging.debug("[LCD] Started LCD rendering thread")
