import BG_random_V3 as bg
import CZ_random_V3 as cz
import DE_random_V3 as de
import ES_random_V3 as es
import EU_random_V3 as eu
import HU_random_V3 as hu
import IT_random_V3 as it
import PL_random_V3 as pl

import random

script_modules = {
    'BG': bg,
    'CZ': cz,
    'DE': de,
    'ES': es,
    'EU': eu,
    'HU': hu,
    'IT': it,
    'PL': pl,
    }

full_script_list = ['BG', 'CZ', 'DE', 'ES', 'EU', 'HU', 'IT', 'PL']

# ['BG', 'CZ', 'DE', 'ES', 'EU', 'HU', 'IT', 'PL']
# ['HU', 'BG']
def list_substraction(list_1, list_2):
    for i in list_2:
        list_1.remove(i)
    new_list = list_1
    return new_list

print("Type countries space-separated, like 'ES EU PL'")
print("Or type '8' to run ALL scripts") # For 8 ERM scripts
print("Or type '8-HU DE' to exclude 1+ script (HU DE) and run all the others")
scripts_string = input("Enter your choice: ")
if scripts_string == "8":
    scripts_to_run = ['BG', 'CZ', 'DE', 'ES', 'EU', 'HU', 'IT', 'PL']
elif "8-" in scripts_string:
    # Remove 8 and minus sign
    removed_scripts = scripts_string[2:].upper().split()
    scripts_to_run = list_substraction(full_script_list, removed_scripts)
    print('Running: ' + ' '.join(scripts_to_run))
else: 
    scripts_to_run = scripts_string.upper().split() # is a list

# Shuffles the list randomly to run scripts in diff order
random.shuffle(scripts_to_run)

# Initialize test data
test_email = input("Enter email: ")
test_phone = "+79444444444"
second_email = None

if len(scripts_to_run) > 5:
    second_email = input('More than 5 scripts, please type in additional email: ')

script_count = 0
for script in scripts_to_run:
    module = script_modules[script]
    main_function = getattr(module, f"main_{script.lower()}")

    current_email = test_email if script_count < 5 else second_email
    
    print(f"\n{'='*60}")
    print(f"Running {script} script with email: {current_email}")
    print(f"{'='*60}")
    
    main_function(current_email, test_phone)
    script_count += 1
        
    
