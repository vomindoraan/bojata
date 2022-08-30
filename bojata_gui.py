#!/usr/bin/env python3
import tkinter as tk
from datetime import datetime
from functools import partial

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
        frame = self.frames[name]
        frame.tkraise()
        frame.event_generate('<<ShowFrame>>')


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

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1)
        self.inputs = {}

        # Left half
        frame1 = tk.Frame(self)
        frame1.grid(row=0, column=0, sticky='nsew',
                    padx=self.root.pad, pady=self.root.pad)
        self.color_swatch = tk.Label(frame1)
        self.color_swatch.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.inputs['hex'] = tk.StringVar(self)
        tk.Label(frame1, textvariable=self.inputs['hex'], font=(FONT_NAME, 36))\
            .pack(side=tk.BOTTOM)

        # Right half
        frame2 = tk.Frame(self)
        frame2.grid(row=0, column=1, sticky='nsew',
                    padx=self.root.pad, pady=self.root.pad)
        frame2.columnconfigure(0, weight=1)
        frame2.columnconfigure(1, weight=1)
        pady = (0, self.root.pad)
        font = (FONT_NAME, 18)

        tk.Label(frame2, text="IME AUTORA ⁽*⁾")\
            .grid(row=0, column=0, columnspan=2, sticky='nw')
        self.inputs['author'] = tk.StringVar(self)
        tk.Entry(frame2, textvariable=self.inputs['author'], font=font)\
            .grid(row=1, column=0, columnspan=2, sticky='we', pady=pady)

        tk.Label(frame2, text="NAZIV BOJE")\
            .grid(row=2, column=0, columnspan=2, sticky='nw')
        self.inputs['name'] = tk.StringVar(self)
        tk.Entry(frame2, textvariable=self.inputs['name'], font=font)\
            .grid(row=3, column=0, columnspan=2, sticky='we', pady=pady)

        tk.Label(frame2, text="KATEGORIJA BOJE")\
            .grid(row=4, column=0, columnspan=2, sticky='nw')
        self.inputs['category'] = tk.StringVar(self)
        categories = [c.value for c in bojata_db.ColorCategory]
        tk.OptionMenu(frame2, self.inputs['category'], "", *categories)\
            .grid(row=5, column=0, columnspan=2, sticky='we', pady=pady)

        tk.Label(frame2, text="BROJ KASETE")\
            .grid(row=6, column=0, columnspan=2, sticky='nw')
        self.inputs['drawer'] = tk.StringVar(self)
        drawers = range(1, DRAWER_COUNT+1)
        tk.OptionMenu(frame2, self.inputs['drawer'], "", *drawers)\
            .grid(row=7, column=0, columnspan=2, sticky='we', pady=pady)

        tk.Label(frame2, text="LOKACIJA")\
            .grid(row=8, column=0, columnspan=2, sticky='nw')
        self.inputs['location'] = tk.StringVar(self, DEFAULT_LOCATION)
        tk.Entry(frame2, textvariable=self.inputs['location'], font=font)\
            .grid(row=9, column=0, columnspan=2, sticky='we', pady=pady)

        tk.Label(frame2, text="KOMENTAR")\
            .grid(row=10, column=0, columnspan=2, sticky='nw')
        self.inputs['comment'] = tk.StringVar(self)
        tk.Entry(frame2, textvariable=self.inputs['comment'], font=font)\
            .grid(row=11, column=0, columnspan=2, sticky='we', pady=pady)

        tk.Button(frame2, text="✔", fg='green', font=font, command=self.submit)\
            .grid(row=12, column=0, sticky='we', ipady=self.root.pad)
        tk.Button(frame2, text="❌", fg='red', font=font, command=self.cancel)\
            .grid(row=12, column=1, sticky='we', ipady=self.root.pad)

        self.bind('<<ShowFrame>>', self.on_show_frame)

    def submit(self):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.inputs['datetime'] = tk.StringVar(self, now)
        input_values = {k: v.get() for k, v in self.inputs.items()}

        color = bojata_db.Color(**input_values)

    def cancel(self):
        root.show_frame('HomeFrame')

    def on_show_frame(self, event):
        self.scanned_color = bojata.curr_color
        self.color_swatch.config(bg=self.scanned_color)
        self.inputs['hex'].set(self.scanned_color)
        # self.update()


class ListFrame(BojataFrame):
    def __init__(self, parent, root):
        super().__init__(parent, root)


if __name__ == '__main__':
    root = BojataRoot()
    color_frame = root.frames['HomeFrame'].color_frame
    bojata.init(frame_init=color_frame, cups_init=0)  # TODO: Set up CUPS
    root.mainloop()
