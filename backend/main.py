from pathlib import Path
from fastapi import FastAPI, File, UploadFile

app = FastAPI(title="PS3 Firmware Testing Agent")
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "firmware" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/upload")
async def upload_firmware(file: UploadFile = File(...)) -> dict:
    destination = UPLOAD_DIR / Path(file.filename or "firmware.bin").name
    data = await file.read()
    destination.write_bytes(data)
    return {"filename": destination.name, "size": len(data)}
