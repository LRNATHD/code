import customtkinter as ctk
import keyboard
import mss
import mss.tools
from PIL import Image, ImageTk
import threading
import sys
import os
import requests
import base64
import io
import time

# Configuration
HOTKEY = "ctrl+alt+s"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
# API_KEY = os.getenv("GEMINI_API_KEY") 

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class SnippingTool(ctk.CTkToplevel):
    def __init__(self, parent, on_capture):
        super().__init__(parent)
        self.on_capture = on_capture
        
        # Multi-monitor setup using MSS
        with mss.mss() as sct:
            # monitor[0] is the summary of all monitors (the virtual screen)
            monitor = sct.monitors[0]
            self.geometry(f"{monitor['width']}x{monitor['height']}+{monitor['left']}+{monitor['top']}")
            
        self.attributes("-alpha", 0.3)
        self.attributes("-topmost", True)
        self.overrideredirect(True) # Frameless
        self.configure(bg="black")
        
        self.canvas = ctk.CTkCanvas(self, cursor="cross", bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Escape>", lambda e: self.close())
        
        # Bring to front forcefully
        self.lift()
        self.focus_force()

    def on_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="cyan", width=2)

    def on_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_release(self, event):
        x1 = self.start_x
        y1 = self.start_y
        x2 = self.canvas.canvasx(event.x)
        y2 = self.canvas.canvasy(event.y)
        
        # Normalize coordinates
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        
        # Adjust for virtual screen offset if necessary (canvas coords are usually relative to window 0,0)
        # But since window 0,0 is at monitor['left'], monitor['top'], we need to add that back if MSS expects absolute
        # `winfo_rootx` helps check where the window actually is.
        
        root_x = self.winfo_rootx()
        root_y = self.winfo_rooty()
        
        self.close()

        final_left = root_x + left
        final_top = root_y + top
        final_right = root_x + right
        final_bottom = root_y + bottom

        if (final_right - final_left) < 5 or (final_bottom - final_top) < 5:
            return 
            
        self.on_capture(int(final_left), int(final_top), int(final_right), int(final_bottom))

    def close(self):
        self.destroy()

class AIDialog(ctk.CTkToplevel):
    def __init__(self, parent, image):
        super().__init__(parent)
        self.title("AI Analysis")
        self.geometry("600x400") # Smaller, more minimal start
        
        # Minimal Overlay Style
        self.overrideredirect(True) # Remove OS chrome
        self.attributes("-topmost", True)
        self.configure(fg_color="#1e1e1e")
        self.border_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=1, border_color="#007acc")
        self.border_frame.pack(fill="both", expand=True)

        self.image = image
        self.setup_ui()
        
        # Dragging logic
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)
        
        self.lift()
        self.focus_force()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        # Header / Close bar
        header = ctk.CTkFrame(self.border_frame, height=30, fg_color="#2d2d2d", corner_radius=0)
        header.pack(fill="x", side="top")
        
        title_lbl = ctk.CTkLabel(header, text="AI Analysis", font=("Segoe UI", 12))
        title_lbl.pack(side="left", padx=10)
        
        close_btn = ctk.CTkButton(header, text="×", width=30, height=30, 
                                  fg_color="transparent", hover_color="#c42b1c", 
                                  command=self.destroy)
        close_btn.pack(side="right")
        
        # Image Preview (Smaller now)
        preview = self.image.copy()
        preview.thumbnail((580, 150))
        self.tk_image = ctk.CTkImage(light_image=preview, dark_image=preview, size=preview.size)
        
        self.img_label = ctk.CTkLabel(self.border_frame, image=self.tk_image, text="")
        self.img_label.pack(pady=5)
        
        # Input - Compact
        self.input_frame = ctk.CTkFrame(self.border_frame, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=10)
        
        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Ask...", 
                                  height=30, font=("Consolas", 12),
                                  fg_color="#3c3c3c", border_color="#007acc", text_color="white")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry.bind("<Return>", lambda e: self.ask_ai())
        
        # Send Button - Iconic or small
        self.btn = ctk.CTkButton(self.input_frame, text="Ask", width=60, command=self.ask_ai, 
                                 fg_color="#007acc", hover_color="#005a9e")
        self.btn.pack(side="right")
        
        # Output Area
        self.output_box = ctk.CTkTextbox(self.border_frame, font=("Consolas", 12), fg_color="#252526", text_color="#d4d4d4")
        self.output_box.pack(fill="both", expand=True, padx=10, pady=5)
        self.output_box.insert("1.0", "Ready.\n")

    def ask_ai(self):
        prompt = self.entry.get()
        if not prompt:
            prompt = "Explain this image."
            
        self.output_box.delete("1.0", "end")
        self.output_box.insert("end", "Analyzing...\n")
        self.update()
        
        threading.Thread(target=self.run_query, args=(prompt,)).start()
        
    def run_query(self, prompt):
        try:
            # Prepare image
            img_byte_arr = io.BytesIO()
            self.image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            b64_image = base64.b64encode(img_bytes).decode('utf-8')

            # Mock API call if no key
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                # Mock response
                time.sleep(1)
                mock_response = (
                    "**Simulator Mode** (No API Key found)\n\n"
                    "I see your screenshot! Since I am running locally without a GEMINI_API_KEY environment variable, "
                    "I cannot send this to Google Gemini.\n\n"
                    f"**Your Question:** {prompt}\n\n"
                    "**To enable real AI:**\n"
                    "1. Get an API key from aistudio.google.com\n"
                    "2. Set the GEMINI_API_KEY environment variable.\n"
                )
                self.update_output(mock_response)
                return

            # Real API Call (Gemini REST Style)
            headers = {"Content-Type": "application/json"}
            url = f"{API_URL}?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {
                            "mime_type": "image/png",
                            "data": b64_image
                        }}
                    ]
                }]
            }
            
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "No text returned")
                self.update_output(text)
            else:
                self.update_output(f"Error {response.status_code}: {response.text}")

        except Exception as e:
            self.update_output(f"Error: {str(e)}")

    def update_output(self, text):
        # Thread safe update
        self.after(0, lambda: self._safe_write(text))

    def _safe_write(self, text):
        self.output_box.delete("1.0", "end")
        self.output_box.insert("end", text)


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Hide main window
        self.withdraw()
        
        print(f"App running. Press {HOTKEY} to snip.")
        
        # Register hotkey
        keyboard.add_hotkey(HOTKEY, self.trigger_snip)
        
    def trigger_snip(self):
        # Schedule in main loop
        self.after(0, self.start_snip_ui)
        
    def start_snip_ui(self):
        SnippingTool(self, self.capture_screen)
        
    def capture_screen(self, x1, y1, x2, y2):
        # Allow UI to vanish
        time.sleep(0.2)
        
        with mss.mss() as sct:
            # MSS handles multi-monitor, but coordinates must be absolute.
            # winfo_pointer is absolute.
            # We assume primary monitor for simplicity or calculate bbox.
            # MSS standard: top, left, width, height
            monitor = {"top": int(y1), "left": int(x1), "width": int(x2-x1), "height": int(y2-y1)}
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            AIDialog(self, img)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
