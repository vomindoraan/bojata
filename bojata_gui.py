#!/usr/bin/env python3
import logging
import os
import sys
import tkinter as tk
import tkinter.messagebox
from datetime import datetime
from functools import partial

from PIL import Image, ImageDraw

import bojata
import bojata_db


FONT_NAME = 'TkDefaultFont'
DRAWER_COUNT = 10
DEFAULT_LOCATION = "Kreativni distrikt, Novi Sad"


class BojataRoot(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title('bojata')
        self.geometry('{}x{}'.format(self.winfo_screenwidth(),
                                     self.winfo_screenheight()))
        self.attributes('-fullscreen', True)
        self.protocol('WM_DELETE_WINDOW', exit)
        self.update()  # Update actual width and height
        self.pad = self.winfo_width() // 100

        tk.font.nametofont(FONT_NAME).configure(size=18)

        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for frame_cls in (HomeFrame, ScanFrame, ListFrame):
            frame = frame_cls(parent=container, root=self)
            frame.grid(row=0, column=0, sticky='nsew')
            frame.update()
            self.frames[frame_cls.__name__] = frame

        self.show_frame('HomeFrame')

    def show_frame(self, name):
        self.curr_frame = self.frames[name]
        self.curr_frame.tkraise()
        self.curr_frame.event_generate('<<ShowFrame>>')

    def rerun_app(self):
        if self.curr_frame is self.frames['HomeFrame']:
            logging.info("Rerunning app...")
            os.execv(sys.executable, ['python'] + sys.argv)


class BojataFrame(tk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.root = root


class HomeFrame(BojataFrame):
    def __init__(self, parent, root):
        super().__init__(parent, root)

        self.color_frame = tk.Frame(self)
        self.color_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                              padx=self.root.pad, pady=self.root.pad)
        font = (FONT_NAME, 24)

        scan_button = tk.Button(self, text="OČITAJ\nBOJU", font=font,
                                padx=self.root.pad*4, pady=self.root.pad*2,
                                command=partial(root.show_frame, 'ScanFrame'))
        scan_button.pack(side=tk.TOP, expand=True)

        list_button = tk.Button(self, text="BAZA\nBOJA", font=font,
                                padx=self.root.pad*4, pady=self.root.pad*2,
                                command=partial(root.show_frame, 'ListFrame'))
        list_button.pack(side=tk.TOP, expand=True)


class ScanFrame(BojataFrame):
    def __init__(self, parent, root):
        super().__init__(parent, root)
        self.bind('<<ShowFrame>>', self.on_show_frame)

    def on_show_frame(self, event):
        self.reset_ui()
        self.scanned_color = bojata.curr_color
        self.color_swatch.config(bg=self.scanned_color)
        self.iv['hex'].set(self.scanned_color)
        self.update()

    def reset_ui(self):
        for child in self.winfo_children():
            child.destroy()

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        self.il: dict[str, tk.Label] = {}      # Input labels
        self.iv: dict[str, tk.StringVar] = {}  # Input variables
        self.ie: dict[str, tk.Widget] = {}     # Input entry widgets

        # Left half
        frame1 = tk.Frame(self)
        frame1.grid(row=0, column=0, sticky='nsew',
                    padx=self.root.pad, pady=self.root.pad)
        self.color_swatch = tk.Label(frame1)
        self.color_swatch.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        f = 'hex'
        self.iv[f] = tk.StringVar(self)
        self.il[f] = tk.Label(frame1, textvariable=self.iv[f], font=(FONT_NAME, 36))
        self.il[f].pack(side=tk.BOTTOM)

        # Right half
        frame2 = tk.Frame(self)
        frame2.grid(row=0, column=1, sticky='nsew',
                    padx=self.root.pad, pady=self.root.pad)
        frame2.columnconfigure(0, weight=1)
        frame2.columnconfigure(1, weight=1)
        pady = (0, self.root.pad)
        font = (FONT_NAME, 18)

        f = 'author'
        self.il[f] = tk.Label(frame2, text="IME AUTORA ⁽*⁾")
        self.il[f].grid(row=0, column=0, columnspan=2, sticky='nw')
        self.iv[f] = tk.StringVar(self)
        self.ie[f] = tk.Entry(frame2, textvariable=self.iv[f], font=font)
        self.ie[f].grid(row=1, column=0, columnspan=2, sticky='we', pady=pady)

        f = 'name'
        self.il[f] = tk.Label(frame2, text="NAZIV BOJE")
        self.il[f].grid(row=2, column=0, columnspan=2, sticky='nw')
        self.iv[f] = tk.StringVar(self)
        self.ie[f] = tk.Entry(frame2, textvariable=self.iv[f], font=font)
        self.ie[f].grid(row=3, column=0, columnspan=2, sticky='we', pady=pady)

        f = 'category'
        self.il[f] = tk.Label(frame2, text="KATEGORIJA BOJE")
        self.il[f].grid(row=4, column=0, columnspan=2, sticky='nw')
        self.iv[f] = tk.StringVar(self)
        categories = [c.value for c in bojata_db.ColorCategory]
        self.ie[f] = tk.OptionMenu(frame2, self.iv[f], "", *categories)
        self.ie[f].grid(row=5, column=0, columnspan=2, sticky='we', pady=pady)

        f = 'drawer'
        self.il[f] = tk.Label(frame2, text="BROJ KASETE")
        self.il[f].grid(row=6, column=0, columnspan=2, sticky='nw')
        self.iv[f] = tk.StringVar(self)
        drawers = range(1, DRAWER_COUNT+1)
        self.ie[f] = tk.OptionMenu(frame2, self.iv[f], "", *drawers)
        self.ie[f].grid(row=7, column=0, columnspan=2, sticky='we', pady=pady)

        f = 'location'
        self.il[f] = tk.Label(frame2, text="LOKACIJA")
        self.il[f].grid(row=8, column=0, columnspan=2, sticky='nw')
        self.iv[f] = tk.StringVar(self, DEFAULT_LOCATION)
        self.ie[f] = tk.Entry(frame2, textvariable=self.iv[f], font=font)
        self.ie[f].grid(row=9, column=0, columnspan=2, sticky='we', pady=pady)

        f = 'comment'
        self.il[f] = tk.Label(frame2, text="KOMENTAR")
        self.il[f].grid(row=10, column=0, columnspan=2, sticky='nw')
        self.iv[f] = tk.StringVar(self)
        self.ie[f] = tk.Entry(frame2, textvariable=self.iv[f], font=font)
        self.ie[f].grid(row=11, column=0, columnspan=2, sticky='we', pady=pady)

        tk.Button(frame2, text="✔", fg='green', font=font, command=self.submit)\
            .grid(row=12, column=0, sticky='we', ipady=self.root.pad)
        tk.Button(frame2, text="❌", fg='red', font=font, command=self.cancel)\
            .grid(row=12, column=1, sticky='we', ipady=self.root.pad)

    def submit(self):
        input_values = {
            k: v.get().strip() or None  # empty string → NULL
            for k, v in self.iv.items()
        }
        input_values['datetime'] = datetime.now()

        required_fields = ['author']
        for f in required_fields:
            if not input_values[f]:
                self.ie[f].config(bg='pink')
                return

        color = bojata_db.Color(**input_values)
        bojata_db.persist(color)

        self.print_prompt()
        root.show_frame('HomeFrame')

    def cancel(self):
        root.show_frame('HomeFrame')

    def print_prompt(self):
        # TODO: Replace with a custom dialog window
        answer = tk.messagebox.askyesno(
            "Štampa",
            "Boja sačuvana u bazu. Da li želite ištampati list potvrde?",
        )
        if answer:
            img = self.generate_image(self.scanned_color)
            bojata.start_printing(self.scanned_color, img)

    def generate_image(self, color):
        with Image.open('template_rev0.6.png') as img:
            img.resize((874, 1240))  # A5 @ 150 PPI
            draw = ImageDraw.Draw(img)
            bojata.draw_swatch(draw, 80, 56, 256, 168, color)
            draw.text((432, 96), text=color, font=bojata.PRINT_FONT, fill=color)
            return img


class ListFrame(BojataFrame):
    def __init__(self, parent, root):
        super().__init__(parent, root)
        # TODO


if __name__ == '__main__':
    root = BojataRoot()
    color_frame = root.frames['HomeFrame'].color_frame
    bojata.init(frame_init=color_frame)
    bojata.serial_buffer_cleanup = root.rerun_app  # Monkey patch cleanup handler
    bojata_db.init()
    root.mainloop()
