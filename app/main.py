import re
from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from urllib.parse import quote, urljoin, urlparse

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from app.models import RadioModel
from app.radio import get_station_by_name
from app.streaming import get_station_by_uuid


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(10.0, read=30.0),
    ) as client:
        app.state.http_client = client
        yield


app = FastAPI(
    title="Global Radio API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_http_client() -> httpx.AsyncClient:
    return app.state.http_client


HttpClientDep = Annotated[
    httpx.AsyncClient,
    Depends(get_http_client),
]

HLS_CONTENT_TYPE = "application/vnd.apple.mpegurl"


def is_hls(content_type: str, url: str) -> bool:
    return "mpegurl" in content_type.lower() or urlparse(url).path.endswith(".m3u8")


def rewrite_playlist(text: str, base_url: str, proxy_base: str) -> str:
    def proxy(link: str) -> str:
        absolute = urljoin(base_url, link)
        return f"{proxy_base}/hls?url={quote(absolute, safe='')}"

    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append(line)
        elif stripped.startswith("#"):
            lines.append(
                re.sub(r'URI="([^"]+)"', lambda m: f'URI="{proxy(m.group(1))}"', line)
            )
        else:
            lines.append(proxy(stripped))
    return "\n".join(lines) + "\n"


async def proxy_url(request: Request, client: httpx.AsyncClient, url: str):
    try:
        req = client.build_request("GET", url)
        resp = await client.send(req, stream=True)
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка соединения с радиосервером: {e}",
        )

    if resp.status_code != 200:
        await resp.aclose()
        raise HTTPException(
            status_code=502,
            detail=f"Радиосервер вернул статус {resp.status_code}",
        )

    content_type = resp.headers.get("content-type", "audio/aac")

    if is_hls(content_type, str(resp.url)):
        body = await resp.aread()
        await resp.aclose()
        text = rewrite_playlist(
            body.decode("utf-8", errors="replace"),
            base_url=str(resp.url),
            proxy_base=str(request.base_url).rstrip("/"),
        )
        return Response(content=text, media_type=HLS_CONTENT_TYPE)

    async def audio_generator() -> AsyncGenerator[bytes, None]:
        try:
            async for chunk in resp.aiter_bytes(chunk_size=8192):
                yield chunk
        finally:
            await resp.aclose()

    return StreamingResponse(audio_generator(), media_type=content_type)


@app.get("/", response_model=list[RadioModel])
def get_stations(
    name: Annotated[str, Query(description="Название радиостанции")] = "BBC Radio",
):
    return get_station_by_name(name)


@app.get("/stream")
async def stream_audio(
    request: Request,
    client: HttpClientDep,
    uuid: Annotated[str, Query(description="UUID радиостанции")],
):
    stream_url = await get_station_by_uuid(uuid=uuid, client=client)

    if not stream_url:
        raise HTTPException(status_code=404, detail="Поток радиостанции не найден")

    return await proxy_url(request, client, stream_url)


@app.get("/hls")
async def hls_proxy(
    request: Request,
    client: HttpClientDep,
    url: Annotated[str, Query(description="Абсолютный URL плейлиста или сегмента")],
):
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Некорректный URL")

    return await proxy_url(request, client, url)