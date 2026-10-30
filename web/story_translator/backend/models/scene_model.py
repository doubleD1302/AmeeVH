# -*- coding: utf-8 -*-
"""
server/models/scene_model.py
Quản lý metadata và tiêu đề thân thiện của các phân cảnh / màn chơi
"""

import json
from backend.config import SCENE_FRIENDLY_JSON

friendly_scene_cache = {}

def get_friendly_scene(scene_id):
    global friendly_scene_cache
    if not friendly_scene_cache and SCENE_FRIENDLY_JSON.exists():
        try:
            friendly_scene_cache = json.loads(SCENE_FRIENDLY_JSON.read_text(encoding="utf-8"))
        except Exception:
            friendly_scene_cache = {}
    return friendly_scene_cache.get(scene_id)
