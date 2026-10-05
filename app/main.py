from fastapi import FastAPI
from fastapi.params import Query

from app.api.radio import radio_search
from app.models import RadioModel

app = FastAPI()


@app.get("/", response_model=list[RadioModel])
def get_station(name: str = Query(default="BBC Radio", description="The station name")):
    return radio_search()

