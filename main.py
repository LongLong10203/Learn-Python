import sys
import subprocess
import importlib.util

packages_required = ["threading", "keyboard", "tkinter"]

for package_name in packages_required:
    # Installing necessary packages if they havent been installed
    if importlib.util.find_spec(package_name) is None:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

# External packagaes
import threading
import keyboard
import tkinter as tk
from tkinter import messagebox

# Built-in packages
import importlib
import inspect
import json

class TimeLimitExceededError(Exception):
    pass

def run_with_timeout(function, timeout, args=(), kwargs={}):
    def wrapper():
        try:
            wrapper.result = function(*args, **kwargs)
        except Exception as e:
            wrapper.result = e

    thread = threading.Thread(target=wrapper)
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        raise TimeLimitExceededError("Time Limit Exceeded")
    
    if isinstance(wrapper.result, Exception):
        raise wrapper.result

    return wrapper.result

def run_testcases(function):
    json_file = json.load(open("levels.json"))
    current_level = json_file["current_level"]
    testcases = json_file[current_level]["testcases"]
    
    for testcase in testcases:
        input_field = testcase["input"]
        output_field = testcase["output"]
        try:
            user_output = run_with_timeout(
                function, 1,  # 1 second timeout
                args=([input_field[parameter] for parameter in input_field])
            )
        except Exception as err:
            raise err

        if output_field != user_output:
            return False

    return True

def load_and_run_function():
    # Ensure the module is not cached by removing it if it exists
    if "level" in sys.modules:
        del sys.modules["level"]

    # Reload the module to ensure we get the latest changes
    level_module = importlib.import_module("level")
    importlib.reload(level_module)

    functions = inspect.getmembers(level_module, inspect.isfunction)

    if len(functions) == 1:
        _, function = functions[0]
        return run_testcases(function)
    elif len(functions) > 1:
        raise Exception(f"Multiple functions found: {[name for name, _ in functions]}")
    else:
        raise Exception("No functions found in level.py")

def update_level(next_level=True) -> None:
    json_file = json.load(open("levels.json"))
    current_level = json_file["current_level"]

    if next_level:
        new_level = str(int(current_level) + 1)
        json_file["current_level"] = new_level
        json.dump(json_file, open("levels.json", "w"), indent=4)
        current_level = new_level

    try:
        data = json_file[current_level]
    except KeyError:
        result: bool = messagebox.askyesno("Congratulations", "You have reached the end of the game. Thank you for playing.\nWould you like to start all over again?")
        if result:
            data = json_file["0"]
            json_file["current_level"] = "0"
            json.dump(json_file, open("levels.json", "w"), indent=4)
        else:
            exit(0)
    
    desc, function_name, parameters, return_type = \
    data["desc"], data["function_name"], data["parameters"], data["return_type"]
    parameters = [f"{parameter_name}: {parameters[parameter_name]}" for parameter_name in parameters]
    content = f"# {desc}\n\ndef {function_name}(" + ", ".join(parameters) + f") -> {return_type}:\n\t..."

    with open("level.py", "w") as py_file:
        py_file.write(content)

def handle_result(result: bool) -> None:
    if result:
        messagebox.showinfo("Result", "Accepted")
        update_level()
    else:
        messagebox.showinfo("Result", "Wrong Answer")

def handle_error(err) -> None:
    messagebox.showerror("Error", str(err))

def listen_for_ctrl_s() -> None:
    while True:
        json_file = json.load(open("levels.json"))
        current_level = json_file["current_level"]

        print(f"You are currently in level {current_level}.")
        keyboard.wait("ctrl+s")
        print("Submitting...")

        try:
            result = load_and_run_function()
            root.after(0, handle_result, result)
        except Exception as err:
            root.after(0, handle_error, err)

def main() -> None:
    global root
    root = tk.Tk()
    root.lift()
    root.attributes("-topmost", True)
    root.withdraw()

    update_level(next_level=False)

    listener_thread = threading.Thread(target=listen_for_ctrl_s, daemon=True)
    listener_thread.start()

    root.mainloop()

if __name__ == "__main__":
    main()