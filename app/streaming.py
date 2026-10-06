import httpx

from app.models import RadioModel
from app.radio import radio_search_by_uuid


async def get_station_by_uuid(
    uuid: str,
    client: httpx.AsyncClient,
) -> str | None:
    stations = await radio_search_by_uuid(uuid, client)

    return stations[0].stream_url if stations else None