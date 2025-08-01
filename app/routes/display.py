from fastapi import APIRouter, Body, Depends

router = APIRouter()

# Import the display instance from main instead of creating a new one
def get_display():
    from app.main import display
    return display

@router.post("/display/text")
def display_text(text: str = Body(..., embed=True), display_instance = Depends(get_display)):
    display_instance.display_image(text)
    return {"status": "Text displayed"}

@router.post("/display/brightness")
def set_brightness(brightness: int = Body(..., embed=True), display_instance = Depends(get_display)):
    if brightness < 0 or brightness > 100:
        return {"status": "Error", "message": "Brightness must be between 0 and 100"}
    display_instance.set_brightness(brightness)
    return {"status": "Brightness set", "brightness": brightness}