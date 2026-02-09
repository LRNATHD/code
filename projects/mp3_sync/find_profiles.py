
import os
import glob

def find_profiles():
    appdata = os.getenv('APPDATA')
    localappdata = os.getenv('LOCALAPPDATA')
    
    potential_paths = {
        'Firefox': os.path.join(appdata, 'Mozilla', 'Firefox', 'Profiles'),
        'Librewolf': os.path.join(appdata, 'Librewolf', 'Profiles'),
        'Waterfox': os.path.join(appdata, 'Waterfox', 'Profiles'),
    }

    print("Checking for browser profiles...")
    
    found_any = False
    for name, path in potential_paths.items():
        if os.path.exists(path):
            print(f"\nFound {name} profiles in: {path}")
            profiles = glob.glob(os.path.join(path, '*'))
            for p in profiles:
                if os.path.isdir(p):
                    print(f"  - {os.path.basename(p)}")
                    found_any = True
        else:
            print(f"\nNo standard {name} profile folder found at: {path}")

    if not found_any:
        print("\nCould not find standard profiles. You might need to locate your profile folder manually.")
        print("In Firefox/Librefox, type 'about:profiles' in the address bar to see the Root Directory.")

if __name__ == "__main__":
    find_profiles()
