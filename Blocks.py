from block_lib import Container, Block

class Main(Container):
    def __init__(self):
        self.blocks = [Block()]
        self.end = Block()


class Function(Container):
    def __init__(self, name, args):
        start = "def "+name+"("
        if type(args)!=type([]):
            args=[args]
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

if __name__=="__main__":
    main = Main()
    hello_world = Function("repeat", "message")
    hello_world.add_block(Print("message"))
    main.add_block(hello_world)
    test = Container()
    noisy = For("i", "10")
    noisy.add_block(PythonCustom("repeat(str(i)+' Hello World')"))
    test.add_block(noisy)
    main.add_block(test)
    print("---------------------------------")
    print(main.write()[0])
    print("---------------------------------")
    print(main.report_structure()[0])
    print("---------------------------------")
    exec(main.write()[0])
    print("---------------------------------")