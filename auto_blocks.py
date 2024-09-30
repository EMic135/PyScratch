import ast
import keyword
import inspect
import builtins
import io
from contextlib import redirect_stdout
from copy import deepcopy
from shutil import get_terminal_size
import importlib

DEBUG = True
TIMEOUT_DURATION = 3  # Timeout in seconds
EXCLUDE_WORDS = ["open", "aiter", "anext", "breakpoint", "global", "globals",
                 "locals", "dict", "input", "print", "complex", "local",
                 "memoryview", "map", 'object', 'property', 'zip', 'import',
                 'copyright', 'credits', 'exit', 'help', 'license',
                 'nonlocal', 'quit', '__loader__','Ellipsis', 'execfile']

OBJ = """
class Potato:
    def __init__(self):
        self.string_example = "string_example"
    def get(self):
        return self.string_example
    def __call__(self):
        print("Potato!")
potato = Potato()
"""

TEST = """
class LimitedTrue:
    def __init__(self):
        self.remaining = 5
    def get(self):
        if self.remaining > 0:
            self.remaining -= 1
            return True
        else:
            return False
"""

def categorize_args(signature):
    pos_only = []
    pos_or_kw = []
    var_positional = None
    keyword_only = []
    var_keyword = None

    # Pre-process signature: Remove brackets used to denote optional args in docstrings.
    signature = signature.replace("[", "").replace("]", "")

    # Split by commas and remove leading/trailing whitespace
    parts = [arg.strip() for arg in signature.split(",")]

    pos_only_section = True
    kw_only_section = False

    for part in parts:
        if part == '/':
            # Positional-only arguments end here
            pos_only_section = False
        elif part == '*':
            # All subsequent arguments are keyword-only
            kw_only_section = True
        elif part.startswith("**"):
            var_keyword = part
        elif part.startswith("*"):
            var_positional = part
            kw_only_section = True
        else:
            if kw_only_section:
                keyword_only.append(part)
            elif pos_only_section:
                pos_only.append(part)
            else:
                pos_or_kw.append(part)
    return {
        "Positional-only": pos_only,
        "Positional-or-keyword": pos_or_kw,
        "Var-positional": var_positional,
        "Keyword-only": keyword_only,
        "Var-keyword": var_keyword,
    }

def categorize_func(func):
    # Use the inspect module to get the function's signature
    sig = inspect.signature(func)

    # Prepare the categories
    categories = {
        'Positional-only': [],
        'Positional-or-keyword': {},
        'Var-positional': None,
        'Keyword-only': {},
        'Var-keyword': None
    }

    # Iterate through the parameters in the signature
    for param_name, param in sig.parameters.items():
        if param.kind == inspect.Parameter.POSITIONAL_ONLY or (param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and param.default is inspect.Parameter.empty):
            categories['Positional-only'].append(param_name)
        elif param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            categories['Positional-or-keyword'][param_name]=param.default
        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            categories['Var-positional'] = f"*{param_name}"
        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
            categories['Keyword-only'][param_name]=param.default
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            categories['Var-keyword'] = f"**{param_name}"

    return categories

def find_ast_node(keyword_name):
    known_dict={
        'def':'functiondef',
        'class': 'classdef'
    }
    if keyword_name in known_dict.keys():
        keyword_name = known_dict[keyword_name]
    for node_name, node_type in ast.__dict__.items():
        if isinstance(node_type, type) and issubclass(node_type, ast.AST):
            if node_name.lower() == keyword_name:
                return node_type
    return None

def get_ast_requirements(node_class):
    if node_class:
        return [field for field in node_class._fields]
    return []

def generate_args_from_help(function_name):
    help_output = io.StringIO()
    with redirect_stdout(help_output):
        help(function_name)
    help_output = help_output.getvalue().replace("..."," ")
    args_list = []
    while f"{function_name}(" in help_output:
        start = help_output.index(f"{function_name}(")
        args_list.append(categorize_args(help_output[start + len(function_name) + 1:help_output.index(')', start)]))
        help_output = help_output[help_output.index(')', start) + 1:]
    return args_list or None

