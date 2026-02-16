# main.py
import os
import uuid
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Se quiser servir arquivos estáticos (HTML/CSS/JS) por aqui:
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")  # [web:69]

# CORS para o seu front (ajuste origens conforme onde hospedar)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # em produção, restrinja isso
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/ogg"}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES


@app.post("/momentos/upload")
async def upload_momentos(files: List[UploadFile] = File(...)):
    saved_files = []

    for file in files:
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=415, detail=f"Tipo não suportado: {file.content_type}")  # [web:68]

        ext = os.path.splitext(file.filename)[1]
        unique_name = f"{uuid.uuid4().hex}{ext}"
        dest_path = os.path.join(UPLOAD_DIR, unique_name)

        try:
            with open(dest_path, "wb") as buffer:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    buffer.write(chunk)
        finally:
            await file.close()

        url_path = f"/uploads/{unique_name}"
        saved_files.append(
            {
                "filename": file.filename,
                "stored_name": unique_name,
                "url": url_path,
                "content_type": file.content_type,
            }
        )

    return {"files": saved_files}


@app.get("/momentos/list")
async def list_momentos():
    items = []
    for name in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, name)
        if not os.path.isfile(path):
            continue

        # tipo simples só pela extensão (para decidir img ou video no front)
        ext = os.path.splitext(name)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".gif"]:
            kind = "image"
        elif ext in [".mp4", ".webm", ".ogg"]:
            kind = "video"
        else:
            continue

        items.append(
            {
                "name": name,
                "url": f"/uploads/{name}",
                "type": kind,
            }
        )

    return {"items": items}


# montar rota estática para os uploads
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")  # [web:69]
