from fastapi import FastAPI
from src.utils.db import Base, engine

app=FastAPI()


Base.metadata.create_all(engine)


