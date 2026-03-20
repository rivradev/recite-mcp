from __future__ import annotations

from recite_mcp.memory import MemoryRepository


def test_update_and_list_memory(tmp_path) -> None:  # noqa: ANN001
    repo = MemoryRepository(tmp_path / "memory.md")

    entry = repo.add_instruction(
        "Prefer category Meals for coffee", tags=["category", "coffee"]
    )
    rows = repo.list_instructions()

    assert entry.instruction.startswith("Prefer")
    assert rows[0].tags == ["category", "coffee"]


def test_duplicate_instruction_deduplicates(tmp_path) -> None:  # noqa: ANN001
    repo = MemoryRepository(tmp_path / "memory.md")

    first = repo.add_instruction("Do X", tags=["a"])
    second = repo.add_instruction("Do X", tags=["b"])
    rows = repo.list_instructions()

    assert len(rows) == 1
    assert rows[0].tags == ["b"]
    assert second.timestamp_utc >= first.timestamp_utc


def test_duplicate_instruction_case_insensitive(tmp_path) -> None:  # noqa: ANN001
    repo = MemoryRepository(tmp_path / "memory.md")

    repo.add_instruction("Do X")
    repo.add_instruction("do x")
    rows = repo.list_instructions()

    assert len(rows) == 1


def test_different_instructions_not_deduped(tmp_path) -> None:  # noqa: ANN001
    repo = MemoryRepository(tmp_path / "memory.md")

    repo.add_instruction("Do X")
    repo.add_instruction("Do Y")
    rows = repo.list_instructions()

    assert len(rows) == 2
