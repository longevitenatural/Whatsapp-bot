import asyncio
import httpx

SHEET_ID = "1Cg1SBYIq2kiPYI-D8mKKlvt1dLC8Zz045jIWpK3Ho0k"

async def test():
    url = "https://docs.google.com/spreadsheets/d/" + SHEET_ID + "/gviz/tq?tqx=out:csv&sheet=Catalogo"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        print(r.text[:800])

asyncio.run(test())
