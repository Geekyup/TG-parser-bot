from fastapi import FastAPI, Form, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import yt_dlp
import os
import shutil
import tempfile
from pathlib import Path

app = FastAPI()
templates = Jinja2Templates(directory="templates")
# Создайте папку templates для index.html

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Video Downloader</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; max-width: 500px; margin: 50px auto; padding: 20px; }
        input[type=url] { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #007bff; color: white; border: none; font-size: 16px; cursor: pointer; }
        button:hover { background: #0056b3; }
        #status { margin-top: 20px; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        a { display: block; margin-top: 10px; color: #007bff; text-decoration: none; }
    </style>
</head>
<body>
    <h1>Скачай видео по ссылке</h1>
    <p>Вставьте URL (Rutube, VK, TikTok и т.д.)</p>
    <form id="form">
        <input type="url" id="url" name="url" placeholder="https://example.com/video" required>
        <button type="submit">Скачать</button>
    </form>
    <div id="status"></div>

    <script>
        document.getElementById('form').onsubmit = async (e) => {
            e.preventDefault();
            const url = document.getElementById('url').value;
            const status = document.getElementById('status');
            status.innerHTML = 'Обрабатываем...';
            
            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    body: new URLSearchParams({url: url}),
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
                });
                if (response.ok) {
                    const title = response.headers.get('Content-Disposition')?.match(/filename="(.+)"/)?.[1] || 'video.mp4';
                    const blob = await response.blob();
                    const a = document.createElement('a');
                    a.href = URL.createObjectURL(blob);
                    a.download = title;
                    a.click();
                    status.innerHTML = 'Скачано!';
                } else {
                    status.innerHTML = 'Ошибка: ' + response.statusText;
                }
            } catch (err) {
                status.innerHTML = 'Ошибка: ' + err.message;
            }
        };
    </script>
</body>
</html>
    """

@app.post("/download")
async def download(url: str = Form(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',  # Лучшее MP4
            'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                def iter_file():
                    with open(filename, 'rb') as f:
                        shutil.copyfileobj(f, yield)  # Генератор для стрима
                
                headers = {'Content-Disposition': f'attachment; filename="{os.path.basename(filename)}"'}
                return StreamingResponse(iter_file(), media_type='video/mp4', headers=headers)
    
    return {"error": "Файл не найден"}