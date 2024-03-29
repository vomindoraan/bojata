#!/usr/bin/env python3
import textwrap
import tkinter as tk
import tkinter.messagebox
from datetime import datetime
from functools import partial

import pandas as pd
from pandastable import Table, TableModel
from PIL import Image, ImageDraw, ImageFont

import bojata
import bojata_db


FONT_NAME = 'TkDefaultFont'
PRINT_FONT_NAME = '/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf'
PRINT_FONT = ImageFont.truetype(PRINT_FONT_NAME, 24)
PRINT_FONT_LARGE = ImageFont.truetype(PRINT_FONT_NAME, 96)
PRINT_ENABLE = False


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

        tk.font.nametofont(FONT_NAME).configure(size=18)
        self.font = (FONT_NAME, 18)
        self.font_medium = (FONT_NAME, 24)
        self.font_large = (FONT_NAME, 36)

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
        self.color_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                              padx=self.root.pad, pady=self.root.pad)

        tk.Button(self, text="OČITAJ\nBOJU", font=self.root.font_medium,
                  padx=self.root.pad*4, pady=self.root.pad*2,
                  command=partial(root.show_frame, 'ScanFrame'))\
            .pack(side=tk.TOP, expand=True, padx=self.root.halfpad)

        tk.Button(self, text="BAZA\nBOJA", font=self.root.font_medium,
                  padx=self.root.pad*4, pady=self.root.pad*2,
                  command=partial(root.show_frame, 'TableFrame'))\
            .pack(side=tk.TOP, expand=True, padx=self.root.halfpad)


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
        frame1.grid(row=0, column=0, sticky='nsew',
                    padx=self.root.pad, pady=self.root.pad)
        self.color_swatch = tk.Label(frame1)
        self.color_swatch.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        f = 'hex'
        self.iv[f] = tk.StringVar(self)
        self.il[f] = tk.Label(frame1, textvariable=self.iv[f], font=self.root.font_large)
        self.il[f].pack(side=tk.BOTTOM)

        # Right half
        frame2 = tk.Frame(self)
        frame2.grid(row=0, column=1, sticky='nsew',
                    padx=self.root.halfpad, pady=self.root.pad)
        frame2.columnconfigure(0, weight=1)
        frame2.columnconfigure(1, weight=1)

        f = 'author'
        self.il[f] = tk.Label(frame2, text="IME AUTORA ⁽*⁾")
        self.il[f].grid(row=0, column=0, columnspan=2, sticky='nw')
        self.iv[f] = tk.StringVar(self)
        self.ie[f] = tk.Entry(frame2, textvariable=self.iv[f], font=self.root.font)
        self.ie[f].grid(row=1, column=0, columnspan=2, sticky='we',
                        pady=self.root.halfpad)

        f = 'name'
        self.il[f] = tk.Label(frame2, text="NAZIV BOJE")
        self.il[f].grid(row=2, column=0, columnspan=2, sticky='nw')
        self.iv[f] = tk.StringVar(self)
        self.ie[f] = tk.Entry(frame2, textvariable=self.iv[f], font=self.root.font)
        self.ie[f].grid(row=3, column=0, columnspan=2, sticky='we',
                        pady=self.root.halfpad)

        f = 'category'
        self.il[f] = tk.Label(frame2, text="KATEGORIJA BOJE")
        self.il[f].grid(row=4, column=0, columnspan=2, sticky='nw')
        self.iv[f] = tk.StringVar(self)
        categories = [c.value for c in bojata_db.ColorCategory]
        self.ie[f] = tk.OptionMenu(frame2, self.iv[f], "", *categories)
        self.ie[f].grid(row=5, column=0, columnspan=2, sticky='we',
                        pady=self.root.halfpad)

        f = 'drawer'
        # self.il[f] = tk.Label(frame2, text="BROJ KASETE")
        self.il[f] = tk.Label(frame2, text="SKENIRANI ARTIKAL")
        self.il[f].grid(row=6, column=0, columnspan=2, sticky='nw')
        self.iv[f] = tk.StringVar(self)
        # drawers = range(1, bojata_db.DRAWER_COUNT+1)
        # self.ie[f] = tk.OptionMenu(frame2, self.iv[f], "", *drawers)
        self.ie[f] = tk.Entry(frame2, textvariable=self.iv[f], font=self.root.font)
        self.ie[f].grid(row=7, column=0, columnspan=2, sticky='we',
                        pady=self.root.halfpad)

        f = 'comment'
        self.il[f] = tk.Label(frame2, text="KOMENTAR")
        self.il[f].grid(row=8, column=0, columnspan=2, sticky='nw')
        self.iv[f] = tk.StringVar(self)
        self.ie[f] = tk.Entry(frame2, textvariable=self.iv[f], font=self.root.font)
        self.ie[f].grid(row=9, column=0, columnspan=2, sticky='we',
                        pady=self.root.halfpad)

        f = 'location'
        self.il[f] = tk.Label(frame2, text="LOKACIJA")
        self.il[f].grid(row=10, column=0, columnspan=2, sticky='nw')
        self.iv[f] = tk.StringVar(self, bojata_db.DEFAULT_LOCATION)
        self.ie[f] = tk.Entry(frame2, textvariable=self.iv[f], font=self.root.font)
        self.ie[f].grid(row=11, column=0, columnspan=2, sticky='we',
                        pady=self.root.halfpad)

        f = 'datetime'
        self.iv[f] = tk.StringVar(self, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        tk.Button(frame2, text="✔", fg='green', font=self.root.font_medium,
                  command=self.submit)\
            .grid(row=12, column=0, sticky='we', ipady=self.root.pad)
        tk.Button(frame2, text="❌", fg='red', font=self.root.font_medium,
                  command=self.cancel)\
            .grid(row=12, column=1, sticky='we', ipady=self.root.pad)

    def submit(self):
        input_values = {
            k: v.get().strip() or None  # empty string → NULL
            for k, v in self.iv.items()
        }

        required_fields = ['author']
        for f in required_fields:
            if not input_values[f]:
                self.ie[f].config(bg='pink')
                return

        color = bojata_db.Color(**input_values)
        bojata_db.persist(color)

        self.print_prompt()
        self.root.show_frame('HomeFrame')

    def cancel(self):
        self.root.show_frame('HomeFrame')

    def print_prompt(self):
        # TODO: Replace with a custom dialog window
        if not PRINT_ENABLE:
            tk.messagebox.showinfo(None, "Boja sačuvana u bazu.")
            return

        if tk.messagebox.askyesno(
            None, "Boja sačuvana u bazu. Da li želite ištampati list potvrde?",
        ):
            bojata.start_printing(self.scanned_color, self.generate_image())

    def generate_image(self):
        with Image.open('template_rev0.6.png') as img:
            img.resize((874, 1240))  # A5 @ 150 PPI
            draw = ImageDraw.Draw(img)

            bojata.draw_swatch(draw, self.scanned_color, x=80, y=56, w=256, h=168)
            text = textwrap.fill(self.scanned_color, width=50, max_lines=1)
            draw.text((432, 96), text, font=PRINT_FONT_LARGE, fill=self.scanned_color)

            value = self.iv['author'].get()
            text = textwrap.fill(value, width=50, max_lines=1)
            draw.text((96, 308), text, font=PRINT_FONT, fill='black')

            value = self.iv['name'].get()
            text = textwrap.fill(value, width=50, max_lines=1)
            draw.text((96, 436), text, font=PRINT_FONT, fill='black')

            value = self.iv['category'].get()
            text = textwrap.fill(value, width=50, max_lines=1)
            draw.text((96, 566), text, font=PRINT_FONT, fill='black')

            value = self.iv['drawer'].get()
            text = textwrap.fill(value, width=50, max_lines=1)
            draw.text((96, 692), text, font=PRINT_FONT, fill='black')

            value = self.iv['comment'].get()
            text = textwrap.fill(value, width=50, max_lines=5)
            draw.text((96, 820), text, font=PRINT_FONT, fill='black')

            value = self.iv['location'].get()
            text = textwrap.fill(value, width=24, max_lines=3)
            draw.text((96, 1076), text, font=PRINT_FONT, fill='black')

            value = self.iv['datetime'].get()
            text = textwrap.fill(value, width=24, max_lines=3)
            draw.text((472, 1076), text, font=PRINT_FONT, fill='black')

            return img


class TableFrame(BojataFrame):
    COLUMN_MAPPING = {
        'hex':      "Boja",
        'author':   "Autor",
        'name':     "Naziv boje",
        'category': "Kategorija boje",
        # 'drawer':   "Broj kasete",
        'drawer':   "Skenirani artikal",
        'comment':  "Komentar",
        'location': "Mesto",
        'datetime': "Vreme",
    }

    def __init__(self, parent, root):
        super().__init__(parent, root)
        frame = tk.Frame(self)
        frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True,
                   padx=self.root.pad, pady=self.root.pad)

        df = pd.DataFrame(columns=self.COLUMN_MAPPING.values())
        self.table = Table(frame, dataframe=df, maxcellwidth=200)
        self.table.drawSelectedRow = lambda: None  # Disable selected row highlighting
        self.table.show()

        tk.Button(self, text="NAZAD", font=self.root.font_medium,
                  padx=self.root.pad*2, pady=self.root.pad,
                  command=partial(root.show_frame, 'HomeFrame'))\
            .pack(side=tk.TOP, pady=self.root.halfpad)

    def on_show_frame(self, event):
        df = bojata_db.Color.read_data(self.COLUMN_MAPPING)
        self.table.updateModel(TableModel(df))

        # Color cells in hex column based on values
        if not df.empty:
            self.table.setRowColors(rows=0, cols=[0], clr='white')
            for row in range(df.shape[0]):
                color = df.at[row, "Boja"]
                self.table.rowcolors["Boja"][row] = color

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

    init_cups = PRINT_ENABLE and None
    bojata.init(init_frame=home_frame.color_frame, init_cups=init_cups)
    bojata_db.init()
    root.mainloop()
