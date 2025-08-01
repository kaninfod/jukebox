from fastapi import APIRouter, Body
from app.ili9488 import ILI9488

router = APIRouter()
display = ILI9488()

@router.post("/display/text")
def display_text(text: str = Body(..., embed=True)):
    display.display_image(text)
    return {"status": "Text displayed"}