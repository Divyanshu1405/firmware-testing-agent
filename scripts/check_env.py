import shutil
import sys

for tool in ["python"]:
    print(f"{tool}: {shutil.which(tool) or sys.executable}")

for tool in ["renode", "wokwi-cli", "ollama"]:
    print(f"{tool}: {shutil.which(tool) or 'not found'}")
