# Lokale Domänenmodelle und LoRA-Finetuning

## Ausgangspunkt

Während der Entwicklung des ersten `os`-Space entstand die Frage, ob spezialisierte lokale Modelle langfristig eine Alternative zu großen zentralen Cloud-Modellen sein können.

Die Beobachtung war überraschend:

Der größte Fortschritt entstand nicht durch ein größeres Modell, sondern durch besseren Kontext.

Beispiele:

- aktueller Benutzer
- Home-Verzeichnis
- aktuelles Arbeitsverzeichnis
- Betriebssysteminformationen

Sobald diese Informationen verfügbar waren, verbesserte sich das Verhalten des Modells deutlich.

Daraus entstand die Vermutung:

> Für viele Unternehmensdomänen ist Kontext wichtiger als Weltwissen.

## Domänen statt Universalmodelle

Die aktuelle KI-Landschaft orientiert sich häufig an großen universellen Modellen.

Das zugrunde liegende Paradigma lautet:

```
Eine KI
für alles
```

Yakoon verfolgt potenziell einen anderen Ansatz:

```
Viele spezialisierte Domänen
mit jeweils eigener KI
```

Beispiele:

- OS
- Mail
- Kalender
- CRM
- Dokumente
- Wissensmanagement

Jede Domäne besitzt:

- eigenen Kontext
- eigene Regeln
- eigene Werkzeuge
- eigene Berechtigungen

Dadurch reduziert sich der benötigte Wissensraum erheblich.

## Warum kleine Modelle interessant sind

Der OS-Space benötigt beispielsweise kein Wissen über:

- Geschichte
- Medizin
- Politik
- Literatur

Er benötigt lediglich Wissen über:

- Dateien
- Prozesse
- Benutzer
- Netzwerk
- Hardware
- Linux-Kommandos

Die zu modellierende Welt wird dadurch sehr klein.

Die zentrale Frage lautet deshalb:

> Wie klein darf ein Modell werden, wenn die Welt klein genug ist?

## Was ist LoRA?

LoRA (Low-Rank Adaptation) ermöglicht es, ein bestehendes Modell anzupassen, ohne das gesamte Modell neu zu trainieren.

Anstatt Milliarden von Gewichten zu verändern, werden lediglich kleine Adapter trainiert.

Vereinfacht:

```
Basismodell
+
LoRA
=
spezialisierte KI
```

Beispiele:

```
Mistral
+
OS-LoRA
=
OS-Agent
```

```
Mistral
+
Mail-LoRA
=
Mail-Agent
```

## Warum LoRA interessant sein könnte

Ein OS-Modell müsste kein neues Weltwissen lernen.

Es müsste lediglich lernen:

- OS-Anfragen zu erkennen
- passende Strategien zu wählen
- Kommandos korrekt einzusetzen
- Ergebnisse zu interpretieren

LoRA eignet sich besonders gut für solche Verhaltensanpassungen.

## Hardware

Für LoRA-Finetuning sind keine GPU-Cluster notwendig.

Bereits aktuelle Workstations oder leistungsfähige Consumer-Hardware können ausreichend sein.

Beispielsweise:

- Ryzen-Systeme
- aktuelle Gaming-PCs
- Workstations mit dedizierter GPU

Die Einstiegshürde ist deutlich geringer als bei vollständigem Modelltraining.

## Wichtige Erkenntnis

Aktuell gibt es keinen Grund, bereits Modelle zu trainieren.

Der nächste Schritt sollte sein:

1. Verschiedene Open-Source-Modelle testen
2. Dieselbe Domäne verwenden
3. Verhalten vergleichen

Beispielsweise:

- Mistral Small
- Qwen
- Gemma
- Llama

Erst wenn systematische Schwächen sichtbar werden, sollte über LoRA nachgedacht werden.

## Offene Forschungsfrage

Die Experimente mit dem OS-Space legen eine interessante Vermutung nahe:

> Intelligenz entsteht möglicherweise nicht primär aus der Größe eines Modells.

Sondern aus der Kombination von:

- Modell
- Kontext
- Werkzeugen
- Domänenwissen

Falls diese Vermutung zutrifft, könnten lokale spezialisierte Modelle langfristig eine realistische Alternative zu zentralisierten Cloud-Agenten darstellen.

Nicht nur aus Kostengründen, sondern auch hinsichtlich:

- Datenschutz
- Energieverbrauch
- Kontrolle
- Nachvollziehbarkeit
- lokaler Wertschöpfung

Die entscheidende Frage lautet dann nicht mehr:

> Wie groß muss ein Modell sein?

Sondern:

> Wie klein kann die Welt sein, die es verstehen muss?
