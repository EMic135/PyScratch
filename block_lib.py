import tkinter as tk
import os
import ast

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
    def __init__(self, content=[""], indent_change=0, color='#33c4ff'):
        if isinstance(content,str):
            content=[content]
        self.indent_change = indent_change
        self.command = content
        self.content = " ".join(self.command)
        self.color=color
        self.frame=None
        self.widgets = None

    def create_frame(self, master=None):
        self.frame = tk.Frame(bg=self.color, master=master)
        self.widgets = []
        for i in range(len(self.command)):
            if is_var(self.command[i]) and not bool(set(self.command[i]) & set(" ():")):
                self.widgets.append(tk.Entry(master=self.frame or self.frame))
                self.widgets[-1].insert("0", self.command[i])
                self.command[i] = self.widgets[-1].get
            else:
                self.widgets.append(tk.Label(master=self.frame, text=self.command[i], bg=self.color))
                self.command[i] = return_func(self.command[i])
            self.widgets[-1].pack(side=tk.LEFT)

    def pack(self,*args, **kwargs):
        self.frame.pack(*args,**kwargs)

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
    def __init__(self, start=['if __name__ == "__main__":'], color = '#dfdf00'):
        self.frame = False
        if type(start)==type(""):
            start=[start]
        self.start=start
        self.start_content=" ".join(self.start)
        self.blocks=[]
        self.add_block(block=Block(content=self.start, indent_change=1, color=color))
        self.end = Block(indent_change=-1)
        self.color = color

    def create_frame(self, master=None):
        self.frame = tk.Frame(bg=self.color)

    def add_block(self, block, prev_block=None):
        if len(self.blocks) > 0:
            if prev_block is None:
                position = self.blocks.index(self.blocks[-1])+1
            else:
                position = self.blocks.index(prev_block) + 1
        else:
            position = 0
        self.blocks.insert(position, block)
        if not isinstance(self.frame,tk.Frame):
            self.create_frame()
        block.create_frame(self.frame)

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
        for block in self.blocks:
            block.pack(*args, **kwargs)
        self.frame.pack(*args, **kwargs)

class Print(Block):
    def __init__(self, message):
        super().__init__(content=['print(',message,')'])


def create_block(name, obj, args, init):
    return name + '(' + obj + '):\n    def __init__(self, ' + args + '):\n        ' + init

def write_block(name, obj, args, init):
    f = open(os.getcwd() + "/Blocks/" + name + ".block", 'w')
    f.write(create_block(name, obj, args, init))
    f.close()

if __name__ == "__main__":
    window = tk.Tk()
    main=Container()
    true=Container(start="if True:")
    main.add_block(true)
    true.add_block(Block("print('Hello World!')"))
    true.add_block(Block("message = 'Hi Again!'"))
    print_block=Print("message")
    true.add_block(print_block)
    print("---------------------------------")
    print(main.write()[0])
    print("---------------------------------")
    print(main.report_structure()[0])
    print("---------------------------------")
    exec(main.write()[0])
    print("---------------------------------")
    main.pack(anchor='w',padx=(20,0))
    window.mainloop()