def analyze_input(identifier):
    if keyword.iskeyword(identifier):
        node_class = find_ast_node(identifier)
        if node_class:
            required_fields = get_ast_requirements(node_class)
            return [True, "k", required_fields]
        else:
            return [True, "k", []]
    try:
        obj = getattr(builtins, identifier)
        if callable(obj):
            try:
                return [True, "f", find_arg(identifier, [categorize_func(obj)])]
            except (ValueError, TypeError):
                try:
                    return [True, "f", find_arg(identifier, generate_args_from_help(identifier))]
                except:
                    return False
    except AttributeError:
        pass
    try:
        exec(identifier)
        return [True, "k", []]
    except:
        pass
    return False

def find_arg(function_name, args_dicts, code=""):
    common_types = [
        '10',  # Integer
        '10.5',  # Float
        '"string_example"',  # String
        '[1, 2, 3]',  # List
        '(1, 2)',  # Tuple
        '{1, 2, 3}',  # Set
        'iter([1, 2, 3])',  # Iterable
        "{'key': 'value'}",  # Dictionary
        'None',  # NoneType
        'True',  # Boolean True
        'False',  # Boolean False
        'lambda x: x * 2',  # Function as argument
        'str',   # Class
        'potato'   # class defined above
    ]
    for args_dict in args_dicts:
        args_dict['Positional-only'] = {arg:[] for arg in args_dict['Positional-only']}
        current_indexes = {arg:0 for arg in args_dict['Positional-only']}
        run=True
        while run:
            current_values = {key:common_types[current_indexes[key]] for i, key in enumerate(current_indexes)}
            test_code=deepcopy(code)
            arg_string = ", ".join([current_values[key] for i, key in enumerate(current_indexes)])
            if 'potato' in arg_string:
                test_code+=OBJ
            try:
                test_code += f"{function_name}({arg_string})"
                test_out = io.StringIO()
                with redirect_stdout(test_out):
                    exec(test_code)
                test_out.getvalue()
                for key in args_dict['Positional-only'].keys():
                    args_dict['Positional-only'][key].append(current_values[key])
            except:
                pass
            add=False
            for key in current_indexes:
                if key == list(current_indexes.keys())[0]:
                    current_indexes[key]+=1
                if add:
                    current_indexes[key] += 1
                    add = False
                if current_indexes[key] >= len(common_types):
                    if list(current_indexes.keys()).index(key) == len(current_indexes)-1:
                        run=False
                        break
                    current_indexes[key] = 0
                    add=True
    return args_dicts

def generate_keyword_code(word, analysis, code='', variables=None):
    """
    Generate the code for Python keywords using the analyzed fields.
    """
    if word == 'lambda': return 'lambda ARGS0: BODY1', ['ARGS0','BODY1']
    field_assignments = {
        'target': 'z ',
        'obj': 'z ',
        'iter': 'in z ',
        'test': 'z ',
        'body': ":\n    z\n",
        'orelse': "else:\n    z\n",
        'handlers': "except:\n    z\n",
        'finalbody': "finally:\n    z\n",
        'msg': ", z",
        'value': "z ",
        'args': '(z)',
        'exc':'z ',
        'cause': 'from z ',
        'items': 'z ',
        'name': 'z ',
        'bases': '(z)',
        'returns': '    return z\n'
    }
    skipped_fields = ['type_comment','keywords','decorator','decorator_list', 'type_params']
    fields = deepcopy(analysis[2])
    if 'decorator' in fields or 'decorator_list' in fields:
        code+="@DECORATOR\n"
    fields = [field for field in fields if not field in skipped_fields]
    variables = variables or [f'{str(field).upper()}{i}' for i, field in enumerate(fields)]
    try:
        code += f"{word} "+"".join([field_assignments[field].replace('z',f'{variables[i]}') for i, field in enumerate(fields)])
    except KeyError:
        print(f'{word}: {analysis[2]}')
        quit()
    return code, variables

