from fastapi.middleware.cors import CORSMiddleware


def setup_CORS(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # oder ["*"] zum Testen
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
