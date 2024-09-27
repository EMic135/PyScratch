import tkinter as tk
import io
from contextlib import redirect_stdout

def all_children(wid, finList=None, indent=0):
    finList = finList or []
    children = wid.winfo_children()
    for item in children:
        finList.append(item)
        all_children(item, finList, indent + 1)
    return finList

class TextDisplay(tk.Frame):
    def __init__(self, name, get_text, **kwargs):
        super().__init__(**kwargs)
        self.widgets = []
        self.name = name
        self.get_text = get_text
        self.widgets.append(tk.Label(master=self, text=name))
        self.output = tk.Text(master=self)
        self.widgets.append(self.output)

    def update_widgets(self):
        self.output.delete("1.0", tk.END)
        self.output.insert("1.0", self.get_text())

    def manage_pack(self):
        for widget in self.widgets:
            widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)