import http.server
import socketserver
import urllib.parse
import json
import usb.core
import usb.util
import sys
import time
import threading

# USB Configuration
CH_USB_VENDOR_ID    = 0x1209
CH_USB_PRODUCT_ID   = 0xd035
CH_USB_EP_OUT       = 0x02
CH_USB_EP_IN        = 0x81
CH_USB_TIMEOUT_MS   = 1000

# Head position tracking (in steps)
# Limit: ±100 steps (±60 degrees)
HEAD_LIMIT = 100
head_position = 0  # Current head position (0 = center)
head_lock = threading.Lock()

# Motor state
state = {
    "m1": {"speed": 0, "dir": 0, "enable": 0}, # Base (X-axis)
    "m2": {"speed": 0, "dir": 0, "enable": 0}  # Head (Y-axis)
}
prev_state = None

class USBHandler:
    def __init__(self):
        self.device = None
        self.connected = False
        self.lock = threading.Lock()
        
        # Try initial connection
        self._try_connect()
        
        # Start background reconnection thread
        self.reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self.reconnect_thread.start()

    def _reconnect_loop(self):
        """Background thread that attempts to reconnect if disconnected."""
        while True:
            time.sleep(2)  # Check every 2 seconds
            with self.lock:
                if not self.connected:
                    self._try_connect()

    def _try_connect(self):
        """Attempt to connect to the USB device. Must be called with lock held or at init."""
        try:
            self.device = usb.core.find(idVendor=CH_USB_VENDOR_ID, idProduct=CH_USB_PRODUCT_ID)
            if self.device:
                try:
                    if self.device.is_kernel_driver_active(0):
                        self.device.detach_kernel_driver(0)
                except:
                    pass
                self.device.set_configuration()
                self.connected = True
                print("✓ USB Device Connected", flush=True)
            else:
                self.connected = False
        except Exception as e:
            print(f"USB Connection Error: {e}", flush=True)
            self.device = None
            self.connected = False

    def send_packet(self, s1, d1, e1, s2, d2, e2):
        """Send a packet and read the echo. Handles disconnection gracefully."""
        with self.lock:
            if not self.connected or self.device is None:
                return None
            
            payload = bytearray([s1, d1, e1, s2, d2, e2])
            
            try:
                self.device.write(CH_USB_EP_OUT, payload)
                response = self.device.read(CH_USB_EP_IN, 64, CH_USB_TIMEOUT_MS)
                print(f"TX: {list(payload)} -> RX: {list(response)}", flush=True)
                return list(response)
            except usb.core.USBTimeoutError:
                print(f"TX: {list(payload)} -> RX: TIMEOUT", flush=True)
                return None
            except usb.core.USBError as e:
                print(f"✗ USB Disconnected: {e}", flush=True)
                self.connected = False
                self.device = None
                return None
            except Exception as e:
                print(f"USB Error: {e}", flush=True)
                self.connected = False
                self.device = None
                return None
    
    def is_connected(self):
        """Check if device is currently connected."""
        with self.lock:
            return self.connected

