
from flask import Flask, request, jsonify
import sync_engine
import threading
import os
import json

app = Flask(__name__)
PORT = 9874

@app.route('/api/status', methods=['GET'])
@app.route('/api/sync/status', methods=['GET'])
def get_status():
    return jsonify(sync_engine.get_sync_status())

@app.route('/api/sync', methods=['POST'])
def start_sync():
    success, msg = sync_engine.start_sync()
    return jsonify({'success': success, 'message': msg})

@app.route('/api/sync/stop', methods=['POST'])
def stop_sync():
    success, msg = sync_engine.stop_sync()
    return jsonify({'success': success, 'message': msg})

@app.route('/api/sync/pause', methods=['POST'])
def pause_sync():
    success, msg = sync_engine.pause_sync()
    return jsonify({'success': success, 'message': msg})

@app.route('/api/sync/upload', methods=['POST'])
def upload_sync():
    # Get device path from config
    config = sync_engine.load_sync_config()
    device_path = config.get('device_path')
    if not device_path:
        return jsonify({'success': False, 'message': 'Device path not configured'})
    
    success, msg = sync_engine.start_upload(device_path)
    return jsonify({'success': success, 'message': msg})

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(sync_engine.load_sync_config())

@app.route('/api/config', methods=['POST'])
def set_config():
    data = request.get_json()
    current = sync_engine.load_sync_config()
    current.update(data)
    sync_engine.save_sync_config(current)
    return jsonify({'success': True, 'message': 'Config saved'})

if __name__ == '__main__':
    print(f"MP3 Sync Service running on http://localhost:{PORT}")
    app.run(host='0.0.0.0', port=PORT)