def handle_function_code(function_name, analysis, code=''):
    args = [arg for i, arg in enumerate(analysis[2][0]['Positional-only'])]
    return f'{function_name}({args})', args

def trial_by_error(word, analysis):
    code=""
    syntax = []
    for a in range(2):
        for b in range(2):
            try:
                exec(f'{'1 'if a else ''}{word}{' 1'if b else ''}')
                syntax.append({'before': a, 'after': b})
            except TypeError:
                syntax.append({'before': a, 'after': b})
            except:
                pass
    for entry in syntax:
        args_list = f'{'VAR1' if entry['before'] or entry['after'] else ''}{', VAR2' if entry['before'] and entry['after'] else ''}'
        temp_code = f'def {word[0].upper()}{word[1:]}({args_list}):return {'VAR1' if entry['before'] else ''} {word} {'VAR1' if (not entry['before']) and entry['after'] else 'VAR2' if entry['before'] and entry['after'] else ''}\n\n'
        analysis[2] = find_arg('func', [categorize_args(args_list)], code=temp_code)
        code += handle_function_code('func', analysis, code=temp_code)[0]
    if syntax:
        return f'{'VAR1' if entry['before'] else ''} {word} {'VAR1' if (not entry['before']) and entry['after'] else 'VAR2' if entry['before'] and entry['after'] else ''}', [arg for i, arg in enumerate(categorize_args(args_list)['Positional-only'])]
    else:
        return False, False

def build_code(word):
    analysis = analyze_input(word)
    code = ""
    if analysis:
        if analysis[1] == 'k':
            if analysis[2]:
                code, args = generate_keyword_code(word, analysis)
            else:
                code, args = trial_by_error(word, analysis)
        elif analysis[1] == 'f':
            code, args = handle_function_code(word, analysis)
        return code, analysis, args
    else:
        print(word)
        print(analysis)
    return code, analysis, []

def build_block(word):
    func_code, analysis, args = build_code(word)
    func_code, args = str(func_code), args or []
    if '' in args:
        del args[args.index('')]
    try:
        start = f'class {word[0].upper()}{word[1:]}:\n'
        init = f'    def __init__({", ".join(['self']+args)}):\n{"".join([f'        self.{arg.lower()}={arg}\n'for arg in args])}'
        lines=func_code.split('\n')
        for i in range(len(lines)):
            for arg in args:lines[i]=lines[i].replace(arg, f'{'{'}self.{arg.lower()}{'}'}')
        code = f'        self.code=f"""\n{"\n".join(lines)}"""'
        return start+init+code
    except Exception as e:
        print(f'\n{word}\n{analysis}\n{args or []}\n{func_code}')
        raise e

def generate_output(word, dict):
    code=build_code(word)[0]
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        try:
            exec(code)
            out = stdout.getvalue()
        except Exception as e:
            out = str(e) + "\nCheck Code <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    dict[word]=f'{'#'*get_terminal_size().columns}\n{word}: {analyze_input(word) if DEBUG else ''}\n----------------------------\n{code}\n----------------------------\n{out}\n{'#'*get_terminal_size().columns}'

def generate_block(word, dict):
    dict[word]=build_block(word)

if __name__ == "__main__":
    keywords = list(keyword.kwlist)

    # Get all built-in objects, functions, and classes in Python
    builtins_list = [name for name in dir(builtins)]
    output = {}
    for word in builtins_list+keywords:
        if word in EXCLUDE_WORDS:continue
        if DEBUG: print(word)
        generate_block(word, output)
    words=list(output.keys())
    while True:
        word = input("Which word do you want to see uses of?")
        try:
            print(output[word])
        except KeyError:
            print("Sorry but i don't know that word")