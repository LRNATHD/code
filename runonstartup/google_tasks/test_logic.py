
import re
import sys
import os

# Mock the functions to avoid needing the full environment if I can't import easily, 
# but since I am in the directory I'll try to import first or mock if needed.
# Actually I'll just copy the logic to ensure I'm testing the exact logic structure 
# without overhead of dependencies if they are missing in strict separation.
# But better to import to test ACTUAL code.

sys.path.append(os.getcwd())
try:
    from tasks_client import extract_and_increment_value, parse_duration, format_duration
except ImportError:
    # Fallback if imports fail for some reason (e.g. missing google libs in this shell environment)
    print("Could not import tasks_client, using copied logic for verification...")
    
    def parse_duration(duration_str):
        match = re.match(r'^(\d+):(\d{2})$', duration_str.strip())
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            return minutes * 60 + seconds
        return None

    def format_duration(total_seconds):
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"

    def extract_and_increment_value(title, pattern, increment_type, increment_value):
        try:
            regex = re.compile(pattern)
            match = regex.search(title)
            
            if not match:
                return None
            
            if increment_type == 'duration_format':
                # Find duration pattern like "1:30" in the title
                duration_match = re.search(r'(\d+:\d{2})', title)
                if duration_match:
                    current_duration = duration_match.group(1)
                    total_seconds = parse_duration(current_duration)
                    if total_seconds is not None:
                        new_seconds = total_seconds + int(increment_value)
                        new_duration = format_duration(new_seconds)
                        return title.replace(current_duration, new_duration)
        except:
            pass
        return None

# Test Cases
print("Testing 'plank 1:00' with +5 seconds...")
title = "plank 1:00"
pattern = "plank"
increment_value = 5.0
result = extract_and_increment_value(title, pattern, 'duration_format', increment_value)
print(f"Original: {title}")
print(f"Result:   {result}")

print("\nTesting 'plank 1:55' with +10 seconds...")
title = "plank 1:55"
result = extract_and_increment_value(title, pattern, 'duration_format', 10)
print(f"Original: {title}")
print(f"Result:   {result}")
