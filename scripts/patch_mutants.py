"""Mutant Generation & Verification Script.

Creates minimal, verified ARM ELF mutants from original.elf for calibration.
Disassembles before and after patching using Capstone and Keystone to ensure
instruction-level validity and structural ELF integrity.
"""

from pathlib import Path
import json
import capstone
import keystone
from elftools.elf.elffile import ELFFile

ROOT_DIR = Path(__file__).resolve().parent.parent
ORIGINAL_ELF = ROOT_DIR / "original.elf"
MUTANTS_DIR = ROOT_DIR / "calib" / "mutants"
MANIFEST_PATH = ROOT_DIR / "calib" / "manifest.json"

MUTANT_SPECS = [
    {
        "mutant_id": "MUTANT_01",
        "filename": "mutant_1_branch_inversion.elf",
        "function": "main",
        "address": 0x80012E0,
        "size": 2,
        "original_asm": "bne #0x80012fa",
        "mutated_asm": "beq.n #0x80012fa",
        "category": "conditional_branch_inversion",
        "description": "Inverts sensor error check in main. Success branch jumps to error logging; error branch attempts to read temperature.",
        "expected_violation": "REQ-02",
        "detection_criteria": "Transmits 'Error' instead of formatted telemetry on valid sensor reads"
    },
    {
        "mutant_id": "MUTANT_02",
        "filename": "mutant_2_timing_delay.elf",
        "function": "main",
        "address": 0x80012F0,
        "size": 4,
        "original_asm": "mov.w r0, #0x7d0",
        "mutated_asm": "mov.w r0, #0",
        "category": "timing_delay_alteration",
        "description": "Sets main loop HAL_Delay duration from 2000 ms to 0 ms, flooding the UART bus without inter-frame delay.",
        "expected_violation": "REQ-01",
        "detection_criteria": "UART transmission rate exceeds 2000 ms period or runs continuously"
    },
    {
        "mutant_id": "MUTANT_03",
        "filename": "mutant_3_humidity_offset.elf",
        "function": "si7021_measure_humidity",
        "address": 0x80013DA,
        "size": 2,
        "original_asm": "subs r0, #6",
        "mutated_asm": "adds r0, #6",
        "category": "calculation_offset_modification",
        "description": "Replaces 'subs r0, #6' with 'adds r0, #6' in Si7021 RH formula, corrupting relative humidity calculation by +12% RH.",
        "expected_violation": "REQ-04",
        "detection_criteria": "Reported relative humidity exceeds physical upper bound (100% RH) or shifts by +12%"
    },
    {
        "mutant_id": "MUTANT_04",
        "filename": "mutant_4_humidity_scale.elf",
        "function": "si7021_measure_humidity",
        "address": 0x80013D4,
        "size": 2,
        "original_asm": "movs r0, #0x7d",
        "mutated_asm": "movs r0, #0",
        "category": "multiplier_scale_zeroing",
        "description": "Zeroes the 125 multiplier in Si7021 RH formula (movs r0, #0), collapsing computed relative humidity to -6%.",
        "expected_violation": "REQ-04",
        "detection_criteria": "Reported humidity is -6%, violating lower physical bound (0% RH)"
    },
    {
        "mutant_id": "MUTANT_05",
        "filename": "mutant_5_i2c_command.elf",
        "function": "si7021_read_previous_temperature",
        "address": 0x80013E2,
        "size": 2,
        "original_asm": "movs r3, #0xe0",
        "mutated_asm": "movs r3, #0xff",
        "category": "i2c_command_corruption",
        "description": "Changes Si7021 temperature read command from 0xE0 to invalid command 0xFF, triggering I2C NACK / sensor transaction failure.",
        "expected_violation": "REQ-02",
        "detection_criteria": "Temperature reading fails (returns 0xFFFF) or triggers error frame"
    }
]


