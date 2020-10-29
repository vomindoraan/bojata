import re
import tkinter as tk
import serial
import logging

logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)

for p in range(5, 12):
    try:
        ser = serial.Serial(f'COM{p}', 9600)
        logging.info("Connected to serial device on %s", ser.port)
        break
    except serial.SerialException:
        continue
else:
    raise FileNotFoundError("No serial device found")

PATTERN = re.compile(r'(\d+),(\d+),(\d+)(?:,(\d+))?\r?\n')
DELAY = 0

root = tk.Tk()
root.title("bojata")
root.update()

def task():
    try:
        line = ser.readline().decode('utf8')
        logging.debug(line)

        if m := PATTERN.match(line):
            r, g, b, i = m.groups()
            r, g, b = map(int, (r, g, b))

            if i is not None:
                total = int(i) or 1
                r = int(r / total * 255)
                g = int(g / total * 255)
                b = int(b / total * 255)

            bg = f'#{r:02x}{g:02x}{b:02x}'
            root.configure(bg=bg)
            root.update()
    except Exception as e:
        logging.exception(e)
    finally:
        root.after(DELAY, task)

root.after(DELAY, task)
root.mainloop()
