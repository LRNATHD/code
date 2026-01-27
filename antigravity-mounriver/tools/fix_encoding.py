import os
import sys

# Extensions to process
TARGET_EXTS = {'.c', '.h', '.cpp', '.hpp', '.ld', '.S'}

def convert_to_utf8(filepath):
    try:
        with open(filepath, 'rb') as f:
            raw = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    # Try common encodings
    content = None
    encodings = ['utf-8', 'gb18030', 'gbk', 'cp1252', 'latin1']
    
    detected_encoding = None
    for enc in encodings:
        try:
            content = raw.decode(enc)
            detected_encoding = enc
            break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        print(f"Failed to decode {filepath}")
        return

    # If it was already utf-8, checking if we need to save is harder without comparison, 
    # but let's just write validation.
    # Actually, we want to ensure it is saved as UTF-8.
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Converted {filepath} from {detected_encoding} to utf-8")
    except Exception as e:
        print(f"Error writing {filepath}: {e}")

def main():
    if len(sys.argv) > 1:
        search_path = sys.argv[1]
    else:
        search_path = os.getcwd()

    print(f"Scanning {search_path}...")
    for root, dirs, files in os.walk(search_path):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in TARGET_EXTS:
                convert_to_utf8(os.path.join(root, file))

if __name__ == "__main__":
    main()
