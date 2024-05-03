from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from domain.question import question_router
from domain.crawling import ex
from domain.crawling import bs

app = FastAPI()

origins = ["http://localhost:5173",]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(ex.router)
app.include_router(bs.router)

