from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parent.parent
BOARD = "platforms/boards/stm32f4_discovery-kit.repl"
SENSOR = REPO_ROOT / "sim" / "si7021.repl"


def run(firmware: Path) -> dict:
    firmware = firmware.resolve()
    uart_log = REPO_ROOT / "logs" / "uart.log"

    command = [
        "renode",
        "--console",
        "--disable-xwt",
        "--execute", 'mach create "test"',
        "--execute",
        f"machine LoadPlatformDescription @{BOARD}",
        "--execute",
        f"machine LoadPlatformDescription @{SENSOR}",
        "--execute",
        f"sysbus LoadELF @{firmware}",
        "--execute",
        f"usart2 CreateFileBackend @{uart_log}",
        "--execute",
        "start",
        "--execute",
        "sleep 1",
        "--execute",
        "q",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30,
    )

    return {
        "firmware": str(firmware),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "uart_log": uart_log.read_text(errors="replace")
        if uart_log.exists()
        else "",
    }