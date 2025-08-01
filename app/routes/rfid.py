from fastapi import APIRouter
from rfid import RC522Reader

router = APIRouter()
rfid_reader = RC522Reader(cs_pin=7)

@router.get("/rfid/read")
def read_rfid():
    uid = rfid_reader.get_latest_uid()
    if uid:
        return {"uid": uid}
    else:
        return {"status": "No card detected"}