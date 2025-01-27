import os
import uuid
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    video_dir: str = "videos"
    allowed_extensions: set = {"mp4", "avi", "mov"}
    max_file_size: int = 50 * 1024 * 1024  # 50 MB

settings = Settings()

app = FastAPI()

if not os.path.exists(settings.video_dir):
    os.makedirs(settings.video_dir)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def validate_file(file: UploadFile):
    file_extension = file.filename.split(".")[-1]
    if file_extension not in settings.allowed_extensions:
        raise HTTPException(status_code=400, detail="Formato de arquivo não suportado.")
    file.file.seek(0, 2)  # Move o cursor para o final do arquivo e verifica o tamanho
    if file.file.tell() > settings.max_file_size:  # Compara o tamanho do arquivo
        raise HTTPException(status_code=400, detail="Arquivo muito grande.")
    file.file.seek(0)  # Retorna para o início do arquivo para a leitura posterior

@app.post("/upload/")
async def upload_video(file: UploadFile = File(...)):
    validate_file(file)
    unique_filename = f"{uuid.uuid4()}.{file.filename.split('.')[-1]}"
    file_path = os.path.join(settings.video_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    logger.info(f"Video uploaded: {file.filename} as {unique_filename}")
    return {"filename": unique_filename, "url": f"/videos/{unique_filename}"}

@app.get("/videos/{video_filename}")
async def get_video(video_filename: str):
    file_path = os.path.join(settings.video_dir, video_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Vídeo não encontrado.")
    
    return FileResponse(file_path, media_type="video/mp4", filename=video_filename)

@app.get("/videos/{video_filename}/download")
async def download_video(video_filename: str):
    file_path = os.path.join(settings.video_dir, video_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Vídeo não encontrado.")
    
    return FileResponse(file_path, media_type="application/octet-stream", filename=video_filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



#env\Scripts\activate