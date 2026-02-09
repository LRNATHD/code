
import psutil
import ctypes

def get_volume_label(drive_letter):
    """
    Get volume label for a drive letter using ctypes.
    """
    kernel32 = ctypes.windll.kernel32
    volumeNameBuffer = ctypes.create_unicode_buffer(1024)
    fileSystemNameBuffer = ctypes.create_unicode_buffer(1024)
    
    drive_path = drive_letter if drive_letter.endswith('\\') else drive_letter + '\\'
    
    success = kernel32.GetVolumeInformationW(
        ctypes.c_wchar_p(drive_path),
        volumeNameBuffer,
        ctypes.sizeof(volumeNameBuffer),
        None,
        None,
        None,
        fileSystemNameBuffer,
        ctypes.sizeof(fileSystemNameBuffer)
    )
    
    if success:
        return volumeNameBuffer.value
    return ""

def list_drives():
    drives = psutil.disk_partitions()
    print("Listing detected drives and labels:")
    for drive in drives:
        label = get_volume_label(drive.device)
        print(f"Drive: {drive.device} - Label: '{label}'")

if __name__ == "__main__":
    list_drives()
