from pathlib import Path
import os

path = Path('brain.py')
text = path.read_text(encoding='utf-8')
needle = 'def _contains(text: str, *words) -> bool:\n    return any(w in text for w in words)\n\n# ---------------------------------------------------------------------------\n'
insert = '''def _contains(text: str, *words) -> bool:
    return any(w in text for w in words)


def _open_with_chrome(url: str | None = None) -> bool:
    if url is None:
        url = "https://www.google.com"
    try:
        subprocess.Popen(["chrome", url], shell=False)
        return True
    except Exception:
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False


def _launch_vscode() -> bool:
    candidates = [
        ["code"],
        [os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Microsoft VS Code", "Code.exe")],
        ["C:\\Program Files\\Microsoft VS Code\\Code.exe"],
        ["C:\\Program Files (x86)\\Microsoft VS Code\\Code.exe"],
    ]
    for cmd in candidates:
        if not cmd[0]:
            continue
        try:
            subprocess.Popen(cmd, shell=False)
            return True
        except Exception:
            continue
    return False


def _launch_hand_gesture() -> bool:
    script_path = os.path.join(os.path.dirname(__file__), "hand-guesture", "hand-guesture.py")
    if not os.path.exists(script_path):
        return False
    try:
        subprocess.Popen([sys.executable, script_path], shell=False)
        return True
    except Exception:
        return False

# ---------------------------------------------------------------------------
'''
if needle not in text:
    raise RuntimeError('Needle not found in brain.py')
text = text.replace(needle, insert)
path.write_text(text, encoding='utf-8')
print('Inserted helper block')
