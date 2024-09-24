class Block:
    def __init__(self, content="", indent_change=0):
        self.indent_change = indent_change
        self.content = content

    def write(self, code, indent_level):
        if self.content != "":
            code += " " * indent_level
            code += self.content
            code += "\n"
        indent_level += self.indent_change
        return code, indent_level

class Container:
    def __init__(self, start='if __name__ == "__main__":'):
        self.blocks=[Block(content=start, indent_change=1)]
        self.end=Block(indent_change=-1)

    def add_block(self, block, prev_block=None):
        if prev_block is None:
            prev_block = self.blocks[-1]
        self.blocks.insert(self.blocks.index(prev_block)+1, block)

    def remove_block(self, block):
        del self.blocks[self.blocks.index(block)]

    def write(self, code, indent_level):
        for block in self.blocks:
            code, indent_level = block.write(code, indent_level)
        code, indent_level = self.end.write(code, indent_level)
        return code, indent_level

class Main(Container):
    def __init__(self):
        self.blocks = [Block()]
        self.end = Block()
    def write(self):
        code=""
        indent_level=0
        for block in self.blocks:
            code, indent_level = block.write(code, indent_level)
        code, indent_level = self.end.write(code, indent_level)
        return code, indent_level


class Function(Container):
    def __init__(self, name, args):
        start = "def "+name+"("
        for arg in args:
            start+=arg+", "
        start=start[0:-2]
        start+="):"
        super().__init__(start=start)

class While(Container):
    def __init__(self, condition):
        super().__init__(start="while "+condition+":")

class For(Container):
    def __init__(self, var, num_runs):
        super().__init__(start="for "+var+" in range("+num_runs+"):")


class Print(Block):
    def __init__(self, text):
        super().__init__(content="print("+text+")")

class PythonCustom(Block):
    def __init__(self, command):
        super().__init__(content=command)


main=Main()
hello_world = Function("repeat",["message"])
hello_world.add_block(Print("message"))
main.add_block(hello_world)
test = Container()
noisy = For("i","10")
noisy.add_block(PythonCustom("repeat(str(i)+' Hello World')"))
test.add_block(noisy)
main.add_block(test)
print("---------------------------------")
print(main.write()[0])
print("---------------------------------")
exec(main.write()[0])
print("---------------------------------")