# Remote Runtime per SSH-Tunnel

## Szenario

Auf einem Server (z.B. Hetzner) läuft eine Yakoon Runtime, gebunden an `127.0.0.1` (nicht öffentlich erreichbar). Von deinem lokalen Rechner aus verbindest du Texture über einen SSH-Tunnel.

## Tunnel aufbauen

```bash
ssh -L 9101:localhost:9101 office
```

- `-L 9101:localhost:9101` – leitet localhost:9101 deines Rechners durch den Tunnel zu localhost:9101 des Servers
- `office` – SSH-Host (wie in `~/.ssh/config` konfiguriert)

Der Tunnel bleibt offen, solange die SSH-Sitzung läuft. Für den Hintergrund:

```bash
ssh -f -N -L 9101:localhost:9101 office
```

- `-f` – fork in den Hintergrund
- `-N` – keine Kommandoausführung, nur Port-Forwarding

## Texture verbinden

Sobald der Tunnel steht, verbindest du Texture wie gewohnt:

```
/connect ws://localhost:9101
```

oder via `texture.yaml`:

```yaml
runtimes:
  - name: office
    url: ws://localhost:9101
    autoconnect: true
```

Texture glaubt, sie spreche mit einer lokalen Runtime – der gesamte Traffic geht aber verschlüsselt durch den SSH-Tunnel zum Server.

## WebSocket über SSH

WebSocket ist TCP mit einem HTTP-Upgrade. SSH tunnelt TCP transparent. Es gibt keinen Protokoll-Konflikt – weder Texture noch die Runtime merken etwas vom Tunnel.

## Mehrere Runtimes

```bash
# Runtime A (Port 9101)
ssh -L 9101:localhost:9101 office

# Runtime B (Port 9102)
ssh -L 9102:localhost:9102 office
```

Jeder Tunnel bekommt einen eigenen lokalen Port. Texture verbindet zu `ws://localhost:9101` und `ws://localhost:9102`.
