import tkinter as tk
import os
import ast
from copy import deepcopy

from logging import exception

DEBUG = False

def is_var(item):
    # Attempt to parse the string into a Python literal using `ast.literal_eval`
    try:
        ast.literal_eval(item)
        return False  # It's a constant
    except (ValueError, SyntaxError):
        pass
    return True

def return_func(string):
    def func():
        return string
    return func


class Block:
    def __init__(self, content=[""], indent_change=0, color='#33c4ff', master=None):
        if isinstance(content,str):
            content=[content]
        self.original_content = deepcopy(content)
        self.indent_change = indent_change
        self.command = content
        self.content = " ".join(self.command)
        self.color=color
        self.master = master
        self.frame = None
        if master is not None:
            self.frame = tk.Frame(bg=self.color, master=self.master)
            self.widgets = []
            for i in range(len(self.command)):
                if self.command[i]=="":
                    self.widgets.append(tk.Label(master=self.frame, text=self.command[i], bg=self.color))
                    self.command[i] = return_func(self.command[i])
                elif is_var(self.command[i]) and not bool(set(self.command[i]) & set(" ():")):
                    self.widgets.append(tk.Entry(master=self.frame))
                    self.widgets[-1].insert("0", self.command[i])
                    self.command[i] = self.widgets[-1].get
                else:
                    self.widgets.append(tk.Label(master=self.frame, text=self.command[i], bg=self.color))
                    self.command[i] = return_func(self.command[i])
                self.widgets[-1].pack(side=tk.LEFT)
        if DEBUG: print(self.original_content,"|", self.content,"|", self.command,"|", self.frame)

    def redo_self(self, block):
        self.__dict__ = block.__dict__

    def pack(self,*args, **kwargs):
        if DEBUG:tk.Label(text="packing block", master=self.frame).pack()
        if DEBUG: print(self.original_content,"|", self.content,"|", self.command,"|", self.frame)
        self.frame.pack(*args,**kwargs)
        if DEBUG:tk.Label(text="block packed", master=self.frame).pack()

    def get_blocks(self,blocks=None):
        blocks = blocks or []
        blocks.append(self)
        return blocks

    def write(self, code="", indent_level=0):
        if self.content != "":
            code += " " * indent_level
            for command in self.command:
                code += command()
            code += "\n"
        indent_level += self.indent_change
        return code, indent_level

    def report_structure(self, report, indent_level):
        if self.content!="":
            report += " " * indent_level
            report += "type: " + str(type(self))
            report+=" Content: "+self.content
        report += "\n"
        indent_level += self.indent_change
        return report, indent_level

class Container:
    def __init__(self, start=['if __name__ == "__main__":'], color = '#dfdf00', master=None):
        self.original_content=deepcopy(start)
        if type(start) == type(""):
            start = [start]
        self.start = start
        self.start_content = " ".join(self.start)
        self.blocks = []
        self.master=master
        self.color = color
        self.frame = tk.Frame(bg=self.color, master=self.master)
        self.add_block(Block(content=self.start, indent_change=1, color=color))
        self.end = Block(indent_change=-1, color=color)

    def redo_self(self, block):
        self.__dict__ = block.__dict__

    def add_block(self, block, prev_block=None):
        if len(self.blocks) > 0:
            if prev_block is None:
                position = self.blocks.index(self.blocks[-1])+1
            elif isinstance(prev_block,int):
                position = prev_block
            else:
                position = self.blocks.index(prev_block) + 1
        else:
            position = 0

        if isinstance(block,Block):
            new_block=Block(content=block.original_content, color=block.color, indent_change=block.indent_change, master = self.frame)
        elif isinstance(block,Container):
            new_block=Container(start=block.original_content, color=block.color, master=self.frame)
        block.redo_self(new_block)
        self.blocks.insert(position, block)

    def remove_block(self, block):
        del self.blocks[self.blocks.index(block)]

    def get_blocks(self,blocks=None):
        blocks = blocks or []
        for block in self.blocks:
            blocks=block.get_blocks(blocks)
        return blocks

    def write(self, code="", indent_level=0):
        for block in self.blocks:
            code, indent_level = block.write(code, indent_level)
        code, indent_level = self.end.write(code, indent_level)
        return code, indent_level

    def report_structure(self, report="", indent_level=0):
        report += " " * indent_level
        report += "type: " + str(type(self))+" "
        for block in self.blocks:
            report, indent_level = block.report_structure(report, indent_level)
        report, indent_level = self.end.report_structure(report, indent_level)
        return report, indent_level

    def pack(self, *args, **kwargs):
        if DEBUG:tk.Label(text="start packing blocks", master=self.frame).pack()
        self.add_block(self.end)
        for block in self.blocks:
            if DEBUG:tk.Label(text="start block pack",master=self.frame).pack()
            block.pack(*args, **kwargs)
            if DEBUG:tk.Label(text="end block pack", master=self.frame).pack()
        if DEBUG:tk.Label(text="finished packing blocks", master=self.frame).pack()
        self.frame.pack(*args, **kwargs)

