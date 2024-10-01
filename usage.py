import ast
import keyword
import inspect
import builtins
import io
from contextlib import redirect_stdout
from copy import deepcopy
from shutil import get_terminal_size
import sys
from time import time

DEBUG = True
TIMEOUT_DURATION = 3  # Timeout in seconds
EXCLUDE_WORDS = ['__loader__','open','quit','exit']

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

DECO = """
def deco(func):
    def wrapper(*args,**kwargs):
        return func(*args,**kwargs)
    return wrapper
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

def analyze_input(identifier, library=''):
    if keyword.iskeyword(identifier):
        node_class = find_ast_node(identifier)
        if node_class:
            required_fields = get_ast_requirements(node_class)
            return [True, "k", required_fields]
        else:
            return [True, "k", []]
    for module in [sys.modules[key] for i, key in enumerate(sys.modules)]:
        try:
            obj = getattr(module, identifier)
            if callable(obj):
                try:
                    return [True, "f", find_arg(identifier, [categorize_func(obj)], library=library)]
                except (ValueError, TypeError):
                    try:
                        return [True, "f", find_arg(identifier, generate_args_from_help(identifier), library=library)]
                    except:
                        return False
        except AttributeError:
            pass
    try:
        exec(identifier.replace(identifier, f'{library + '.' if library else ''}{identifier}'))
        return [True, "k", []]
    except:
        pass
    return False

def find_arg(function_name, args_dicts, code="", library=''):
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
        if args_dict['Var-positional'] and not args_dict['Positional-only']:
            args_dict['Positional-only'].append('var1')
            args_dict['Positional-only'].append('var2')
        args_dict['Positional-only'] = {arg:[] for arg in args_dict['Positional-only']}
        current_indexes = {arg:0 for arg in args_dict['Positional-only']}
        run=True
        while run:
            current_values = {key:common_types[current_indexes[key]] for i, key in enumerate(current_indexes)}
            test_code=deepcopy(code)
            arg_string = ", ".join([current_values[key] for i, key in enumerate(current_indexes)])
            if arg_string:
                if 'potato' in arg_string:
                    test_code+=OBJ
                try:
                    test_code += f"{function_name}({arg_string})"
                    test_out = io.StringIO()
                    with redirect_stdout(test_out):
                        exec(test_code.replace(function_name,f'{library+'.'if library!='' else ''}{function_name}'))
                    test_out.getvalue()
                    for key in args_dict['Positional-only'].keys():
                        args_dict['Positional-only'][key].append(current_values[key])
                except:pass
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
            else:
                run = False
    return args_dicts

def assign_variables(analysis, test=TEST, code='', library=''):
    """
    Assign variables to the required fields based on the analysis result.
    """
    variables = []
    field_assignments = {
        'target': 'z = 1',
        'iter': 'z = [1, 2, 3]',
        'test': 'z = LimitedTrue()',
        'obj': 'z = Potato()',
        'value': "z = 1",
        'decorator': 'z = deco',
        'decorator_list': 'z = deco',
        'cause' : 'try:print(1/0)\nexcept Exception as exc: z = exc',
        'items': 'import io\nfrom contextlib import redirect_stdout\nz =io.StringIO()',
        'msg': 'z = "message"'
    }
    fields = deepcopy(analysis[2])
    variables = variables or [f'{str(field).upper()}{i}' if field in field_assignments else None for i, field in enumerate(fields)]
    code += "\n".join([field_assignments[field].replace('z', f'{variables[i]}') if field in field_assignments else '' for i, field in enumerate(fields)])
    return code, variables

def generate_keyword_code(word, analysis, code, variables, library=''):
    """
    Generate the code for Python keywords using the analyzed fields.
    """
    field_assignments = {
        'target': 'z ',
        'obj': 'z ',
        'iter': 'in z ',
        'test': 'z.get() ',
        'body': ": print('Inside body')\n",
        'orelse': "else: print('Else condition met')\n",
        'handlers': "except: print('Except condition met')\n",
        'finalbody': "finally: print('Final condition met')\n",
        'msg': ", 'Message'",
        'value': " z",
        'type_comment': '',
        'args': '',
        'exc':'RuntimeError("This is an Error Message") ',
        'cause': 'from z ',
        'items': 'redirect_stdout(z)',
        'name': 'z ',
        'bases': '(z)',
        'returns': '    return z\n'
    }
    skipped_fields = ['keywords', 'type_params']
    fields = deepcopy(analysis[2])
    fields = [field for field in fields if not field in skipped_fields]
    variables = variables or [f'{str(field).upper()}{i}' for i, field in enumerate(fields)]
    try:
        code += f"{word} "+"".join([field_assignments[field].replace('z', f'{variables[i]}') if field in field_assignments else '' for i, field in enumerate(fields)])
        if 'items' in analysis[2]:
            code += f'print({variables[analysis[2].index('items')]}.getvalue())'
    except Exception as e:
        print(f'{word}: {analysis[2]}')
        raise e
    return code

def handle_function_code(function_name, analysis, code='', library=''):
    """
    Generate code for built-in functions based on inferred or default arguments.
    """
    for argument_combination in analysis[2]:
        try:
            if argument_combination['Positional-only']:
                if isinstance(argument_combination['Positional-only'][list(argument_combination['Positional-only'].keys())[0]], list):
                    value_combination = [{key: f"{argument_combination['Positional-only'][key][i]}" for key in argument_combination['Positional-only'].keys()} for i in range(len(argument_combination['Positional-only'][list(argument_combination['Positional-only'].keys())[0]]))]
                else:
                    value_combination = [{key: f"{argument_combination['Positional-only'][key]}" for key in argument_combination['Positional-only'].keys()}]
            elif argument_combination['Positional-or-keyword']:
                if isinstance(argument_combination['Positional-or-keyword'][list(argument_combination['Positional-or-keyword'].keys())[0]], list):
                    value_combination = [{key: f"{argument_combination['Positional-or-keyword'][key][i]}" for key in argument_combination['Positional-or-keyword'].keys()} for i in range(len(argument_combination['Positional-or-keyword'][list(argument_combination['Positional-or-keyword'].keys())[0]]))]
                else:
                    value_combination = [{key: f"{argument_combination['Positional-or-keyword'][key]}" for key in argument_combination['Positional-or-keyword'].keys()}]
            elif argument_combination['Keyword-only']:
                if isinstance(argument_combination['Keyword-only'][list(argument_combination['Keyword-only'].keys())[0]], list):
                    value_combination = [{key: f"{argument_combination['Keyword-only'][key][i]}" for key in argument_combination['Keyword-only'].keys()} for i in range(len(argument_combination['Keyword-only'][list(argument_combination['Keyword-only'].keys())[0]]))]
                else:
                    value_combination = [{key: f"{argument_combination['Keyword-only'][key]}" for key in argument_combination['Keyword-only'].keys()}]
            else:continue
        except Exception as e:
            print(argument_combination)
            raise e
        for combination in value_combination:
            variables = []
            for i, arg in enumerate(combination):
                variables.append(f'var{i}')
            try:
                new_code = f'print({function_name}({', '.join(combination[arg] for i, arg in enumerate(combination))}))\n'
            except Exception as e:
                print(argument_combination)
                print(value_combination)
                print(combination)
                raise e
            if new_code not in code:
                code += new_code
    if 'potato' in code:
        code = OBJ + code
    return code

def trial_by_error(word, analysis, library=''):
    code=""
    bool_syntax = []
    other_syntax = []
    for a in range(2):
        for b in range(2):
            try:
                exec(f'{'1 'if a else ''}{word}{' 1'if b else ''}'.replace(word, f'{library + '.' if library else ''}{word}'))
                bool_syntax.append({'before': a, 'after': b})
                other_syntax.append({'before': a, 'after': b})
            except TypeError:
                other_syntax.append({'before': a, 'after': b})
            except:
                pass
    for entry in bool_syntax:
        for a in range(2):
            for b in range(2):
                string = f'print({str(a)+" " if entry['before'] else ''}{word}{" "+str(b) if entry['after'] else ''})\n'
                if not string in code:
                    code += string
    for entry in other_syntax:
        args_list = f'{'var1' if entry['before'] or entry['after'] else ''}{', var2' if entry['before'] and entry['after'] else ''}'
        temp_code = f'def func({args_list}):return {'var1' if entry['before'] else ''} {word} {'var1' if (not entry['before']) and entry['after'] else 'var2' if entry['before'] and entry['after'] else ''}\n\n'
        analysis[2] = find_arg('func', [categorize_args(args_list)], code=temp_code)
        code = handle_function_code('func', analysis, code=temp_code)
    return code

def build_code(word, library=''):
    analysis = analyze_input(word, library=library)
    code = ""
    if analysis:
        if analysis[1] == 'k':
            if analysis[2]:
                if 'test' in analysis[2]:
                    code += TEST
                if 'Potato' in analysis[2]:
                    code += OBJ
                if 'deco' in analysis[2]:
                    code += OBJ
                code, variables = assign_variables(analysis, code=code, library=library)
                code = generate_keyword_code(word, analysis, code, variables, library=library)
            else:
                code = trial_by_error(word, analysis, library=library)
        elif analysis[1] == 'f':
            code = handle_function_code(word, analysis, library=library)
    else:
        code = f'help({word})'
    return code

def generate_output(word, dict, library=''):
    code=build_code(word, library=library).replace(word,f'{library+'.'if library else ''}{word}')
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        try:
            exec(code)
            out = stdout.getvalue()
        except Exception as e:
            out = str(e) + "\nCheck Code <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
    dict[word]=[f'{'#'*get_terminal_size().columns}\n{word}: {analyze_input(word) if DEBUG else ''}\n----------------------------\n{code}',code]

if __name__ == "__main__":
    keywords = list(keyword.kwlist)

    # Get all built-in objects, functions, and classes in Python
    builtins_list = [name for name in dir(builtins)]
    output={}
    libraries = ['math', 'random', 'egsegsegseg']
    words = {}
    for word in builtins_list+keywords:
        if word in EXCLUDE_WORDS:continue
        if DEBUG: print(word)
        generate_output(word, output)
    for lib in libraries:
        try:
            exec(f'import {lib}\nwords["{lib}"]=[member[0] for member in inspect.getmembers({lib})]')
            for word in words[lib]:
                if word in EXCLUDE_WORDS: continue
                if DEBUG: print(word)
                generate_output(word, output, library=lib)
        except ModuleNotFoundError:
            print(f'Can`t find module {lib}')
        except Exception as e:
            raise e
    words=list(output.keys())
    while True:
        word = input("Which word do you want to see uses of?")
        if word in words:
            print(output[word][0])
            exec(output[word][1])
        else:
            print("Sorry but i don't know that word")