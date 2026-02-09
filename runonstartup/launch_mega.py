import os
import shutil
import sys
import subprocess

def setup_and_run():
    # Detect current python executable
    original_exe = sys.executable
    exe_dir = os.path.dirname(original_exe)
    
    # Target name for the process
    new_exe_name = "UnifiedRunningService.exe"
    target_exe = os.path.join(exe_dir, new_exe_name)
    
    print(f"Original Python: {original_exe}")
    print(f"Target Executable: {target_exe}")
    
    # Try to copy python.exe to UnifiedRunningService.exe
    if not os.path.exists(target_exe):
        try:
            print("Copying python.exe to custom name...")
            shutil.copy2(original_exe, target_exe)
            print("Success!")
        except Exception as e:
            print(f"Failed to copy executable: {e}")
            print("Falling back to standard python execution.")
            target_exe = original_exe
    else:
        print("Custom executable already exists.")

    # Path to the unified server script
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'unified_server.py')
    
    # Command specific to Windows Task Scheduler / Startup or just manual run
    # Use Popen to launch it detached?
    # This script (launch_mega.py) is just a setup tool.
    # We will invoke the NEW executable with the script.
    
    cmd = [target_exe, script_path]
    print(f"Launching with command: {' '.join(cmd)}")
    
    try:
        # Use CREATE_NEW_CONSOLE to detach from current terminal
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        print("Launched successfully in new window.")
    except Exception as e:
        print(f"Failed to launch: {e}")

if __name__ == "__main__":
    setup_and_run()