def create_block(name, obj, args, init):
    return 'from block_lib import *\nclass '+ name + '(' + obj + '):\n    def __init__(self, ' + args + '):\n        ' + init

def write_block(name, obj, args, init):
    f = open(os.getcwd() + "/Blocks/" + name + ".block", 'w')
    f.write(create_block(name, obj, args, init))
    f.close()

if __name__ == "__main__":
    import io
    from contextlib import redirect_stdout
    #DEBUG = True
    class Print(Block):
        def __init__(self, message):
            super().__init__(content=['print(', message, ')'])

    window = tk.Tk()
    window.title('Hi!')
    window.rowconfigure([0, 1, 2], weight=1, minsize=50)
    window.columnconfigure(0, weight=1, minsize=50)
    frame=tk.Frame()
    preview_frame = tk.Frame()
    output_frame = tk.Frame()

    if DEBUG:print(1)
    main=Container(color='pink',master=frame)
    if DEBUG:print(2)
    main.add_block(Block("message = 'Bye!'"))
    if DEBUG:print(3)
    true=Container(start="if True:", color='green')
    if DEBUG:print(4)
    main.add_block(true)
    if DEBUG:print(5)
    true.add_block(Block(["print(","word",")"]))
    if DEBUG:print(6)
    true.add_block(Block("message = 'Hi Again!'"))
    if DEBUG:print(7)
    print_block=Print("message")
    if DEBUG:print(8)
    main.add_block(print_block)
    if DEBUG:
        print(9)
        print("---------------------------------")
        print(main.write()[0])
        print("---------------------------------")
        print(main.report_structure()[0])
        print("---------------------------------")
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            try:
                exec(main.write()[0])
                out = stdout.getvalue()
            except Exception as e:
                out = e
        print(out)
    if DEBUG:print("---------------------------------")
    main.pack(side=tk.TOP, anchor='w',padx=(25,0), fill='x')
    frame.grid(row=0)

    tk.Label(master=preview_frame, text="Preview").pack(side=tk.TOP, fill=tk.X, expand=True)
    preview = tk.Text(master=preview_frame)
    preview.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    preview_frame.grid(row=1, sticky="news")

    tk.Label(master=output_frame, text="Output").pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    output = tk.Text(master=output_frame)
    output.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    output_frame.grid(row=2, sticky="news")

    def handle_keyrelease(event):
        preview.delete("1.0", tk.END)
        preview.insert("1.0", main.write()[0])

        output.delete("1.0", tk.END)
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            try:
                exec(main.write()[0])
                out = stdout.getvalue()
            except Exception as e:
                out = e
        output.insert("1.0", out)

    window.bind("<KeyRelease>", handle_keyrelease)

    window.mainloop()
