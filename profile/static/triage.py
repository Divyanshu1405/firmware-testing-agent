from pathlib import Path
from elftools.elf.elffile import ELFFile


def analyze_firmware(firmware_path):
    path = Path(firmware_path)

    with open(path, "rb") as f:
        elf = ELFFile(f)

        result = {
            "file": path.name,
            "format": "ELF",
            "architecture": elf.get_machine_arch(),
            "entry_point": hex(elf.header["e_entry"]),
            "sections": [],
        }

        for section in elf.iter_sections():
            result["sections"].append({
                "name": section.name,
                "address": hex(section["sh_addr"]),
                "size": section["sh_size"],
            })

    return result
    return result


if __name__ == "__main__":
    import sys
    import json

result = analyze_firmware(sys.argv[1])

with open("profile/static/static.json", "w") as f:
    json.dump(result, f, indent=2)

print("static.json created successfully")