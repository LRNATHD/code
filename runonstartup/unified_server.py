import multiprocessing
import os
import sys
import time
import shutil
import subprocess

# Paths to the project directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FBREADER_DIR = os.path.join(BASE_DIR, 'fbreader_web')
GOOGLE_TASKS_DIR = os.path.join(BASE_DIR, 'google_tasks')
PARTS_INVENTORY_DIR = os.path.join(BASE_DIR, 'parts_inventory')

def run_fbreader():
    """Worker function to run FBReader Web."""
    print(f"Starting FBReader Web from {FBREADER_DIR}...")
    os.chdir(FBREADER_DIR)
    sys.path.insert(0, FBREADER_DIR)
    
    # Import app and config after setting up path
    try:
        import app
        import config
        app.app.run(host=config.HOST, port=config.PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Error running FBReader: {e}")

def run_google_tasks():
    """Worker function to run Google Tasks App."""
    print(f"Starting Google Tasks from {GOOGLE_TASKS_DIR}...")
    os.chdir(GOOGLE_TASKS_DIR)
    sys.path.insert(0, GOOGLE_TASKS_DIR)
    
    # Import app and config after setting up path
    try:
        import app
        import config
        # automation_thread starts on import
        app.app.run(host=config.HOST, port=config.PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Error running Google Tasks: {e}")

def run_parts_inventory():
    """Worker function to run Parts Inventory Server."""
    print(f"Starting Parts Inventory from {PARTS_INVENTORY_DIR}...")
    os.chdir(PARTS_INVENTORY_DIR)
    sys.path.insert(0, PARTS_INVENTORY_DIR)
    
    # Import server
    try:
        import server
        server.run_server()
    except Exception as e:
        print(f"Error running Parts Inventory: {e}")

if __name__ == '__main__':
    # Redirect output to log file
    sys.stdout = open('unified_server.log', 'w', buffering=1)
    sys.stderr = sys.stdout

    # Ensure correct executable name if renamed
    if getattr(sys, 'frozen', False):
        # If frozen (e.g. PyInstaller), this is standard
        pass
    else:
        # Check if running as "python.exe" or custom name
        executable_name = os.path.basename(sys.executable)
        print(f"Running as: {executable_name}")

    # Create processes for Python apps
    p1 = multiprocessing.Process(target=run_fbreader, name="FBReader")
    p2 = multiprocessing.Process(target=run_google_tasks, name="GoogleTasks")
    p3 = multiprocessing.Process(target=run_parts_inventory, name="PartsInventory")
    
    processes = [p1, p2, p3]

    print("Starting services...")
    for p in processes:
        p.start()
        time.sleep(1) # stagger start

    # Start Cloudflare Tunnel separately
    print("Starting Cloudflare Tunnel...")
    p_cf = None
    try:
        # We need to make sure we don't block, so use Popen
        # Redirect output to a separate log file
        cf_log = open('cloudflared.log', 'w')
        # Use simple Popen. We can't easily wait on it if we want to monitor the python apps too, 
        # but we can keep the Popen object.
        p_cf = subprocess.Popen(["cloudflared", "tunnel", "run", "fbreader"], 
                               stdout=cf_log, 
                               stderr=subprocess.STDOUT)
        print(f"Cloudflare Tunnel started with PID {p_cf.pid}")
    except Exception as e:
        print(f"Failed to start Cloudflare Tunnel: {e}")

    print("All services started. Press Ctrl+C to stop.")

    try:
        # Keep main process alive to monitor children
        while True:
            time.sleep(1)
            # Check if any python process died
            if not any(p.is_alive() for p in processes):
                print("All python processes stopped.")
                break
            
            # Check cloudflared
            if p_cf and p_cf.poll() is not None:
                print(f"Cloudflare Tunnel died with code {p_cf.returncode}")
                # Optional: Restart it?
                # For now just log it
                p_cf = None # Prevent repeated logging
                
    except KeyboardInterrupt:
        print("\nStopping services...")
        for p in processes:
            p.terminate()
            p.join()
        
        # Kill cloudflared
        if p_cf and p_cf.poll() is None:
            p_cf.terminate()
            
        print("Done.")
