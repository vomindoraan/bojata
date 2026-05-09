import os
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import numpy as np
from PIL import Image, ImageDraw

import bojata


logger = logging.getLogger(__name__)

LCD_W = int(os.getenv('LCD_W', 480))
LCD_H = int(os.getenv('LCD_H', 320))
LCD_FB = os.getenv('LCD_FB', '/dev/fb1')

# Globals
thread:      threading.Thread
initialized: bool = False


def render_swatch(*, w=LCD_W, h=LCD_H, fb_filename=LCD_FB, n_chunks=8, delay=bojata.LCD_DELAY,
                  stop_if=lambda: False, get_color=partial(getattr, bojata, 'curr_color')):

    def image_chunks(img: Image, size: int, count: int) -> list[np.ndarray]:
        """Chunked view of raw RGB888 image bytes"""
        arr = np.asarray(img)
        return [arr[i*size : (i+1)*size] for i in range(count)]

    def encode_chunk(rows: np.ndarray) -> bytes:
        """Convert a slice of rows to RGB565 bytes"""
        px = rows.astype(np.uint16)
        r, g, b = px[:, :, 0], px[:, :, 1], px[:, :, 2]
        rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b & 0xF8) >> 3)
        return rgb565.astype('H').tobytes()

    delay /= 1000  # ms → s
    chunk_h = h // n_chunks  # Rows per chunk
    img = Image.new(mode='RGB', size=(w, h), color='black')
    draw = ImageDraw.Draw(img)
    chunks = image_chunks(img, chunk_h, n_chunks)  # Initial frame (all black)

    # Draw frame in chunks using thread pool workers
    with ThreadPoolExecutor(max_workers=n_chunks) as pool:
        # Pre-encode the first frame so the pipeline has something to start with
        futures = [pool.submit(encode_chunk, chunk) for chunk in chunks]

        while not stop_if():
            time.sleep(delay)

            if (color := get_color()) is None:
                continue

            logger.debug("Rendering %s to LCD...", color)
            bojata.draw_swatch(draw, color, x=0, y=0, w=w, h=h)
            # TODO: Draw hex value as text

            # Submit encoding of next frame while writing current frame
            chunks = image_chunks(img, chunk_h, n_chunks)
            next_futures = [pool.submit(encode_chunk, chunk) for chunk in chunks]
            with open(fb_filename, 'wb') as fb:
                for future in futures:
                    fb.write(future.result())  # Blocks per-chunk, not all at once
            futures = next_futures


# For testing
def generate_color(*, delay=bojata.TASK_DELAY, stop_if=lambda: False,
                   set_color=partial(setattr, bojata, 'curr_color')):
    import random

    delay /= 1000
    while not stop_if():
        rand = random.randint(0, (1 << 24) - 1)
        set_color(f'#{rand:06x}')
        logger.debug("Generated %s", bojata.curr_color)
        time.sleep(delay)


def init():
    global thread
    thread = threading.Thread(target=render_swatch)
    thread.start()
    logger.info("Started LCD rendering thread")

    global initialized
    initialized = True
