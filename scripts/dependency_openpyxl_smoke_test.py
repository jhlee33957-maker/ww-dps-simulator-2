from __future__ import annotations

import openpyxl
from openpyxl import load_workbook


def main() -> None:
    assert openpyxl is not None
    assert load_workbook is not None
    print("dependency_openpyxl_smoke_test ok")


if __name__ == "__main__":
    main()
