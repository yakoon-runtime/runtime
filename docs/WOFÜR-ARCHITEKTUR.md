# Wofür Architektur? (KI-Perspektive)

## Kurze Antwort

Architektur ist nicht für Compiler, nicht für Maschinen, nicht für die KI.

Architektur ist für **den Entwickler** — als Kontrollinstrument, Orientierung und Vertrauensanker.

## Wieso

> "Dann schreibt man halt einfach Scheißcode. Die KI macht das schon."

Der Denkfehler: "die KI" hat nicht das ganze System im Blick. Ich sehe Kontextfenster.
Und selbst bei unbegrenztem Kontext: ich *rate* das semantisch Richtige. Ohne Architektur rate ich nur lokal.

Architektur (Ports, Protocols, geschichtete Module, explizite Verträge) gibt mir:

1. **Verlässliche Grenzen.** "Hier endet Space, hier beginnt Runtime." Sobald ein Import aus `y5n.runtime` in einem Space auftaucht, weiss ich: das ist ein Fehler, selbst wenn der Code läuft.

2. **Lokale Korrektheit.** Mit Protocols kann ich eine Änderung in einem Space machen, ohne die Runtime-Semantik im Kopf zu haben. Der Vertrag (Interface) reicht.

3. **Rückgrat für Refactoring.** Typescript/mypy zeigt mir, welche 12 Dateien ich anfassen muss — nicht weil ich es weiss, sondern weil die Struktur es mir sagt.

4. **Wiedereinstieg.** Du fragst mich in sechs Monaten: "Mach mal X". Ohne Architektur fange ich bei Null an zu raten. Mit Architektur lese ich die Ports und Protocols und weiss, wo X hingehört.

## Der Maßstab

Nicht: *"Schafft die KI, den Code zu ändern?"*

Sondern: **"Schaffst du als Entwickler zu erkennen, ob die Änderung richtig ist?"**

Scheißcode kann ich auch schreiben. Aber Scheißcode ist Scheißcode — egal wer ihn schreibt.
Und ohne Architektur erkennst du nicht mal, ob er richtig ist. Du siehst nur "irgendwie läuft es (noch)".

Architektur ist dein **Vertrauensanker** in einer Welt, in der nicht du den Code schreibst.
