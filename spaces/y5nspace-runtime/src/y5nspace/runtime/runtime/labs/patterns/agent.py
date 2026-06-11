from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnCallLLM
from y5n.llm.agents import Agent

SYSTEM_PROMPT = """Du bist ein Assistent für {domain}.

Antworte in einem der folgenden JSON-Formate:

1. Kommando ausführen:
  {{"command": "ls", "args": ["-la", "/tmp"]}}

2. Fertig:
  {{"done": true, "result": "Deine Antwort"}}

3. Fehler:
  {{"error": "Begründung"}}"""


async def run(space: NodeSpace):

    request = " ".join(space.request.args())
    if not request:
        yield out_text("Usage: agent <frage>")
        return

    llm: OnCallLLM = space.ports.get(OnCallLLM)

    agent = Agent(
        llm=llm,
        prompt=SYSTEM_PROMPT,
        channel="agent-demo",
        max_steps=5,
    )

    yield agent.run(
        request=request,
        context={"domain": "Demo"},
    )

    yield out_text(agent.result or "?")
