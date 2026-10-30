# -*- coding: utf-8 -*-
"""
server/views/response_view.py
Chuẩn hóa phản hồi HTTP, trả về JSON hoặc phục vụ file tĩnh
"""

import json
from pathlib import Path

def send_json(handler, data):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)

def serve_file(handler, filepath: Path, content_type=None):
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        handler.send_response(200)
        if content_type:
            handler.send_header("Content-Type", content_type)
        elif filepath.suffix.lower() == ".ttf":
            handler.send_header("Content-Type", "font/ttf")
        elif filepath.suffix.lower() == ".otf":
            handler.send_header("Content-Type", "font/otf")
        elif filepath.suffix.lower() == ".png":
            handler.send_header("Content-Type", "image/png")
        elif filepath.suffix.lower() in [".jpg", ".jpeg"]:
            handler.send_header("Content-Type", "image/jpeg")
        elif filepath.suffix.lower() == ".mp3":
            handler.send_header("Content-Type", "audio/mpeg")
        elif filepath.suffix.lower() == ".wav":
            handler.send_header("Content-Type", "audio/wav")
        elif filepath.suffix.lower() == ".json":
            handler.send_header("Content-Type", "application/json; charset=utf-8")
        elif filepath.suffix.lower() == ".css":
            handler.send_header("Content-Type", "text/css; charset=utf-8")
        elif filepath.suffix.lower() == ".js":
            handler.send_header("Content-Type", "application/javascript; charset=utf-8")

        handler.send_header("Content-Length", str(len(data)))
        handler.send_header("Access-Control-Allow-Origin", "*")
        handler.end_headers()
        handler.wfile.write(data)
    except Exception as e:
        handler.send_error(500, f"Error reading file: {e}")
