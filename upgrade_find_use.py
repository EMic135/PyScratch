import ast
import keyword
import inspect
import builtins
import io
from contextlib import redirect_stdout
from copy import deepcopy

DEBUG = False
TEST = """
class LimitedTrue:
 def __init__(self):
  self.remaining=5
 def get(self):
  if self.remaining>0:
   self.remaining-=1
   return True
  else:
   return False
"""

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


def analyze_input(identifier):
    if keyword.iskeyword(identifier):
        node_class = find_ast_node(identifier)
        if node_class:
            required_fields = get_ast_requirements(node_class)
            return [True, "k", required_fields]
        else:
            return [True, "k", False]
    try:
        obj = getattr(builtins, identifier)
        if callable(obj):
            try:
                sig = inspect.signature(obj)
                args = [param.name for param in sig.parameters.values()]
                return [True, "f", args]
            except (ValueError, TypeError):
                return [False]
    except AttributeError:
        return [False]
    return [False, False]


def get_default_args(func):
    if isinstance(func, str):
        try:
            func = globals()[func]
        except:
            func = getattr(__builtins__, func)
    signature = inspect.signature(func)
    return {
        k: v.default
        for k, v in signature.parameters.items()
        if v.default is not inspect.Parameter.empty
    }


def find_arg(word, all_args, kw_args):
    common_types = [
        1,  # Integer
        1.5,  # Float
        "string_example",  # String
        [1, 2, 3],  # List
        (1, 2),  # Tuple
        {1, 2, 3},  # Set
        {'key': 'value'},  # Dictionary
        None,  # NoneType
        True,  # Boolean True
        False,  # Boolean False
        lambda x: x * 2,  # Function as argument
        str
    ]
    known_args = deepcopy(kw_args)
    unknown_args = {x: 1 for x in all_args if x not in kw_args.keys()}
    type_indexes = [0] * len(unknown_args)

    while True:
        current_values = {arg_name: common_types[type_indexes[i]] for i, arg_name in enumerate(unknown_args)}
        combined_args = {**current_values, **known_args}

        try:
            exec(f"{word}({", ".join([repr(val) for val in current_values.values()] + [f"{key}={repr(val)}" for key, val in known_args.items()])})")
            return combined_args
        except TypeError:
            type_indexes[-1] += 1
            for j in range(len(type_indexes) - 1, -1, -1):
                if type_indexes[j] >= len(common_types):
                    if j == 0:
                        return False
                    type_indexes[j] = 0
                    type_indexes[j - 1] += 1


def assign_variables(analysis, code, test):
    """
    Assign variables to the required fields based on the analysis result.
    """
    variables = []
    if 'test' in analysis[2]: code += test
    for i, field in enumerate(analysis[2]):
        field_assignments = {
            'target': '1',
            'obj': '1',
            'iter': '[1, 2, 3]',
            'test': 'LimitedTrue()'
        }
        var_name = f'var{i}'
        if field in field_assignments:
            variables.append(var_name)
            code += f'{var_name} = {field_assignments[field]}\n'
        elif field == 'body' or field == 'orelse':
            # These fields are used to mark the body and else blocks, no variables needed
            variables.append(None)
    return code, variables


def generate_keyword_code(word, analysis, code, variables):
    """
    Generate the code for Python keywords using the analyzed fields.
    """
    indent = 1
    code += f"{word} "

    for i, field in enumerate(analysis[2]):
        if field == 'target' or field == 'obj':
            code += f'{variables[i]} '
        elif field == 'iter':
            code += f'in {variables[i]} '
        elif field == 'test':
            code += f'{variables[i]}.get() '
        elif field == 'body':
            code += ":\n" + (" " * 4 * indent) + "print('Inside loop/condition')\n"
            indent -= 1
        elif field == 'orelse':
            code += "else:\n" + (" " * 4 * (indent + 1)) + "print('Else condition met')\n"
            indent -= 1
    return code


def handle_function_code(word, analysis):
    """
    Generate code for built-in functions based on inferred or default arguments.
    """
    code = ""
    argument_defaults = get_default_args(word)
    arg_values = find_arg(word, analysis[2], argument_defaults)
    if arg_values is not False:
        variables = []
        for i, arg in enumerate(analysis[2]):
            variables.append(f'var{i}')
            arg_value = repr(arg_values[arg]) if arg in arg_values else 'None'
            code += f'{variables[i]} = {arg_value}\n'
        code += f'print({word}('
        code += ', '.join(f'{arg}={variables[i]}' if arg in argument_defaults else variables[i] for i, arg in enumerate(analysis[2]))
        code += '))'
    else:
        code = f'print({word}())'
    return code


def build_code(word, test=TEST):
    analysis = analyze_input(word)
    code = ""
    if analysis[0]:
        if analysis[1] == 'k':
            if analysis[2]:
                if 'test' in analysis[2]:
                    code += test
                code, variables = assign_variables(analysis, code, test)
                code = generate_keyword_code(word, analysis, code, variables)
        elif analysis[1] == 'f':
            code = handle_function_code(word, analysis)
        return code
    else:
        return f"help({word})"

if __name__ == "__main__":
    keywords = keyword.kwlist

    # Get all built-in objects, functions, and classes in Python
    not_allowed="Error","Warning","Exception"
    builtins_list = [name for name in dir(builtins) if not (name.startswith("__") or [True for word in not_allowed if word in name])]

    # Separate built-in elements into functions, classes, and methods
    builtin_functions = []
    builtin_classes = []
    builtin_methods = []

    for name in builtins_list:
        obj = getattr(builtins, name)
        if inspect.isbuiltin(obj) or inspect.isfunction(obj):
            builtin_functions.append(name)
        elif inspect.isclass(obj):
            builtin_classes.append(name)
        elif inspect.ismethod(obj):
            builtin_methods.append(name)

    # Display the results
    print("Python Keywords:\n", keywords)
    print("\nBuilt-in Functions:\n", builtin_functions)
    print("\nBuilt-in Classes:\n", builtin_classes)
    print("\nBuilt-in Methods:\n", builtin_methods)

    for word in keywords+builtin_functions:
        if word=='open':
            continue
        try:
            print("############################")
            print(word, analyze_input(word))
            print("----------------------------")
            code = build_code(word)
            print(code)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                try:
                    exec(code)
                    out = stdout.getvalue()
                except Exception as e:
                    out = str(e) + "\nCheck Code <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<"
            print(out)
            print("############################")
        except:
            print(f"Failed to process {word}")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                help(word)
            out = stdout.getvalue()
            if f"{word}(" in out:
                start=out.index(f"{word}(")
                print(f"Usage: {out[start:out.index(')',start)+1]}")
            else:
                help(word)