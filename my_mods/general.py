from os import system, name
import numpy as np


def file2list(file):
    lines = file.readlines()
    return lines


def iterate_list(my_list):
    # Prints the contents of a list
    for line in my_list:
        print(line)


def iterate_dict(command_dict):
    for key, value in command_dict.items():
        print(f'KEY: {key}')
        if isinstance(value, list):
            for line in value:
                print(f'    VALUE: {line}')  
        else:
            print(f'    VALUE: {value}')


def iterate_nested_dict(command_dict):
    for key, value in command_dict.items():
        print(f'PRIMARY KEY: {key}')
        if isinstance(value, list):
            for line in value:
                print(f'    VALUE: {line}')  
        else:
            iterate_dict(value)
        print('===============================')


def clear(): 
    # Function to clear the terminal screen
    # for Windows
    if name == 'nt':
        _ = system('cls')
    # for Mac and Linux
    else:
        _ = system('clear')


def is_even(num):
    # Python program to check if the input number is odd or even.
    # A number is even if division by 2 gives a remainder of 0.
    # If the remainder is 1, it is an odd number.
    if (num % 2) == 0:
        return True
    else:
        return False

def hex2dec(hex_value):
    return int(hex_value, 16)


def dec2hex(dec_value):
    return format(dec_value, '04x')

def dec2hex2x(dec_value):
    return format(dec_value, '02x')


def input_number(prompt):
    while True:
        try:
            number = float(input(prompt))
            break
        except ValueError:
            pass
    return number


def display_menu(menu_level, menu_name, options):
    clear()
    print(menu_name)
    for i in range(len(options)):
        print(f'  {i + 1}. {options[i]}')
    if menu_level != 'Main':
        print(f'  {i + 2}. Go Back')
        i += 1
        extra_options = 3
    else:
        extra_options = 2
    print(f'  {i + 2}. Quit')

    choice = 0
    while not(np.any(choice == np.arange(len(options)) + 1)):
        choice = input_number('Enter choice: ')

    return choice


def string_to_list(string, delim): 
    li = list(string.split(delim))
    return li 

def check_if_in_list_of_dict(dict_list, value):
    """Check if given value exists in list of dictionaries """
    for elem in dict_list:
        if value in elem.values():
            return True
    return False


