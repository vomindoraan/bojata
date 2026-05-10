import os
import logging
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
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
stop_event:  threading.Event
initialized: bool = False


def image_chunks(img: Image, size: int, count: int) -> list[np.ndarray]:
    """Chunked view of raw RGB888 image bytes."""
    arr = np.asarray(img)
    return [arr[i*size : (i+1)*size] for i in range(count)]


def encode_chunk(rows: np.ndarray) -> bytes:
    """Convert a slice of rows to little-endian RGB565 bytes."""
    px = rows.astype(np.uint16)
    r, g, b = px[:, :, 0], px[:, :, 1], px[:, :, 2]
    rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | ((b & 0xF8) >> 3)
    return rgb565.astype('H').tobytes()


def encode_image(img: Image, chunk_h: int, n_chunks: int,
                 pool: ThreadPoolExecutor = None) -> list[bytes | Future[bytes]]:
    """Encode image as RGB565 in chunks using an optional thread pool."""
    chunks = image_chunks(img, chunk_h, n_chunks)
    if pool is None:
        return [encode_chunk(c) for c in chunks]
    else:
        return [pool.submit(encode_chunk, c) for c in chunks]


def render_swatch(*, w=LCD_W, h=LCD_H, fb_filename=LCD_FB, n_chunks=8, delay=bojata.LCD_DELAY,
                  get_color=partial(getattr, bojata, 'curr_color')):
    delay /= 1000  # ms → s
    chunk_h = h // n_chunks  # Rows per chunk
    img = Image.new(mode='RGB', size=(w, h), color='black')
    draw = ImageDraw.Draw(img)

    # Draw frame in chunks using thread pool workers
    with ThreadPoolExecutor(max_workers=n_chunks) as pool:
        # Pre-encode the first frame so the pipeline has something to start with
        futures = encode_image(img, chunk_h, n_chunks, pool)

        global stop_event
        while not stop_event.is_set():
            time.sleep(delay)

            if (color := get_color()) is None:  # Use event instead?
                continue

            logger.debug("Rendering %s to LCD...", color)
            bojata.draw_swatch(draw, color, x=0, y=0, w=w, h=h)  # TODO: Draw hex text?

            # Submit encoding of next frame while writing current frame
            next_futures = encode_image(img, chunk_h, n_chunks, pool)
            with open(fb_filename, 'wb') as fb:
                for f in futures:
                    fb.write(f.result())  # Blocks per-chunk, not all at once
            futures = next_futures


# For testing
def generate_color(*, delay=330, set_color=partial(setattr, bojata, 'curr_color')):
    import random
    delay /= 1000

    global stop_event
    while not stop_event.is_set():
        rand = random.randint(0, (1 << 24) - 1)
        set_color(f'#{rand:06x}')
        logger.debug("Generated %s", bojata.curr_color)
        time.sleep(delay)


def init():
    global stop_event
    stop_event = threading.Event()

    global thread
    thread = threading.Thread(target=render_swatch)
    thread.start()
    logger.info("Started LCD rendering thread")

    global initialized
    initialized = True


def stop():
    global stop_event, initialized
    stop_event.set()
    initialized = False
