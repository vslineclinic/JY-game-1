from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import NOTES_FILE, ensure_data_dir
from src.schemas import StrategyNote, UserInput


@dataclass
class StoredNote:
    note_id: str
    created_at: str
    game_name: str
    topic: str
    input_hash: str
    user_input: dict[str, Any]
    strategy_note: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StoredNote":
        return cls(
            note_id=str(data.get("note_id", "")),
            created_at=str(data.get("created_at", "")),
            game_name=str(data.get("game_name", "")),
            topic=str(data.get("topic", "")),
            input_hash=str(data.get("input_hash", "")),
            user_input=dict(data.get("user_input", {})),
            strategy_note=dict(data.get("strategy_note", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class JsonStorage:
    def __init__(self, path: Path = NOTES_FILE):
        self.path = path
        ensure_data_dir()

    def _read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                return raw
        except json.JSONDecodeError:
            backup_path = self.path.with_suffix(".broken.json")
            self.path.replace(backup_path)
            self.path.write_text("[]", encoding="utf-8")
        return []

    def _write_all(self, items: list[dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_note(self, user_input: UserInput, strategy_note: StrategyNote) -> StoredNote:
        note = StoredNote(
            note_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            game_name=user_input.game_name,
            topic=user_input.topic,
            input_hash=make_input_hash(user_input),
            user_input=user_input.to_dict(),
            strategy_note=strategy_note.to_dict(),
        )
        items = self._read_all()
        items.insert(0, note.to_dict())
        self._write_all(items)
        return note

    def list_notes(self) -> list[StoredNote]:
        return [StoredNote.from_dict(item) for item in self._read_all()]

    def get_note(self, note_id: str) -> StoredNote | None:
        for item in self._read_all():
            if item.get("note_id") == note_id:
                return StoredNote.from_dict(item)
        return None

    def delete_note(self, note_id: str) -> bool:
        items = self._read_all()
        new_items = [item for item in items if item.get("note_id") != note_id]
        changed = len(new_items) != len(items)
        if changed:
            self._write_all(new_items)
        return changed

    def find_by_input_hash(self, input_hash: str) -> StoredNote | None:
        for item in self._read_all():
            if item.get("input_hash") == input_hash:
                return StoredNote.from_dict(item)
        return None


def make_input_hash(user_input: UserInput) -> str:
    video_ids = ",".join(v.video_id for v in user_input.selected_videos)
    base = "|".join(
        [
            user_input.game_name,
            user_input.topic,
            user_input.skill_level,
            user_input.grade_level,
            user_input.child_question,
            user_input.practice_goal,
            video_ids,
            user_input.manual_notes[:3000],
        ]
    )
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


# Convenience functions requested in the planning document.
_default_storage = JsonStorage()


def save_note(user_input: UserInput, strategy_note: StrategyNote) -> StoredNote:
    return _default_storage.save_note(user_input, strategy_note)


def list_notes() -> list[StoredNote]:
    return _default_storage.list_notes()


def get_note(note_id: str) -> StoredNote | None:
    return _default_storage.get_note(note_id)


def delete_note(note_id: str) -> bool:
    return _default_storage.delete_note(note_id)
