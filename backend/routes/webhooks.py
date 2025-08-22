from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.form()
    print("Received WhatsApp message:", data)
    return {"status": "success"}
