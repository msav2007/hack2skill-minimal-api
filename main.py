from fastapi import FastAPI

app = FastAPI(title="Hack2Skill Minimal API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Hack2Skill submission API"}


@app.get("/ping")
def ping() -> dict[str, str]:
    return {"status": "ok"}
