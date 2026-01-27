import os
import re
import time
import sys

# Instructions:
# 1. Install dependencies: pip install deep-translator chardet
# 2. Run script: python tools/translate_comments.py [directory_path]

try:
    from deep_translator import GoogleTranslator
    import chardet
except ImportError:
    print("Missing dependencies. Please run:")
    print("pip install deep-translator chardet")
    sys.exit(1)

# Configuration
TARGET_EXTS = {'.c', '.h', '.cpp', '.hpp', '.ld', '.S'}
translator = GoogleTranslator(source='auto', target='en')

def contains_chinese(text):
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

def translate_text_block(text):
    """Translates a block of text, handling newlines effectively."""
    if not contains_chinese(text):
        return text

    lines = text.split('\n')
    translated_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped or not contains_chinese(stripped):
            translated_lines.append(line)
            continue
        
        # separate leading/trailing whitespace
        leading = line[:len(line) - len(line.lstrip())]
        trailing = line[len(line.rstrip()):]
        content_to_translate = line.strip()
        
        # Don't translate if it looks like code (rudimentary check)
        if content_to_translate.endswith(';') or content_to_translate.startswith('#'):
            # It might be mixed code/comment, skip for safety or try to separate
            # For now, translate everything in a comment block
            pass

        try:
            # removing special chars that might confuse translator?
            # deep_translator usually handles text okay.
            translated = translator.translate(content_to_translate)
            translated_lines.append(leading + translated + trailing)
            # Sleep briefly to be nice to the API
            time.sleep(0.2)
        except Exception as e:
            print(f"    [Error] Translation failed for line: {content_to_translate[:20]}... {e}")
            translated_lines.append(line)

    return '\n'.join(translated_lines)


def process_file(filepath):
    print(f"Checking {filepath}...")
    
    # 1. Read file with auto-detected encoding
    try:
        raw_data = open(filepath, 'rb').read()
    except Exception as e:
        print(f"    [Error] Could not read file: {e}")
        return

    detected = chardet.detect(raw_data)
    encoding = detected['encoding']
    if not encoding:
        encoding = 'utf-8' # default guess

    try:
        content = raw_data.decode(encoding)
    except UnicodeDecodeError:
        # Fallback for common Chinese encodings
        try:
            content = raw_data.decode('gb18030')
            encoding = 'gb18030'
        except UnicodeDecodeError:
            print(f"    [Error] Failed to decode file with {encoding} or gb18030")
            return

    # 2. Tokenize/Regex to find comments ignoring strings
    # Regex explanation:
    # Group 1: String Literal "..."
    # Group 2: Char Literal '...'
    # Group 3: Block Comment /* ... */
    # Group 4: Line Comment // ...
    pattern = re.compile(r'("(?:\\[\s\S]|[^"\\])*")|(\'(?:\\[\s\S]|[^\'\\])*\')|(/\*[\s\S]*?\*/)|(//.*?$)')

    original_content = content
    modified = False

    def replacer(match):
        nonlocal modified
        s_str = match.group(1)
        s_char = match.group(2)
        s_block = match.group(3)
        s_line = match.group(4)

        if s_str or s_char:
            return match.group(0) # It's code string, return as is
        
        if s_block:
            if contains_chinese(s_block):
                # Extract content inside /* */
                inner = s_block[2:-2]
                translated_inner = translate_text_block(inner)
                modified = True
                return f"/*{translated_inner}*/"
            return s_block

        if s_line:
            if contains_chinese(s_line):
                # Extract content after //
                inner = s_line[2:]
                translated_inner = translate_text_block(inner)
                modified = True
                return f"//{translated_inner}"
            return s_line
        
        return match.group(0)

    # 3. Apply translation
    # Process line by line for line comments? No, regex finditer or sub is better.
    # But python re.sub with multiline flag is needed for $ to match end of line
    try:
        new_content = pattern.sub(replacer, content)
    except Exception as e:
        print(f"    [Error] Regex substitution failed: {e}")
        return

    # 4. Save if changed
    if modified:
        print(f"    -> Translating and saving {filepath} (UTF-8)")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except Exception as e:
            print(f"    [Error] Failed to write file: {e}")
    else:
        # print(f"    No changes.")
        pass

def main():
    if len(sys.argv) > 1:
        search_path = sys.argv[1]
    else:
        search_path = os.getcwd()

    print(f"Scanning directory: {search_path}")
    
    files_to_scan = []
    
    for root, dirs, files in os.walk(search_path):
        # Skip hidden folders like .git
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in TARGET_EXTS:
                files_to_scan.append(os.path.join(root, file))
    
    print(f"Found {len(files_to_scan)} source files.")
    print("Starting translation... (this may take time due to API rate limits)")
    
    for i, file_path in enumerate(files_to_scan):
        process_file(file_path)
        # Optional report progress
        if (i+1) % 10 == 0:
            print(f"Progress: {i+1}/{len(files_to_scan)}")

if __name__ == "__main__":
    main()
