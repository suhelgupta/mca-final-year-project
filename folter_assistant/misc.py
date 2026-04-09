from .storage import load_json, save_json


class NotesManager:
    FILE_NAME = "notes.json"

    def __init__(self):
        self.notes = load_json(self.FILE_NAME, default=[])

    def _save(self):
        save_json(self.FILE_NAME, self.notes)

    def add_note(self, title, content):
        note = {
            "id": len(self.notes) + 1,
            "title": title,
            "content": content,
        }
        self.notes.append(note)
        self._save()
        return note

    def list_notes(self):
        return self.notes

    def get_note(self, note_id):
        for note in self.notes:
            if note.get("id") == note_id:
                return note
        return None

    def remove_note(self, note_id):
        self.notes = [note for note in self.notes if note.get("id") != note_id]
        self._save()
