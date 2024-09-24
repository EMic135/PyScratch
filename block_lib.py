class Block:
    def __init__(self, content="", indent_change=0):
        self.indent_change = indent_change
        self.content = content

    def write(self, code="", indent_level=0):
        if self.content != "":
            code += " " * indent_level
            code += self.content
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
    def __init__(self, start='if __name__ == "__main__":'):
        self.blocks=[Block(content=start, indent_change=1)]
        self.end=Block(indent_change=-1)

    def add_block(self, block, prev_block=None):
        if prev_block is None:
            prev_block = self.blocks[-1]
        self.blocks.insert(self.blocks.index(prev_block)+1, block)

    def remove_block(self, block):
        del self.blocks[self.blocks.index(block)]

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

if __name__ == "__main__":
    main=Container()
    main.add_block(Block("print('Hello World!')"))
    print("---------------------------------")
    print(main.write()[0])
    print("---------------------------------")
    print(main.report_structure()[0])
    print("---------------------------------")
    exec(main.write()[0])
    print("---------------------------------")