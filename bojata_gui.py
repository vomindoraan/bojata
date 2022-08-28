#!/usr/bin/env python3
import tkinter as tk
from functools import partial

import bojata


class BojataGUI(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title('bojata')
        self.geometry('{}x{}'.format(self.winfo_screenwidth(),
                                     self.winfo_screenheight()))
        self.attributes('-fullscreen', True)
        self.protocol('WM_DELETE_WINDOW', exit)

        self.update()  # Update actual width and height
        self.padding = self.winfo_width() // 100

        tk.font.nametofont('TkDefaultFont').configure(size=36)

        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for frame_cls in (HomeFrame, ScanFrame, ListFrame):
            name = frame_cls.__name__
            frame = frame_cls(parent=container, root=self)
            frame.grid(row=0, column=0, sticky='nsew')
            frame.update()
            self.frames[name] = frame

        self.show_frame('HomeFrame')

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()
        frame.event_generate('<<ShowFrame>>')


class HomeFrame(tk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.root = root

        self.color_frame = tk.Frame(self)
        self.color_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                              padx=self.root.padding, pady=self.root.padding)

        scan_button = tk.Button(self, text="SCAN", # fg="red",
                                padx=self.root.padding*2, pady=self.root.padding*2,
                                command=partial(root.show_frame, 'ScanFrame'))
        scan_button.pack(side=tk.TOP, expand=True)

        list_button = tk.Button(self, text="LIST", # fg="green",
                                padx=self.root.padding*2, pady=self.root.padding*2,
                                command=partial(root.show_frame, 'ListFrame'))
        list_button.pack(side=tk.TOP, expand=True)


class ScanFrame(tk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.root = root

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        # Left half
        frame1 = tk.Frame(self)
        frame1.grid(row=0, column=0, sticky='nsew',
                    padx=self.root.padding, pady=self.root.padding)
        self.color_label = tk.Label(frame1)
        self.color_label.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.hex_label = tk.Label(frame1)
        self.hex_label.pack(side=tk.BOTTOM)

        # Right half
        frame2 = tk.Frame(self)
        frame2.grid(row=0, column=1, sticky='nsew',
                    padx=self.root.padding, pady=self.root.padding)
        # TODO

        self.bind('<<ShowFrame>>', self.on_show_frame)

    def on_show_frame(self, event):
        self.scanned_color = bojata.color
        self.color_label.config(bg=self.scanned_color)
        self.hex_label.config(text=self.scanned_color)
        # self.update()


class ListFrame(tk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.root = root


if __name__ == '__main__':
    root = BojataGUI()
    color_frame = root.frames['HomeFrame'].color_frame
    bojata.init(window_init=color_frame, cups_init=0)
    root.mainloop()
