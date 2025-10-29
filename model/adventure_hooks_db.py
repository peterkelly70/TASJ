from __future__ import annotations

from typing import Dict, List, Optional


class AdventureHooksDB:
    def __init__(self, db_instance):
        self.db = db_instance

    def list_hooks(self) -> List[Dict[str, object]]:
        rows = self.db.execute_query(
            "SELECT hook_id, title, description, planet_id FROM adventure_hooks ORDER BY title"
        )
        return [
            {
                "hook_id": row[0],
                "title": row[1],
                "description": row[2],
                "planet_id": row[3],
            }
            for row in rows
        ]

    def get_hook(self, hook_id: int) -> Optional[Dict[str, object]]:
        records = self.db.read_records("adventure_hooks", {"hook_id": hook_id})
        if not records:
            return None
        columns = self.db.get_table_columns("adventure_hooks")
        row = records[0]
        return {columns[idx]: row[idx] for idx in range(len(columns))}

    def create_hook(self, title: str, description: str, planet_id: Optional[int]) -> int:
        data = {
            "title": title,
            "description": description,
            "planet_id": planet_id,
        }
        result = self.db.create_record("adventure_hooks", data)
        if result != 1:
            raise RuntimeError("Failed to insert adventure hook")
        # Return the last inserted hook id
        hook = self.db.execute_query("SELECT last_insert_rowid()")[0][0]
        return hook

    def update_hook(self, hook_id: int, title: str, description: str, planet_id: Optional[int]) -> None:
        data = {
            "title": title,
            "description": description,
            "planet_id": planet_id,
        }
        result = self.db.update_record("adventure_hooks", data, {"hook_id": hook_id})
        if result != 1:
            raise RuntimeError("Failed to update adventure hook")

    def delete_hook(self, hook_id: int) -> None:
        result = self.db.delete_record("adventure_hooks", {"hook_id": hook_id})
        if result != 1:
            raise RuntimeError("Failed to delete adventure hook")
