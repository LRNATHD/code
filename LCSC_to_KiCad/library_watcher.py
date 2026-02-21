import os
import time
import shutil
import re

# --- CONFIGURATION ---
WATCH_DIR = r"C:\Users\LRNA\Downloads\KiCad_Imports"
TARGET_SYMBOL_LIB = r"C:\Users\LRNA\Desktop\Kicad-Design-Library\EasyEDA.kicad_sym"
TARGET_FOOTPRINT_DIR = r"C:\Users\LRNA\Desktop\Kicad-Design-Library\EasyEDA.pretty"
POLL_INTERVAL = 2  # seconds

# Ensure watch dir exists
if not os.path.exists(WATCH_DIR):
    try:
        os.makedirs(WATCH_DIR)
        print(f"Created watch directory: {WATCH_DIR}")
    except OSError as e:
        print(f"Error creating watch directory: {e}")

def parse_symbol_file(filepath):
    """
    Extracts symbol definitions from a .kicad_sym file.
    Returns a list of symbol strings (including nested symbols).
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex to find (symbol "NAME" ... ) 
    # Match generic balanced parentheses is hard with regex.
    # But KiCad symbols are usually top-level inside current version.
    # Structure: (kicad_symbol_lib ... (symbol "A" ...) (symbol "B" ...) )
    
    symbols = []
    
    # Simple parser for top-level (symbol ...) blocks
    # We assume standard formatting from our converter or KiCad
    
    depth = 0
    start_idx = -1
    in_symbol = False
    
    for i, char in enumerate(content):
        if char == '(':
            if depth == 1: # potential start of symbol (inside lib)
                if content[i+1:i+7] == "symbol":
                    start_idx = i
                    in_symbol = True
            depth += 1
        elif char == ')':
            depth -= 1
            if in_symbol and depth == 1:
                # End of symbol
                symbols.append(content[start_idx:i+1])
                in_symbol = False
                
    return symbols

def merge_symbol(filepath):
    print(f"Processing Symbol: {filepath}")
    new_symbols = parse_symbol_file(filepath)
    
    if not new_symbols:
        print("No symbols found in file.")
        return

    # Read existing library
    if os.path.exists(TARGET_SYMBOL_LIB):
        with open(TARGET_SYMBOL_LIB, 'r', encoding='utf-8') as f:
            lib_content = f.read()
    else:
        # Create new lib header
        lib_content = '(kicad_symbol_lib (version 20211014) (generator "easyeda2kicad_watcher")\n)'
    
    # Check for duplicates (by name)
    # Simple string check for now. Ideally parse names.
    
    updated_content = lib_content.strip()
    if updated_content.endswith(")"):
        updated_content = updated_content[:-1] # Remove closing paren of lib
    
    count = 0
    for sym in new_symbols:
        # Extract name to check duplicate
        match = re.search(r'\(symbol\s+"([^"]+)"', sym)
        if match:
            name = match.group(1)
            # Check if symbol with this name already exists in lib_content
            # This is a bit weak (could match substring), but okay for MVP script
            if f'(symbol "{name}"' in lib_content:
                print(f"Skipping duplicate symbol: {name}")
                continue
        
        updated_content += "\n  " + sym + "\n"
        count += 1
        
    updated_content += ")\n"
    
    if count > 0:
        with open(TARGET_SYMBOL_LIB, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"Merged {count} symbols into {TARGET_SYMBOL_LIB}")
    
    # Delete source file
    try:
        os.remove(filepath)
    except Exception as e:
        print(f"Error deleting file {filepath}: {e}")


def move_footprint(filepath):
    print(f"Processing Footprint: {filepath}")
    filename = os.path.basename(filepath)
    target = os.path.join(TARGET_FOOTPRINT_DIR, filename)
    
    if not os.path.exists(TARGET_FOOTPRINT_DIR):
        os.makedirs(TARGET_FOOTPRINT_DIR)
        
    if os.path.exists(target):
        print(f"Footprint {filename} already exists. Overwriting.")
    
    try:
        shutil.move(filepath, target)
        print(f"Moved to {target}")
    except Exception as e:
        print(f"Error moving footprint: {e}")

def main():
    print(f"Watching {WATCH_DIR}...")
    print(f"Target Symbol Lib: {TARGET_SYMBOL_LIB}")
    print(f"Target Footprint Dir: {TARGET_FOOTPRINT_DIR}")
    
    while True:
        try:
            files = os.listdir(WATCH_DIR)
            for f in files:
                filepath = os.path.join(WATCH_DIR, f)
                if not os.path.isfile(filepath):
                    continue
                
                # Check file extension
                if f.endswith(".kicad_sym"):
                    # Wait for write to finish (simple heuristic)
                    time.sleep(0.5) 
                    try:
                        merge_symbol(filepath)
                    except Exception as e:
                        print(f"Error processing symbol {f}: {e}")
                        
                elif f.endswith(".kicad_mod"):
                    time.sleep(0.5)
                    try:
                        move_footprint(filepath)
                    except Exception as e:
                        print(f"Error processing footprint {f}: {e}")
                        
        except Exception as e:
            print(f"Loop Error: {e}")
            
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
