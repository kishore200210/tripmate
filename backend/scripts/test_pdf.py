import asyncio
from app.modules.pdf.tasks import _generate_itinerary_pdf_async

async def main():
    try:
        path = await _generate_itinerary_pdf_async("9b64e398-bba1-491d-a78d-364ebc4a05e4")
        print("Success:", path)
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
