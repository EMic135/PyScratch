import ast

code="""
def hi(a):
    print(a)
    #return a
"""
def dump_tree(tree):
    tree = str(ast.dump(tree))
    indent=0
    prev=0
    i=0
    while i < len(tree):
        if i == prev and tree[i]in' ,':
            tree=tree[0:i]+tree[i+1:]
            i-=1
        if i >= prev:
            if tree[i:i+4]=='[], ':
                print(f'{'    ' * indent}{tree[prev:i + 4]}')
                prev = i + 4
            elif tree[i:i+2]=='[]':
                print(f'{'    ' * indent}{tree[prev:i + 2]}')
                prev = i + 2
            elif tree[i] in '([':
                print(f'{'    '*indent}{tree[prev:i+1]}')
                indent += 1
                prev=i+1
            if tree[i] in ',':
                print(f'{'    '*indent}{tree[prev:i+1]}')
                prev=i+1
            if tree[i] in '])':
                print(f'{'    '*indent}{tree[prev:i+1]}')
                indent -= 1
                prev=i+1
        i+=1
print(ast.dump(ast.parse(code)))
dump_tree(ast.parse(code))