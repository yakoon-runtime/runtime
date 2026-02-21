const API_URL = "http://localhost:8000/command/run"; // Yakoon WebAPI

let sessionId = localStorage.getItem("yakoonSessionId");

if (!sessionId) {
  sessionId = crypto.randomUUID();
  localStorage.setItem("yakoonSessionId", sessionId);
}

export async function sendCommand(input: string): Promise<string> {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      input,
    }),
  });

  if (!response.ok) {
    return `Fehler: ${response.status}`;
  }

  const data = await response.json();
  return data.output ?? "(kein Output)";
}
