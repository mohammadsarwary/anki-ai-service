from __future__ import annotations

import csv
import io
import re
from typing import Any


HEADER_ALIASES = {
    "front": {"front", "term", "word", "question"},
    "back": {"back", "definition", "meaning", "answer"},
    "difficulty": {"difficulty", "level"},
    "tags": {"tags", "tag"},
    "example_sentence": {"example", "examples", "sentence", "example_sentence"},
    "pronunciation": {"pronunciation", "pronounce", "ipa"},
}


def format_ai_back_content(back: dict[str, Any]) -> str:
    lines: list[str] = []
    definition = str(back.get("definition") or "").strip()
    if definition:
        lines.append(definition)

    pronunciation = back.get("pronunciation") if isinstance(back.get("pronunciation"), dict) else {}
    pronunciation_text = str(pronunciation.get("text") or "").strip()
    if pronunciation_text:
        lines.extend(["", f"Pronunciation: {pronunciation_text}"])

    part_of_speech = str(back.get("part_of_speech") or "").strip()
    if part_of_speech:
        lines.extend(["", f"[{part_of_speech}]"])

    usage = str(back.get("usage") or "").strip()
    if usage:
        lines.extend(["", f"Usage: {usage}"])

    examples = back.get("examples") if isinstance(back.get("examples"), list) else []
    normalized_examples = []
    for example in examples:
        if isinstance(example, dict):
            text = str(example.get("text") or "").strip()
        else:
            text = str(example or "").strip()
        if text:
            normalized_examples.append(text)
    if normalized_examples:
        lines.extend(["", "Examples:"])
        lines.extend(f"- {example}" for example in normalized_examples)

    memory_tip = str(back.get("memory_tip") or "").strip()
    if memory_tip:
        lines.extend(["", f"Memory Tip: {memory_tip}"])

    return "\n".join(lines).strip()


def form_errors(form) -> dict[str, list[str]]:
    return {field: [str(error) for error in errors] for field, errors in form.errors.items()}


def parse_card_import_content(
    raw_text: str,
    *,
    default_difficulty: str = "",
    default_tags: list[str] | None = None,
) -> tuple[list[dict[str, Any]], int]:
    text = (raw_text or "").strip()
    if not text:
        return [], 0

    default_tags = default_tags or []
    rows = _read_delimited_rows(text)
    if not rows:
        rows = _read_plain_rows(text)

    cards: list[dict[str, Any]] = []
    skipped = 0
    if not rows:
        return cards, skipped

    index_map, data_rows = _index_import_columns(rows)
    for row in data_rows:
        payload = _row_to_card_payload(row, index_map, default_difficulty=default_difficulty, default_tags=default_tags)
        if payload:
            cards.append(payload)
        else:
            skipped += 1
    return cards, skipped


def _read_delimited_rows(text: str) -> list[list[str]]:
    sample = text[:2048]
    if not any(delimiter in sample for delimiter in [",", "\t", ";"]):
        return []
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
    except csv.Error:
        delimiter = "\t" if "\t" in sample else ","
        dialect = csv.excel()
        dialect.delimiter = delimiter

    reader = csv.reader(io.StringIO(text), dialect)
    return [[cell.strip() for cell in row] for row in reader if any(cell.strip() for cell in row)]


def _read_plain_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for separator in ["\t", " - ", " | ", " = ", ": "]:
            if separator in line:
                front, back = line.split(separator, 1)
                rows.append([front.strip(), back.strip()])
                break
    return rows


def _index_import_columns(rows: list[list[str]]) -> tuple[dict[str, int], list[list[str]]]:
    headers = [_normalize_header(cell) for cell in rows[0]]
    front_index = _find_header_index(headers, "front")
    back_index = _find_header_index(headers, "back")
    if front_index is not None and back_index is not None:
        index_map = {
            key: index
            for key in HEADER_ALIASES
            if (index := _find_header_index(headers, key)) is not None
        }
        return index_map, rows[1:]

    return {
        "front": 0,
        "back": 1,
        "difficulty": 2,
        "tags": 3,
        "example_sentence": 4,
        "pronunciation": 5,
    }, rows


def _row_to_card_payload(
    row: list[str],
    index_map: dict[str, int],
    *,
    default_difficulty: str,
    default_tags: list[str],
) -> dict[str, Any] | None:
    front = _row_value(row, index_map.get("front")).strip()
    back = _row_value(row, index_map.get("back")).strip()
    if not front or not back:
        return None

    difficulty = _row_value(row, index_map.get("difficulty")).lower()
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = default_difficulty if default_difficulty in {"easy", "medium", "hard"} else ""

    tags = [*default_tags, *_split_tags(_row_value(row, index_map.get("tags")))]
    tags = list(dict.fromkeys(tag for tag in tags if tag))

    return {
        "front": front,
        "back": back,
        "difficulty": difficulty or None,
        "tags": tags,
        "example_sentence": _row_value(row, index_map.get("example_sentence")).strip() or None,
        "pronunciation": _row_value(row, index_map.get("pronunciation")).strip() or None,
    }


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _find_header_index(headers: list[str], key: str) -> int | None:
    aliases = HEADER_ALIASES[key]
    for index, header in enumerate(headers):
        if header in aliases:
            return index
    return None


def _row_value(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return row[index]


def _split_tags(raw: str) -> list[str]:
    return [tag.strip() for tag in re.split(r"[,;|]", raw or "") if tag.strip()]
