from fastapi import FastAPI
from app.api import users, groups, expenses, auth, dept
from app.database import Base, engine

app = FastAPI()
# @app.get("/")
# async def read_root():
#     return {"message": "Hello, World"}


Base.metadata.create_all(bind=engine)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(groups.router, prefix="/groups", tags=["groups"])
app.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(dept.router, prefix="/dept", tags=["dept"])
