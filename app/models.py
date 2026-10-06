from pydantic import BaseModel, computed_field


class RadioModel(BaseModel):
    stationuuid: str
    name: str
    url: str
    url_resolved: str | None = None
    homepage: str | None = None
    favicon: str | None = None
    tags: str | None = None
    country: str | None = None
    countrycode: str | None = None
    language: str | None = None
    codec: str | None = None
    bitrate: int | None = None

    @computed_field
    @property
    def stream_url(self) -> str:
        return self.url_resolved or self.url