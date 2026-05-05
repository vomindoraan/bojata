#!/usr/bin/env python3
import os
import textwrap
import tkinter as tk
import tkinter.messagebox
from datetime import datetime
from functools import partial

import pandas as pd
from pandastable import Table, TableModel
from PIL import Image, ImageDraw, ImageFont

import bojata
import bojata_db as db


UI_FONT_NAME = 'TkDefaultFont'
PRINT_TEMPLATE = 'print/template_rev0.7.png'

DEFAULT_LOCATION = "Atelje 61, Novi Sad"
DRAWER_COUNT = 10


class BojataRoot(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title('Bojata GUI')
        self.geometry(f'{self.winfo_screenwidth()}x{self.winfo_screenheight()}')
        self.attributes('-fullscreen', True)
        self.protocol('WM_DELETE_WINDOW', exit)
        self.update()  # Update actual width and height

        self.pad = self.winfo_width() // 100
        self.halfpad = (0, self.pad)

        tk.font.nametofont(UI_FONT_NAME).configure(size=18)
        self.font = (UI_FONT_NAME, 18)
        self.font_medium = (UI_FONT_NAME, 24)
        self.font_large = (UI_FONT_NAME, 36)

        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for frame_cls in (HomeFrame, ScanFrame, TableFrame):
            frame = frame_cls(parent=container, root=self)
            frame.grid(row=0, column=0, sticky='nsew')
            self.frames[frame_cls.__name__] = frame

        self.show_frame('HomeFrame')

    def show_frame(self, name):
        self.active_frame = self.frames[name]
        self.active_frame.tkraise()
        self.active_frame.event_generate('<<ShowFrame>>')
        self.update()


class BojataFrame(tk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.root = root
        self.bind('<<ShowFrame>>', self.on_show_frame)

    def on_show_frame(self, event):
        pass


class HomeFrame(BojataFrame):
    def __init__(self, parent, root):
        super().__init__(parent, root)

        self.color_frame = tk.Frame(self)
        self.color_frame.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=self.root.pad, pady=self.root.pad,
        )

        tk.Button(
            self, text="OČITAJ\nBOJU", font=self.root.font_medium,
            command=partial(root.show_frame, 'ScanFrame'),
            padx=self.root.pad*4, pady=self.root.pad*2,
        ).pack(side=tk.TOP, expand=True, padx=self.root.halfpad)

        tk.Button(
            self, text="BAZA\nBOJA", font=self.root.font_medium,
            command=partial(root.show_frame, 'TableFrame'),
            padx=self.root.pad*4, pady=self.root.pad*2,
        ).pack(side=tk.TOP, expand=True, padx=self.root.halfpad)


class ScanFrame(BojataFrame):
    def on_show_frame(self, event):
        self.reinit_ui()
        self.scanned_color = bojata.curr_color
        self.color_swatch.config(bg=self.scanned_color)
        self.iv['hex'].set(self.scanned_color)
        self.update()

    def reinit_ui(self):
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
        frame1.grid(
            row=0, column=0, sticky='nsew', padx=self.root.pad, pady=self.root.pad,
        )
        self.color_swatch = tk.Label(frame1)
        self.color_swatch.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        c = 'hex'
        self.iv[c] = tk.StringVar(self)
        self.il[c] = tk.Label(frame1, textvariable=self.iv[c], font=self.root.font_large)
        self.il[c].pack(side=tk.BOTTOM)

        # Right half
        frame2 = tk.Frame(self)
        frame2.columnconfigure(0, weight=1)
        frame2.columnconfigure(1, weight=1)
        frame2.grid(
            row=0, column=1, sticky='nsew', padx=self.root.halfpad, pady=self.root.pad,
        )

        c = 'author'
        self.il[c] = tk.Label(frame2, text=db.Color.label_of(c))
        self.il[c].grid(row=0, column=0, columnspan=2, sticky='nw')
        self.iv[c] = tk.StringVar(self)
        self.ie[c] = tk.Entry(frame2, textvariable=self.iv[c], font=self.root.font)
        self.ie[c].grid(row=1, column=0, columnspan=2, sticky='we', pady=self.root.halfpad)

        c = 'name'
        self.il[c] = tk.Label(frame2, text=db.Color.label_of(c))
        self.il[c].grid(row=2, column=0, columnspan=2, sticky='nw')
        self.iv[c] = tk.StringVar(self)
        self.ie[c] = tk.Entry(frame2, textvariable=self.iv[c], font=self.root.font)
        self.ie[c].grid(row=3, column=0, columnspan=2, sticky='we', pady=self.root.halfpad)

        c = 'category'
        self.il[c] = tk.Label(frame2, text=db.Color.label_of(c))
        self.il[c].grid(row=4, column=0, columnspan=2, sticky='nw')
        self.iv[c] = tk.StringVar(self)
        categories = [cat.value for cat in db.ColorCategory]
        self.ie[c] = tk.OptionMenu(frame2, self.iv[c], "", *categories)
        self.ie[c].grid(row=5, column=0, columnspan=2, sticky='we', pady=self.root.halfpad)

        c = 'object'
        self.il[c] = tk.Label(frame2, text=db.Color.label_of(c))
        self.il[c].grid(row=6, column=0, columnspan=2, sticky='nw')
        self.iv[c] = tk.StringVar(self)
        # objects = range(1, DRAWER_COUNT+1)
        # self.ie[c] = tk.OptionMenu(frame2, self.iv[c], "", *objects)
        self.ie[c] = tk.Entry(frame2, textvariable=self.iv[c], font=self.root.font)
        self.ie[c].grid(row=7, column=0, columnspan=2, sticky='we', pady=self.root.halfpad)

        c = 'comment'
        self.il[c] = tk.Label(frame2, text=db.Color.label_of(c))
        self.il[c].grid(row=8, column=0, columnspan=2, sticky='nw')
        self.iv[c] = tk.StringVar(self)
        self.ie[c] = tk.Entry(frame2, textvariable=self.iv[c], font=self.root.font)
        self.ie[c].grid(row=9, column=0, columnspan=2, sticky='we', pady=self.root.halfpad)

        c = 'location'
        self.il[c] = tk.Label(frame2, text=db.Color.label_of(c))
        self.il[c].grid(row=10, column=0, columnspan=2, sticky='nw')
        self.iv[c] = tk.StringVar(self, DEFAULT_LOCATION)
        self.ie[c] = tk.Entry(frame2, textvariable=self.iv[c], font=self.root.font)
        self.ie[c].grid(row=11, column=0, columnspan=2, sticky='we', pady=self.root.halfpad)

        c = 'datetime'
        self.il[c] = tk.Label(frame2, text=db.Color.label_of(c))
        self.il[c].grid(row=12, column=0, columnspan=2, sticky='nw')
        self.iv[c] = tk.StringVar(self, datetime.now().strftime(db.DATETIME_FORMAT))
        self.ie[c] = tk.Entry(frame2, textvariable=self.iv[c], font=self.root.font)
        self.ie[c].bind('<Key>', lambda e: 'break')  # Read-only
        self.ie[c].grid(row=13, column=0, columnspan=2, sticky='we', pady=self.root.halfpad)

        tk.Button(
            frame2, text="✔", fg='green', font=self.root.font_medium, command=self.submit,
        ).grid(row=14, column=0, sticky='we', padx=self.root.halfpad, pady=self.root.pad)
        tk.Button(
            frame2, text="❌", fg='red', font=self.root.font_medium, command=self.cancel,
        ).grid(row=14, column=1, sticky='we', pady=self.root.pad)

    def submit(self):
        input_values = {
            c: v.get().strip() or None  # empty string → NULL
            for c, v in self.iv.items()
        }

        required = [col.name for col in db.Color.__table__.columns if not col.nullable]
        missing = [e for c, e in self.ie.items() if c in required and not input_values[c]]
        if missing:
            for e in missing:
                e.config(bg='pink')
            return

        color = db.Color(**input_values)
        db.persist(color)
        self.print_prompt()

        self.root.show_frame('HomeFrame')

    def cancel(self):
        self.root.show_frame('HomeFrame')

    def print_prompt(self):
        # TODO: Replace with a custom dialog window
        if not bojata.PRINT_ENABLED:
            tk.messagebox.showinfo(None, "Boja sačuvana u bazu.")
            return

        if tk.messagebox.askyesno(
            None, "Boja sačuvana u bazu. Da li želite ištampati priznanicu?",
        ):
            # TODO: Enqueue for print task instead
            bojata.start_printing(self.scanned_color, self.generate_image())

    def generate_image(self):
        with Image.open(PRINT_TEMPLATE) as img:
            img.resize((874, 1240))  # A5 @ 150 PPI
            draw = ImageDraw.Draw(img)

            bojata.draw_swatch(draw, self.scanned_color, x=80, y=56, w=256, h=168)
            text = textwrap.fill(self.scanned_color, width=50, max_lines=1)
            draw.text((432, 96), text, font=bojata.PRINT_FONT_LARGE, fill=self.scanned_color)

            value = self.iv['author'].get()
            text = textwrap.fill(value, width=50, max_lines=1)
            draw.text((96, 308), text, font=bojata.PRINT_FONT, fill='black')

            value = self.iv['name'].get()
            text = textwrap.fill(value, width=50, max_lines=1)
            draw.text((96, 436), text, font=bojata.PRINT_FONT, fill='black')

            value = self.iv['category'].get()
            text = textwrap.fill(value, width=50, max_lines=1)
            draw.text((96, 566), text, font=bojata.PRINT_FONT, fill='black')

            value = self.iv['object'].get()
            text = textwrap.fill(value, width=50, max_lines=1)
            draw.text((96, 692), text, font=bojata.PRINT_FONT, fill='black')

            value = self.iv['comment'].get()
            text = textwrap.fill(value, width=50, max_lines=5)
            draw.text((96, 820), text, font=bojata.PRINT_FONT, fill='black')

            value = self.iv['location'].get()
            text = textwrap.fill(value, width=24, max_lines=3)
            draw.text((96, 1076), text, font=bojata.PRINT_FONT, fill='black')

            value = self.iv['datetime'].get()
            text = textwrap.fill(value, width=24, max_lines=3)
            draw.text((472, 1076), text, font=bojata.PRINT_FONT, fill='black')

            return img


class TableFrame(BojataFrame):
    def __init__(self, parent, root):
        super().__init__(parent, root)
        frame = tk.Frame(self)
        frame.pack(
            side=tk.TOP, fill=tk.BOTH, expand=True, padx=self.root.pad, pady=self.root.pad
        )

        df = db.Color.empty_data()
        self.table = Table(
            frame, dataframe=df, maxcellwidth=225,
            rowselectedcolor=None, colselectedcolor=None,  # Disable highlighting
        )
        self.table.show()

        tk.Button(
            self, text="NAZAD", font=self.root.font_medium,
            command=partial(root.show_frame, 'HomeFrame'),
            padx=self.root.pad*2, pady=self.root.pad,
        ).pack(side=tk.TOP, pady=self.root.halfpad)

    def on_show_frame(self, event):
        df = db.Color.read_data()
        self.table.updateModel(TableModel(df))

        # Color cells in hex column based on values
        if not df.empty:
            col = db.Color.label_of(db.Color.hex, annotated=False)
            self.table.setColorByMask(col, pd.Series(), df[col])

        self.table.redraw()


if __name__ == '__main__':
    root = BojataRoot()
    home_frame = root.frames['HomeFrame']

    # Monkey patch serial buffer cleanup to only execute when home frame is active
    orig_cleanup = bojata.serial_buffer_cleanup
    def patched_cleanup():
        if root.active_frame is home_frame:
            orig_cleanup()
    bojata.serial_buffer_cleanup = patched_cleanup

    bojata.init(init_frame=home_frame.color_frame)
    db.init()
    root.mainloop()
