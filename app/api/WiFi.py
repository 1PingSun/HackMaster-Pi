from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, List
from .mylib.WeakPasswordGenerater.main import PasswordGenerator
import os

router = APIRouter(
    prefix="/WiFi",
    tags=["WiFi"]
)

templates = Jinja2Templates(directory="templates")

# 定義請求模型
class WordlistRequest(BaseModel):
    output_filename: str
    info_data: Dict[str, List[str]]

@router.get("/wordlist-generator", response_class=HTMLResponse)
def read_wordlist_generator(request: Request):
    return templates.TemplateResponse(
        "WiFi/wordlist-generator.html",
        {"request": request, "message": "Wordlist Generator"}
    )

@router.post("/wordlist-generator")
async def generate_wordlist(request: WordlistRequest):
    try:
        # 確保檔案名稱合法
        filename = request.output_filename
        if not filename.endswith('.txt'):
            filename += '.txt'
            
        # 建立生成器實例
        generator = PasswordGenerator(output_file=f"static/wordlists/{filename}")
        
        # 從請求中取得資料
        info_data = request.info_data
        
        # 生成密碼字典
        generator.generate(
            DATE=info_data.get('date', []),
            TEL=info_data.get('tel', []),
            NAME=info_data.get('name', []),
            ID=info_data.get('ID', []),
            SSID=info_data.get('SSID', [''])[0] if info_data.get('SSID') else ''
        )
        
        # 讀取生成的檔案以取得樣本和行數
        file_path = f"static/wordlists/{filename}"
        with open(file_path, 'r') as f:
            lines = f.readlines()
            total_count = len(lines)
            sample = ''.join(lines[:10]) # 只回傳前10行作為樣本
            
        return JSONResponse({
            "success": True,
            "filename": filename,
            "count": total_count,
            "sample": sample,
            "download_link": f"/static/wordlists/{filename}"
        })
        
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })