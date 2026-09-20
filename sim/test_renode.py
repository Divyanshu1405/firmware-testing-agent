from pathlib import Path
from renode_backend import run


firmware = Path(__file__).parent.parent / "firmware" / "inputs" / "firmware2.elf"

result = run(firmware)

print("Return code:", result["returncode"])
print("STDOUT:")
print(result["stdout"])
print("STDERR:")
print(result["stderr"])