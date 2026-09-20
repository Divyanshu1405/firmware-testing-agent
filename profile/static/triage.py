"""Static ELF Triage for Firmware Testing.

Inspects compiled ARM ELF firmware to extract architecture, entry point,
interrupt vector table, section map, symbols, strings, and debug info.
Emits structured JSON to unblock platform selection and simulator setup.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional

from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_FIRMWARE = ROOT_DIR / "original.elf"
if not DEFAULT_FIRMWARE.exists():
    DEFAULT_FIRMWARE = ROOT_DIR / "firmware" / "inputs" / "firmware1.elf"
DEFAULT_OUTPUT = ROOT_DIR / "profile" / "static" / "static.json"

VECTOR_NAMES = [
    "initial_sp",
    "reset_handler",
    "nmi_handler",
    "hardfault_handler",
    "memmanage_handler",
    "busfault_handler",
    "usagefault_handler",
    "reserved1",
    "reserved2",
    "reserved3",
    "reserved4",
    "svcall_handler",
    "debugmon_handler",
    "reserved5",
    "pendsv_handler",
    "systick_handler",
]


def extract_strings(data: bytes, min_len: int = 4) -> List[str]:
    """Extract printable ASCII strings of at least min_len length."""
    pattern = re.compile(rb"[\x20-\x7e]{" + str(min_len).encode() + rb",}")
    return [match.group(0).decode("ascii", errors="ignore") for match in pattern.finditer(data)]


def extract_vector_table(elf: ELFFile) -> Dict[str, str]:
    """Extract standard ARM Cortex-M interrupt vector table entries."""
    vector_table: Dict[str, str] = {}
    isr_section = elf.get_section_by_name(".isr_vector")
    if isr_section is not None:
        data = isr_section.data()
        count = min(len(VECTOR_NAMES), len(data) // 4)
        if count > 0:
            unpacked = struct.unpack(f"<{count}I", data[: count * 4])
            for name, addr in zip(VECTOR_NAMES[:count], unpacked):
                vector_table[name] = hex(addr)
    return vector_table


def analyze_firmware(firmware_path: Path | str) -> Dict[str, Any]:
    """Perform comprehensive static analysis of a firmware ELF binary."""
    path = Path(firmware_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Firmware ELF not found: {path}")

    with open(path, "rb") as f:
        elf = ELFFile(f)

        # 1. Basic Header Information
        result: Dict[str, Any] = {
            "file": path.name,
            "format": "ELF",
            "architecture": elf.get_machine_arch(),
            "endianness": "little" if elf.little_endian else "big",
            "entry_point": hex(elf.header["e_entry"]),
            "vector_table": extract_vector_table(elf),
            "sections": [],
            "symbols": {
                "is_stripped": True,
                "total_symbols": 0,
                "function_count": 0,
                "functions": [],
                "object_count": 0,
                "objects": [],
            },
            "has_debug_info": False,
            "strings": [],
        }

        # 2. Section Analysis
        rodata_data = bytearray()
        has_debug = False

        for section in elf.iter_sections():
            sec_name = section.name
            sh_flags = section["sh_flags"]
            result["sections"].append({
                "name": sec_name,
                "address": hex(section["sh_addr"]),
                "size": section["sh_size"],
                "offset": hex(section["sh_offset"]),
                "type": section["sh_type"],
            })

            if ".debug" in sec_name or ".line" in sec_name:
                has_debug = True

            if sec_name in (".rodata", ".text"):
                rodata_data.extend(section.data())

            # Symbol Table Inspection
            if isinstance(section, SymbolTableSection):
                result["symbols"]["is_stripped"] = False
                result["symbols"]["total_symbols"] = section.num_symbols()
                functions = []
                objects = []
                for sym in section.iter_symbols():
                    st_type = sym["st_info"]["type"]
                    name = sym.name
                    if not name:
                        continue
                    if st_type == "STT_FUNC":
                        functions.append(name)
                    elif st_type == "STT_OBJECT":
                        objects.append(name)
                result["symbols"]["function_count"] = len(functions)
                result["symbols"]["functions"] = sorted(set(functions))
                result["symbols"]["object_count"] = len(objects)
                result["symbols"]["objects"] = sorted(set(objects))

        result["has_debug_info"] = has_debug

        # 3. String Extraction (deduplicated, sorted)
        extracted = extract_strings(bytes(rodata_data))
        # Filter for interesting firmware strings (alphanumeric phrases)
        meaningful_strings = [
            s for s in extracted
            if any(c.isalpha() for c in s) and len(s) >= 4
        ]
        result["strings"] = sorted(set(meaningful_strings))

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Static Firmware ELF Triage")
    parser.add_argument("firmware", nargs="?", default=DEFAULT_FIRMWARE, type=Path, help="Path to firmware ELF")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT, type=Path, help="Output JSON path")
    args = parser.parse_args()

    firmware_path = Path(args.firmware).resolve()
    print(f"Analyzing firmware: {firmware_path}")
    result = analyze_firmware(firmware_path)

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Static triage completed successfully -> {output_path}")
    print(f"  Architecture: {result['architecture']}")
    print(f"  Entry Point:  {result['entry_point']}")
    print(f"  Vector Table: {len(result['vector_table'])} vectors detected")
    print(f"  Sections:     {len(result['sections'])} sections")
    print(f"  Symbols:      {result['symbols']['function_count']} functions, stripped={result['symbols']['is_stripped']}")
    print(f"  Strings:      {len(result['strings'])} extracted literals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())