usb_handler = USBHandler()

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        global state, prev_state, head_position
        
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode())
        elif self.path.startswith('/api/joystick'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            # Get joystick position (-1 to 1 for x and y)
            x = float(params.get('x', [0])[0])  # -1 (left) to 1 (right)
            y = float(params.get('y', [0])[0])  # -1 (up) to 1 (down)
            
            # Convert to speed and direction
            # Base (M1) = X-axis
            m1_speed = int(abs(x) * 255)
            m1_dir = 1 if x > 0 else 0
            m1_enable = 1 if abs(x) > 0.1 else 0
            
            # Head (M2) = Y-axis
            m2_speed = int(abs(y) * 255)
            m2_dir = 1 if y > 0 else 0  # 1 = down, 0 = up
            m2_enable = 1 if abs(y) > 0.1 else 0
            
            # Check head limits
            with head_lock:
                # If trying to move up (dir=0) and at upper limit, disable
                if m2_enable and m2_dir == 0 and head_position <= -HEAD_LIMIT:
                    m2_enable = 0
                    print(f"HEAD LIMIT: At upper limit ({head_position} steps)", flush=True)
                # If trying to move down (dir=1) and at lower limit, disable
                elif m2_enable and m2_dir == 1 and head_position >= HEAD_LIMIT:
                    m2_enable = 0
                    print(f"HEAD LIMIT: At lower limit ({head_position} steps)", flush=True)
            
            state["m1"] = {"speed": m1_speed, "dir": m1_dir, "enable": m1_enable}
            state["m2"] = {"speed": m2_speed, "dir": m2_dir, "enable": m2_enable}
            
            # Only send if state changed
            current = json.dumps(state)
            if prev_state != current:
                prev_state = current
                usb_handler.send_packet(
                    m1_speed, m1_dir, m1_enable,
                    m2_speed, m2_dir, m2_enable
                )
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            with head_lock:
                response = {"state": state, "head_position": head_position}
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path.startswith('/api/head_step'):
            # Called by receiver to report step taken
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            direction = int(params.get('dir', [0])[0])
            
            with head_lock:
                if direction == 0:  # up
                    head_position -= 1
                else:  # down
                    head_position += 1
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            with head_lock:
                self.wfile.write(json.dumps({"head_position": head_position}).encode())
                
        elif self.path == '/api/reset_head':
            with head_lock:
                head_position = 0
            print("Head position reset to center", flush=True)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"head_position": 0}).encode())
        else:
            self.send_error(404)

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Turret Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
    <style>
        * { box-sizing: border-box; touch-action: none; }
        body { 
            background: linear-gradient(135deg, #1e1e2f 0%, #0f0f1a 100%);
            color: #ffffff;
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
            user-select: none;
        }
        .panel {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(15px);
            padding: 30px;
            border-radius: 30px;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 20px 50px rgba(0,0,0,0.3);
            text-align: center;
        }
        h1 {
            margin: 0 0 20px 0;
            font-weight: 300;
            letter-spacing: 4px;
            text-transform: uppercase;
            font-size: 1.3rem;
            color: rgba(255,255,255,0.8);
        }
        
        .joystick-container {
            width: 280px;
            height: 280px;
            background: rgba(0,0,0,0.3);
            border-radius: 50%;
            position: relative;
            margin: 0 auto 20px;
            border: 2px solid rgba(255,255,255,0.1);
        }
        
        .joystick-zone {
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
        }
        
        .joystick-center {
            position: absolute;
            width: 20px;
            height: 20px;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
        
        .joystick-crosshair-h {
            position: absolute;
            width: 100%;
            height: 1px;
            background: rgba(255,255,255,0.1);
            top: 50%;
        }
        
        .joystick-crosshair-v {
            position: absolute;
            width: 1px;
            height: 100%;
            background: rgba(255,255,255,0.1);
            left: 50%;
        }
        
        .joystick-handle {
            position: absolute;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            border-radius: 50%;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            box-shadow: 0 5px 20px rgba(0,0,0,0.4);
            cursor: grab;
            transition: box-shadow 0.2s;
        }
        
        .joystick-handle:active {
            cursor: grabbing;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }
        
        .joystick-handle.active {
            background: linear-gradient(135deg, #3498db, #2980b9);
        }
        
        .info {
            font-size: 0.75rem;
            color: rgba(255,255,255,0.4);
            margin-top: 15px;
        }
        
        .head-indicator {
            width: 200px;
            height: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            margin: 10px auto;
            position: relative;
            overflow: hidden;
        }
        
        .head-marker {
            position: absolute;
            width: 4px;
            height: 100%;
            background: #e74c3c;
            left: 50%;
            transform: translateX(-50%);
            transition: left 0.1s;
        }
        
        .head-limits {
            position: absolute;
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: space-between;
            padding: 0 10%;
        }
        
        .head-limit-marker {
            width: 2px;
            height: 100%;
            background: rgba(255,255,255,0.3);
        }
        
        .reset-btn {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.8rem;
            margin-top: 10px;
        }
        
        .reset-btn:hover {
            background: rgba(255,255,255,0.2);
        }
    </style>
</head>
<body>
    <div class="panel">
        <h1>Turret Joystick</h1>
        
        <div class="joystick-container" id="joystickContainer">
            <div class="joystick-zone" id="joystickZone"></div>
            <div class="joystick-crosshair-h"></div>
            <div class="joystick-crosshair-v"></div>
            <div class="joystick-center"></div>
            <div class="joystick-handle" id="joystickHandle"></div>
        </div>
        
        <div class="info">Head Position (±60°)</div>
        <div class="head-indicator">
            <div class="head-limits">
                <div class="head-limit-marker"></div>
                <div class="head-limit-marker"></div>
            </div>
            <div class="head-marker" id="headMarker"></div>
        </div>
        
        <button class="reset-btn" onclick="resetHead()">Reset Head Position</button>
        
        <div class="info" id="debug">X: 0.00, Y: 0.00</div>
    </div>

    <script>
        const container = document.getElementById('joystickContainer');
        const handle = document.getElementById('joystickHandle');
        const zone = document.getElementById('joystickZone');
        const debug = document.getElementById('debug');
        const headMarker = document.getElementById('headMarker');
        
        let isDragging = false;
        let centerX, centerY, maxRadius;
        let currentX = 0, currentY = 0;
        let sendInterval = null;
        
        function init() {
            const rect = container.getBoundingClientRect();
            centerX = rect.width / 2;
            centerY = rect.height / 2;
            maxRadius = rect.width / 2 - 30; // Handle radius
        }
        
        function updateHandle(clientX, clientY) {
            const rect = container.getBoundingClientRect();
            let x = clientX - rect.left - centerX;
            let y = clientY - rect.top - centerY;
            
            // Clamp to circle
            const dist = Math.sqrt(x*x + y*y);
            if (dist > maxRadius) {
                x = (x / dist) * maxRadius;
                y = (y / dist) * maxRadius;
            }
            
            handle.style.left = (centerX + x) + 'px';
            handle.style.top = (centerY + y) + 'px';
            
            // Normalize to -1 to 1
            currentX = x / maxRadius;
            currentY = y / maxRadius;
            
            debug.textContent = `X: ${currentX.toFixed(2)}, Y: ${currentY.toFixed(2)}`;
        }
        
        function resetHandle() {
            handle.style.left = '50%';
            handle.style.top = '50%';
            currentX = 0;
            currentY = 0;
            debug.textContent = 'X: 0.00, Y: 0.00';
            sendState();
        }
        
        function sendState() {
            fetch(`/api/joystick?x=${currentX.toFixed(3)}&y=${currentY.toFixed(3)}`)
                .then(r => r.json())
                .then(d => {
                    // Update head position indicator
                    const pos = d.head_position || 0;
                    const percent = 50 + (pos / 100) * 40; // Map -100..100 to 10%..90%
                    headMarker.style.left = percent + '%';
                });
        }
        
        function startDrag(e) {
            isDragging = true;
            handle.classList.add('active');
            init();
            
            const touch = e.touches ? e.touches[0] : e;
            updateHandle(touch.clientX, touch.clientY);
            
            // Start sending at 20Hz
            sendState();
            sendInterval = setInterval(sendState, 50);
        }
        
        function moveDrag(e) {
            if (!isDragging) return;
            e.preventDefault();
            
            const touch = e.touches ? e.touches[0] : e;
            updateHandle(touch.clientX, touch.clientY);
        }
        
        function endDrag() {
            if (!isDragging) return;
            isDragging = false;
            handle.classList.remove('active');
            
            if (sendInterval) {
                clearInterval(sendInterval);
                sendInterval = null;
            }
            
            resetHandle();
        }
        
        function resetHead() {
            fetch('/api/reset_head');
            headMarker.style.left = '50%';
        }
        
        // Event listeners
        zone.addEventListener('mousedown', startDrag);
        zone.addEventListener('touchstart', startDrag);
        
        document.addEventListener('mousemove', moveDrag);
        document.addEventListener('touchmove', moveDrag, { passive: false });
        
        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchend', endDrag);
        
        // Keyboard support
        const keys = {};
        document.addEventListener('keydown', (e) => {
            if (e.repeat) return;
            keys[e.key] = true;
            updateFromKeys();
            if (!sendInterval) {
                sendInterval = setInterval(sendState, 50);
            }
        });
        
        document.addEventListener('keyup', (e) => {
            delete keys[e.key];
            updateFromKeys();
            if (Object.keys(keys).length === 0) {
                if (sendInterval) {
                    clearInterval(sendInterval);
                    sendInterval = null;
                }
                resetHandle();
            }
        });
        
        function updateFromKeys() {
            let x = 0, y = 0;
            if (keys['ArrowLeft']) x -= 1;
            if (keys['ArrowRight']) x += 1;
            if (keys['ArrowUp']) y -= 1;
            if (keys['ArrowDown']) y += 1;
            
            currentX = x;
            currentY = y;
            
            handle.style.left = (50 + x * 35) + '%';
            handle.style.top = (50 + y * 35) + '%';
            debug.textContent = `X: ${x.toFixed(2)}, Y: ${y.toFixed(2)}`;
        }
        
        init();
    </script>
</body>
</html>
"""

PORT = 8000
while True:
    try:
        httpd = socketserver.TCPServer(("", PORT), QuietHandler)
        print(f"Serving at http://localhost:{PORT}", flush=True)
        break
    except OSError:
        print(f"Port {PORT} in use, trying {PORT+1}...", flush=True)
        PORT += 1

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
httpd.server_close()
