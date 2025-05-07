from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from api import WiFi, BLE, RFID
import os

app = FastAPI(
    title="HackMaster Pi",
    description="An open source IoT Hacker Tool by using Raspberry Pi Zero W 2",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "favicon.ico")
    return FileResponse(favicon_path)

app.include_router(BLE.router)
app.include_router(WiFi.router)
app.include_router(RFID.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=4000)