def generate_mutants():
    MUTANTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(ORIGINAL_ELF, "rb") as f:
        orig_bytes = bytearray(f.read())
        f.seek(0)
        orig_elf = ELFFile(f)
        text_sec = orig_elf.get_section_by_name(".text")
        text_addr = text_sec["sh_addr"]
        text_offset = text_sec["sh_offset"]

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    ks = keystone.Ks(keystone.KS_ARCH_ARM, keystone.KS_MODE_THUMB)

    manifest_entries = []

    print(f"Generating {len(MUTANT_SPECS)} verified binary mutants from {ORIGINAL_ELF.name}...")

    for spec in MUTANT_SPECS:
        addr = spec["address"]
        size = spec["size"]
        file_offset = text_offset + (addr - text_addr)

        # 1. Verify original instruction at address
        current_bytes = orig_bytes[file_offset : file_offset + size]
        insns = list(md.disasm(current_bytes, addr))
        assert len(insns) == 1, f"Expected 1 instruction at {hex(addr)}, found {len(insns)}"
        orig_ins = insns[0]

        # 2. Assemble replacement
        rep_enc, count = ks.asm(spec["mutated_asm"], addr)
        rep_bytes = bytes(rep_enc)
        assert len(rep_bytes) == size, f"Replacement size mismatch: {len(rep_bytes)} != {size}"

        # 3. Create mutant binary bytearray
        mutant_bytes = bytearray(orig_bytes)
        mutant_bytes[file_offset : file_offset + size] = rep_bytes

        # 4. Save mutant file
        mutant_path = MUTANTS_DIR / spec["filename"]
        with open(mutant_path, "wb") as f:
            f.write(mutant_bytes)

        # 5. Reopen with pyelftools to verify ELF validity
        with open(mutant_path, "rb") as f:
            mutant_elf = ELFFile(f)
            assert mutant_elf.get_machine_arch() == "ARM", "ELF architecture corrupted"
            mut_text = mutant_elf.get_section_by_name(".text")
            assert mut_text["sh_size"] == text_sec["sh_size"], "Section size changed unexpectedly"
            
            # Disassemble patched instruction from mutant file
            mut_data = mut_text.data()
            mut_ins_bytes = mut_data[addr - text_addr : addr - text_addr + size]
            mut_insns = list(md.disasm(mut_ins_bytes, addr))
            assert len(mut_insns) == 1, "Failed to decode patched instruction"
            mut_ins = mut_insns[0]

        # 6. Verify exact byte diff (must differ ONLY within file_offset .. file_offset + size)
        diff_offsets = [
            i for i in range(len(orig_bytes)) if orig_bytes[i] != mutant_bytes[i]
        ]
        assert len(diff_offsets) > 0, "No bytes were changed in mutant"
        assert all(file_offset <= i < file_offset + size for i in diff_offsets), (
            f"Diff offsets {diff_offsets} contained bytes outside target range [{file_offset}, {file_offset + size})"
        )

        print(f"  [OK] {spec['mutant_id']} ({spec['filename']}):")
        print(f"       Addr 0x{addr:x}: {orig_ins.mnemonic} {orig_ins.op_str} -> {mut_ins.mnemonic} {mut_ins.op_str}")
        print(f"       Bytes: {current_bytes.hex()} -> {rep_bytes.hex()} (diff size: {len(diff_offsets)} bytes)")

        manifest_entries.append({
            "mutant_id": spec["mutant_id"],
            "filename": spec["filename"],
            "function": spec["function"],
            "address": hex(addr),
            "original_bytes": current_bytes.hex(),
            "mutated_bytes": rep_bytes.hex(),
            "original_instruction": f"{orig_ins.mnemonic} {orig_ins.op_str}",
            "mutated_instruction": f"{mut_ins.mnemonic} {mut_ins.op_str}",
            "category": spec["category"],
            "description": spec["description"],
            "expected_violation": spec["expected_violation"],
            "detection_criteria": spec["detection_criteria"]
        })

    # Save manifest
    with open(MANIFEST_PATH, "w") as f:
        json.dump({"mutants": manifest_entries}, f, indent=2)

    print(f"\nManifest successfully written to {MANIFEST_PATH.relative_to(ROOT_DIR)}")
    return manifest_entries


if __name__ == "__main__":
    generate_mutants()
