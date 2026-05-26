from y5n.apps.webapi.endpoints import command
from y5n.apps.webapi.socket.handler import router as ws_router


# Include routes
def init_routes(app):
    app.include_router(command.router, prefix="/command")
    app.include_router(ws_router)
