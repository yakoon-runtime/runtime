from fastapi import APIRouter
from pydantic import BaseModel
from y5n.apps.webapi.sessions.handler import handle_input

router = APIRouter()


class CommandRequest(BaseModel):
    session_id: str
    input: str


@router.post("/run")
async def run_command(data: CommandRequest):
    result = await handle_input(data.session_id, data.input)
    return {"output": result}
