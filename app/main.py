import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.api.radio import radio_search
from app.models import RadioModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=list[RadioModel])
def get_station(name: str = Query(default="BBC Radio", description="The station name")):
    return radio_search(name=name,name_exact=True)


@app.get("/stream")
async def stream_audio():
    stream_url = "http://151.80.56.90:8090/bbc_radio_one_dance.aac"

    client = httpx.AsyncClient()
    req = client.build_request("GET", stream_url)
    resp = await client.send(req, stream=True)

    if resp.status_code != 200:
        await client.aclose()
        raise HTTPException(status_code=502, detail="Не удалось подключиться к потоку")

    async def audio_generator():
        try:
            async for chunk in resp.aiter_bytes(chunk_size=8192):
                yield chunk
        finally:
            await resp.aclose()
            await client.aclose()

    return StreamingResponse(audio_generator(), media_type="audio/aac")