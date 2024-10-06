import datetime
import os
import random
import threading
import time
import sys
import io

def safe_exec(string, in_io=io.StringIO(), out_io=io.StringIO()):
    stdin, stdout = sys.stdin, sys.stdout
    sys.stdin, sys.stdout = in_io, out_io
    try:
        exec(string)
    except SystemExit:
        pass
    sys.stdin, sys.stdout = stdin, stdout


class ErrorLoggingFunction:
    """
    A decorator for logging exceptions raised by a function to a file.

    Args:
        function (callable): The function to be decorated.
        log_file (str, optional): The name of the log file. Defaults to "error.txt".
        error_func (callable, optional): A function to call on error
    """

    def __init__(self, function, log_file="error.txt", error_func=lambda: None):
        """
        Initialize the ErrorLoggingFunction decorator.
        """
        self.function = function
        self.log_file = log_file
        self.error_func = error_func
        # Create log file if it doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, "w"):
                pass

    def __call__(self, *args):
        """
        Call the decorated function and log any raised exceptions.
        """
        error_message = ""
        try:
            return self.function(*args)
        except (Exception, BaseException) as e:
            if isinstance(e, (tuple, list)):
                for item in e:
                    tb = item.__traceback__
                    error_message += f"[{datetime.datetime.now()}] [{__file__}] {type(item).__name__} : {item} : "
                    while tb is not None:
                        if not (tb.tb_frame.f_code.co_name == "__call__") :
                            error_message += f"{tb.tb_frame.f_code.co_name} line:{tb.tb_lineno}, "
                        tb = tb.tb_next
                    error_message+="\n"
            else:
                tb = e.__traceback__
                error_message += f"[{datetime.datetime.now()}] [{__file__}] {type(e).__name__} : {e} : "
                tb = tb.tb_next
                while tb is not None:
                    error_message += f"{tb.tb_frame.f_code.co_name} line:{tb.tb_lineno}"
                    tb = tb.tb_next
                    if tb is not None:
                        error_message += ", "
                error_message += "\n"
        except:
            error_message += f"[{datetime.datetime.now()}] [{__file__}] {self.function.__name__} unknown error"

        if error_message!="":
            self.error_func()
            with open(self.log_file, "a") as f:
                try:
                    f.write(error_message)
                    f.flush()
                except:
                    print("F")
                    # If there is an error writing to the log file, start a new thread to wait
                    # a random amount of time and retry the write operation.
                    def retry_write():
                        wait_time = random.randint(1, 10)/100
                        time.sleep(wait_time)
                        with open(self.log_file, "a") as f2:
                            try:
                                f2.write(error_message)
                                f2.flush()
                            except:
                                pass
                    threading.Thread(target=retry_write).start()


class DataLoggingFunction:
    """
    A decorator for logging data made by a function to a file.

    Args:
        function (callable): The function to be decorated.
        log_file (str, optional): The name of the log file. Defaults to "log.txt".
    """

    def __init__(self, function, log_file="log.txt"):
        """
        Initialize the DataLoggingFunction decorator.
        """
        self.function = function
        self.log_file = log_file
        # Create log file if it doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, "w"):
                pass

    def __call__(self, *args, **kwargs):
        """
        Call the decorated function and log any data.
        """
        result = self.function(*args, **kwargs)
        data = f"[{datetime.datetime.now()}] [{__file__}] {self.function.__name__} : {str(result)}\n"
        with open(self.log_file, "a") as f:
            try:
                f.write(data)
                f.flush()
            except:
                print("F")
                # If there is an error writing to the log file, start a new thread to wait
                # a random amount of time and retry the write operation.
                def retry_write():
                    wait_time = random.randint(1, 10)/100
                    time.sleep(wait_time)
                    with open(self.log_file, "a") as f2:
                        try:
                            f2.write(data)
                            f2.flush()
                        except:
                            pass
                threading.Thread(target=retry_write).start()
        return result

def test():
    @DataLoggingFunction
    def works():
        return "hi"
    @ErrorLoggingFunction
    def divide_by_zero():
        x = 1 / 0
    @ErrorLoggingFunction
    def read_file():
        with open("nonexistent_file.txt", "r") as f:
            data = f.read()
    @ErrorLoggingFunction
    def add_numbers():
        return "1" + 2
    @ErrorLoggingFunction
    def get_value():
        my_dict = {"key1": "value1", "key2": "value2"}
        return my_dict["nonexistent_key"]
    import requests
    @ErrorLoggingFunction
    def make_request():
        response = requests.get("http://nonexistent_website.com")
        return response.status_code
    class MyClass:
        def __init__(self, value):
            self.value = value

        @ErrorLoggingFunction
        def __del__(self):
            raise Exception("Error in __del__ method")

    @ErrorLoggingFunction
    def raise_exception_in_del():
        obj = MyClass()
        del obj  # This will call the __del__ method and raise an exception
    @ErrorLoggingFunction
    def access_nonexistent_attr():
        obj = MyClass(10)
        return obj.nonexistent_attribute
    @ErrorLoggingFunction
    def convert_invalid_string_to_int():
        return int("not_an_integer")
    @ErrorLoggingFunction
    def access_out_of_range_index():
        my_list = [1, 2, 3]
        return my_list[10]
    @ErrorLoggingFunction
    def access_undefined_variable():
        return undefined_variable
    @ErrorLoggingFunction
    def infinite_recursion():
        return infinite_recursion()

    works()
    divide_by_zero()
    read_file()
    add_numbers()
    get_value()
    make_request()
    access_nonexistent_attr()
    convert_invalid_string_to_int()
    access_out_of_range_index()
    access_undefined_variable()
    infinite_recursion()

if __name__ == '__main__':
    test()