from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as element_tree
from collections import defaultdict
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REFERENCE_RE = re.compile(r"^([^!]+)!([A-Z]+[1-9][0-9]*(?::[A-Z]+[1-9][0-9]*)?)$")
CELL_RE = re.compile(r"^([A-Z]+)([1-9][0-9]*)$")
MAIN_NAMESPACE = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RELATIONSHIP_NAMESPACE = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PACKAGE_RELATIONSHIP_NAMESPACE = "{http://schemas.openxmlformats.org/package/2006/relationships}"


def parse_reference(reference: str) -> tuple[str, str]:
    match = REFERENCE_RE.fullmatch(reference)
    if not match:
        raise ValueError(f"malformed workbook reference: {reference!r}")
    return match.group(1), match.group(2)


def _column_number(column: str) -> int:
    number = 0
    for character in column:
        number = number * 26 + ord(character) - ord("A") + 1
    return number


def _cell_coordinates(cell: str) -> tuple[int, int]:
    match = CELL_RE.fullmatch(cell)
    if not match:
        raise ValueError(f"malformed cell coordinate: {cell!r}")
    return int(match.group(2)), _column_number(match.group(1))


def _range_coordinates(cells: str) -> set[tuple[int, int]]:
    start, *end = cells.split(":")
    min_row, min_column = _cell_coordinates(start)
    max_row, max_column = _cell_coordinates(end[0] if end else start)
    if max_row < min_row or max_column < min_column:
        raise ValueError(f"invalid workbook range: {cells!r}")
    return {
        (row, column)
        for row in range(min_row, max_row + 1)
        for column in range(min_column, max_column + 1)
    }


def _shared_strings(workbook: ZipFile) -> list[str]:
    try:
        root = element_tree.fromstring(workbook.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(item.itertext()) for item in root.findall(f"{MAIN_NAMESPACE}si")]


def _sheet_paths(workbook: ZipFile) -> dict[str, str]:
    book = element_tree.fromstring(workbook.read("xl/workbook.xml"))
    relationships = element_tree.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    targets = {
        relation.attrib["Id"]: relation.attrib["Target"]
        for relation in relationships.findall(f"{PACKAGE_RELATIONSHIP_NAMESPACE}Relationship")
    }
    paths: dict[str, str] = {}
    for sheet in book.findall(f"{MAIN_NAMESPACE}sheets/{MAIN_NAMESPACE}sheet"):
        relationship_id = sheet.attrib[f"{RELATIONSHIP_NAMESPACE}id"]
        target = targets[relationship_id]
        paths[sheet.attrib["name"]] = "xl/" + target.lstrip("/")
    return paths


def _cell_value(cell: element_tree.Element, shared_strings: list[str]) -> object:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        inline = cell.find(f"{MAIN_NAMESPACE}is")
        return "" if inline is None else "".join(inline.itertext())
    value = cell.findtext(f"{MAIN_NAMESPACE}v")
    if value is None:
        return None
    if cell_type == "s":
        return shared_strings[int(value)]
    if cell_type == "b":
        return value == "1"
    return value


class SourceWorkbookCache:
    """One-pass XML cache for the exact cells used by the v121 source audit."""

    def __init__(self, workbook_path: Path, references: Iterable[str]) -> None:
        self.workbook_path = workbook_path
        self.references = tuple(sorted(set(references)))
        self.values: dict[str, tuple[object, ...]] = {}
        self.sheet_count = 0
        self.cell_count = 0

    def load(self) -> "SourceWorkbookCache":
        requested: dict[str, dict[str, set[tuple[int, int]]]] = defaultdict(dict)
        for reference in self.references:
            sheet, cells = parse_reference(reference)
            requested[sheet][reference] = _range_coordinates(cells)

        with ZipFile(self.workbook_path) as workbook:
            shared_strings = _shared_strings(workbook)
            paths = _sheet_paths(workbook)
            for sheet_name, ranges in requested.items():
                if sheet_name not in paths:
                    raise ValueError(f"missing workbook sheet: {sheet_name!r}")
                wanted = set().union(*ranges.values())
                found: dict[tuple[int, int], object] = {coordinate: None for coordinate in wanted}
                scanned = 0
                with workbook.open(paths[sheet_name]) as stream:
                    for event, cell in element_tree.iterparse(stream, events=("start", "end")):
                        if event == "start" and cell.tag == f"{MAIN_NAMESPACE}dimension":
                            bounds = _range_coordinates(cell.attrib["ref"])
                            maximum_row = max(row for row, _column in bounds)
                            maximum_column = max(column for _row, column in bounds)
                            if any(row > maximum_row or column > maximum_column for row, column in wanted):
                                raise ValueError(f"out-of-range workbook reference on sheet: {sheet_name!r}")
                        if event != "end" or cell.tag != f"{MAIN_NAMESPACE}c":
                            continue
                        coordinate = _cell_coordinates(cell.attrib["r"])
                        if coordinate in found:
                            found[coordinate] = _cell_value(cell, shared_strings)
                        cell.clear()
                        scanned += 1
                if not scanned:
                    raise ValueError(f"empty workbook sheet: {sheet_name!r}")
                for reference, coordinates in ranges.items():
                    self.values[reference] = tuple(found[coordinate] for coordinate in sorted(coordinates))
                    self.cell_count += len(coordinates)
                self.sheet_count += 1
        return self

    def get(self, reference: str) -> tuple[object, ...]:
        parse_reference(reference)
        if reference not in self.values:
            raise ValueError(f"workbook reference was not collected: {reference!r}")
        return self.values[reference]


def source_references(source: dict) -> list[str]:
    references = [item["ref"] for item in source["workbook"].get("exact_cell_refs", [])]
    references.extend(ref for mapping in source["effect_mappings"] for ref in mapping.get("sheet_cell_refs", []))
    return references


def load_source_cache(source: dict) -> SourceWorkbookCache:
    return SourceWorkbookCache(ROOT / source["workbook"]["local_name"], source_references(source)).load()
