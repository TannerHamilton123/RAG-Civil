from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/number/{number}")
async def get_number(number: int):
    return {"message": f"The number is {number}"}