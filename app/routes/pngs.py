from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import os, time

router = APIRouter()

@router.get("/web", response_class=HTMLResponse)
async def list_images():
    image_folder = os.path.join(os.path.dirname(__file__), "..", "..", "tests")
    files = [f for f in os.listdir(image_folder) if f.endswith(".png")]
    links = [f'<li><a href="/pngs/view/{file}">{file}</a></li>' for file in files]
    return f"<h1>PNG Files</h1><ul>{''.join(links)}</ul>"



@router.get("/web/view/{filename}", response_class=HTMLResponse)
async def view_image(filename: str):
    timestamp = int(time.time())
    return f"""
    <h1>{filename}</h1>
    <img src="/pngs-static/{filename}?v={timestamp}" alt="{filename}" style="max-width:100%;"/>
    <br><a href="/pngs">Back to list</a>
    """
