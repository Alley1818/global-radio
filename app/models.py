from typing import Optional
from pydantic import BaseModel

class RadioModel(BaseModel):
    changeuuid: Optional[str] = None
    stationuuid: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    homepage: Optional[str] = None
    tags: Optional[str] = None
    country: Optional[str] = None
    countrycode: Optional[str] = None
    language: Optional[str] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = None


"""
class Radio(BaseModel):
    changeuuid: str
    stationuuid: str
    name: str
    url: str
    homepage: str
    tags: str
    country: str
    countrycode: str
    language: str
    codec: str
    bitrate: int
"""