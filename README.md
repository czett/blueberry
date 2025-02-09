![banner where?](https://github.com/czett/blueberry/blob/main/assets/banner2.png)

# Blueberry

Blueberry ist ein sprachgesteuertes System, das Sprachbefehle erkennt, darauf reagiert und Antworten generiert. Es nutzt Ollama und das llama3.2:1b-Modell für KI-basierte Antworten sowie Speech-to-Text für die Spracherkennung.

## Funktionen
- Erkennung von Sprachbefehlen über Mikrofon
- Ausgabe von Antworten mit Text-to-Speech
- Verarbeitung von Folgeanfragen
- aktuelles Wetter ohne genaue Filter (Temperatur und Regenwahrscheinlichkeit)
- Timer stellen und deren Klingelton (klingeln im Ruhezustand und in aktueller Ausgabe)
- KI-gestützte Antwortgenerierung mit **Ollama** und dem **llama3.2:1b-Modell**

## Geplant/in Entwicklung
- Wetter (spezifisch heute/morgen und Ort feststellen; bisher nur sporadisch)
- To-Do Liste
- AI unterbrechen (erstmal ausgesetzt, da brachial zu langsam)

## Installation
1. Klone das Repository.
2. Installiere die benötigten Abhängigkeiten. (`pip install -r requirements.txt`)
3. Installiere ollama und das gewünschnte KI-Modell
4. Stelle sicher, dass die Zugangsdaten in der Datei `credentials.yml` vorhanden sind.

## Nutzung
Starte das Skript und sprich nach dem Startsound Befehle, auf die Blueberry reagiert. Das System nutzt das llama3.2:1b-Modell über Ollama, um Antworten zu generieren.
