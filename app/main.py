from fastapi import FastAPI
from app.api import users, groups, expenses
from app.database import Base, SessionLocal, engine
app = FastAPI()
# @app.get("/")
# async def read_root():
#     return {"message": "Hello, World"}


Base.metadata.create_all(bind=engine)




app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(groups.router, prefix="/groups", tags=["groups"])
app.include_router(expenses.router, prefix="/expenses", tags=["expenses"])

