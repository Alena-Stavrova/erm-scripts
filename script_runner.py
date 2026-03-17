import BG_order_V0 as bg
import CZ_order_V0 as cz
import DE_order_V0 as de
#import ES_order_V0 as es
import EU_order_V0 as eu
#import HU_order_V0 as hu
#import IT_order_V0 as it
#import PL_order_V0 as pl

import random

script_modules = {
    'BG': bg,
    'CZ': cz,
    'DE': de,
    #'ES': es,
    'EU': eu,
    #'HU': hu,
    #'IT': it,
    #'PL': pl,
    }

scripts_string = input('Type countries space-separated, like "ES EU PL": ')
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
        
    
