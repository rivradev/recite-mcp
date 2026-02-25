from __future__ import annotations

from recite_mcp.memory import MemoryRepository


def test_update_and_list_memory(tmp_path) -> None:  # noqa: ANN001
    repo = MemoryRepository(tmp_path / "memory.md")

    entry = repo.add_instruction("Prefer category Meals for coffee", tags=["category", "coffee"])
    rows = repo.list_instructions()

    assert entry.instruction.startswith("Prefer")
    assert rows[0].tags == ["category", "coffee"]

