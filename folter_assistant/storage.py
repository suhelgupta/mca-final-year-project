import json
import os


def _ensure_data_folder():
    folder = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(folder, exist_ok=True)
    return folder


def load_json(filename, default=None):
    if default is None:
        default = []
    path = os.path.join(_ensure_data_folder(), filename)
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(filename, data):
    path = os.path.join(_ensure_data_folder(), filename)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
