from fastapi import FastAPI

from yakoon.apps.webapi.tools.middleware import setup_CORS
from yakoon.apps.webapi.tools.routes import init_routes

app = FastAPI()


def run_web_api(host: str = "127.0.0.1", port: int = 8000, reload=False):
    """
    http://127.0.0.1:8000/docs
    """
    setup_CORS(app)
    init_routes(app)

    import uvicorn

    uvicorn.run("yakoon.apps.webapi.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    run_web_api()
