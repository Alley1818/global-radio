import httpx

from pydantic import TypeAdapter
from pyradios import RadioBrowser

from app.models import RadioModel


rb = RadioBrowser()

MIRRORS = [
    "https://de1.api.radio-browser.info",
    "https://nl1.api.radio-browser.info",
    "https://at1.api.radio-browser.info",
]


radio_list_adapter = TypeAdapter(
    list[RadioModel]
)


def get_station_by_name(
    name: str,
) -> list[RadioModel]:

    result = rb.search(
        name=name,
        hidebroken=True,
        order="clickcount",
        reverse=True,
        limit=100,
    )

    filtered: list[dict] = []
    seen: set[str] = set()

    for station in result:
        if station.get("lastcheckok") != 1:
            continue

        stream = station.get("url_resolved") or station.get("url")
        if not stream or stream in seen:   # без URL и дубликаты
            continue

        if station.get("hls") == 1:
             continue

        seen.add(stream)
        filtered.append(station)

    return radio_list_adapter.validate_python(filtered)


async def radio_search_by_uuid(
    uuid: str,
    client: httpx.AsyncClient,
) -> list[RadioModel]:

    for mirror in MIRRORS:
        try:
            response = await client.get(
                f"{mirror}/json/stations/byuuid/{uuid}",
                timeout=httpx.Timeout(
                    3.0,
                    connect=2.0,
                ),
            )

            if response.status_code == 200:
                return radio_list_adapter.validate_python(
                    response.json()
                )

        except httpx.RequestError:
            continue

    return []