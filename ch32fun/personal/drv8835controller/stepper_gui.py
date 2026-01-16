
import tkinter as tk
from tkinter import ttk
import usb.core
import usb.util
import time

CH_USB_VENDOR_ID = 0x1209
CH_USB_PRODUCT_ID = 0xd035
CH_USB_EP_OUT = 0x02

class StepperControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stepper Motor Controller")
        self.root.geometry("400x300")
        
        self.device = None
        self.connect_usb()
        
        # Variables
        self.speed_var = tk.IntVar(value=100) # 0-255
        self.dir_var = tk.IntVar(value=0)     # 0 or 1
        self.enable_var = tk.IntVar(value=0)  # 0 or 1
        
        self.last_send_time = 0
        
        self.create_widgets()
        
    def connect_usb(self):
        try:
            self.device = usb.core.find(idVendor=CH_USB_VENDOR_ID, idProduct=CH_USB_PRODUCT_ID)
            if self.device is None:
                print("Device not found")
                return
            
            try:
                if self.device.is_kernel_driver_active(0):
                    self.device.detach_kernel_driver(0)
            except (NotImplementedError, usb.core.USBError):
                pass
                
            self.device.set_configuration()
            print("Connected to device")
        except usb.core.NoBackendError:
            print("No backend found")
            
    def send_packet(self, force=False):
        current_time = time.time()
        if not force and (current_time - self.last_send_time < 0.5):
            # Throttle
            return
            
        self.last_send_time = current_time

        if self.device is None:
            self.connect_usb()
            if self.device is None:
                return

        # Packet: [Speed, Dir, Enable]
        # Speed: 0-255
        # Dir: 0 or 1
        # Enable: 0 or 1
        
        data = bytearray([
            self.speed_var.get(),
            self.dir_var.get(),
            self.enable_var.get()
        ])
        
        try:
            self.device.write(CH_USB_EP_OUT, data)
            print(f"Sent: Speed={data[0]}, Dir={data[1]}, En={data[2]}")
        except usb.core.USBError as e:
            print(f"Send Error: {e}")
            self.device = None # Force reconnect next time

    def create_widgets(self):
        # Enable Toggle
        # Using a checkbutton that updates immediately
        ttk.Checkbutton(self.root, text="Motor Enable", variable=self.enable_var, command=self.send_packet).pack(pady=10)
        
        # Direction
        dir_frame = ttk.LabelFrame(self.root, text="Direction")
        dir_frame.pack(fill="x", padx=10, pady=5)
        ttk.Radiobutton(dir_frame, text="Clockwise", variable=self.dir_var, value=0, command=self.send_packet).pack(side="left", padx=20)
        ttk.Radiobutton(dir_frame, text="Counter-Clockwise", variable=self.dir_var, value=1, command=self.send_packet).pack(side="left", padx=20)
        
        # Speed Scale
        speed_frame = ttk.LabelFrame(self.root, text="Speed (Left=Slow, Right=Fast)")
        speed_frame.pack(fill="x", padx=10, pady=5)
        
        # Scale command is called on drag, might be too frequent, but let's try.
        # Ideally bind to ButtonRelease-1 or update periodically
        self.speed_scale = ttk.Scale(speed_frame, from_=0, to=255, variable=self.speed_var, orient="horizontal", command=lambda x: self.send_packet())
        self.speed_scale.pack(fill="x", padx=10, pady=10)
        
        # Manual Send Button
        ttk.Button(self.root, text="Resend Command", command=self.send_packet).pack(pady=20)
        
if __name__ == "__main__":
    root = tk.Tk()
    app = StepperControlApp(root)
    root.mainloop()
