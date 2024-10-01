import sys, io
def safe_exec(string, in_io=io.StringIO(), out_io=io.StringIO()):
    stdin, stdout = sys.stdin, sys.stdout
    sys.stdin, sys.stdout = in_io, out_io
    try:
        exec(string)
    except SystemExit:
        pass
    sys.stdin, sys.stdout = stdin, stdout
    print(out_io.getvalue())
safe_exec("print('hi')")