from os import system, name

# Clear the command prompt or terminal screen (based on OS type)
if name == 'nt':
    _ = system('cls')
else:
    _ = system('clear')

# Prompt for range start and stop unit numbers
start = input('Enter starting unit number in the range to be removed:  ')
stop = input('Enter ending unit number in the range to be removed:  ')

# Initialize list variable
range_list = []

# Create a list of range values
for i in range(int(start), int(stop) + 1):
    range_list.append(str(i))

# Create command string by using join to add spaces to the values in the list
range_str = "STRASPBAL TYPE(*ENDALC) UNIT(" + ' '.join(range_list) + ')'

# Print the final command to the terminal
print('\n' + range_str + '\n')