
import psutil
import subprocess

def list_drives():
    drives = psutil.disk_partitions()
    for drive in drives:
        device_id = drive.device[:2]  # e.g., 'C:'
        try:
            cmd = f'wmic logicaldisk where "DeviceID=\'{device_id}\'" get VolumeName'
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            lines = [line.strip() for line in output.splitlines() if line.strip()]
            if len(lines) > 1:
                label = lines[1]
            else:
                label = "<No Label>"
            print(f"Drive: {device_id}, Label: '{label}'")
        except Exception as e:
            print(f"Error checking {device_id}: {e}")

if __name__ == "__main__":
    list_drives()
