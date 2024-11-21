![Banner](https://github.com/nih23/Chatbot-Hackathon/blob/main/res/Banner.jpg?raw=true)

# Chatbot-Hackathon

Beim Skat-Hackathon entwickelst du in einem Team eine KI, die in der Lage ist, Skat-Karten auf der Hand und auf dem Tisch zu erkennen – und das alles in Echtzeit! Mit Hilfe modernster Objekterkennungsmodelle wie YOLO, SAM2 und GroundingDino erfasst deine KI die Spielkarten und entscheidet, welche Karte als nächstes gespielt werden soll. Mithilfe von leistungsstarken Large Language Models (LLMs), darunter selbst gehostete Open-Source-Modelle, wird deine KI auch die optimale Spielstrategie entwickeln.
Am Ende des Hackathons treten die besten KI-Systeme gegeneinander an – und du hast die Chance auf tolle Preise!

# Getting started
Das Python Paket kann mit folgendem Befehl installiert werden:
```bash
git clone https://github.com/nih23/sisax-hackathon
cd sisax-hackathon
pip install -e .
```

Im `demo_notebook.ipynv` wird Objekterkennung und Interaktion mit einem LLM demonstriert. Es ist zu beachten, dass die entsprechende Keys, Hosts, Ports, etc. in der .env zu spezifizieren sind. Aktuell werden folgende Angaben benötigt:

```bash
OBJECT_DETECTION_HOST=http://...:8000
OLLAMA_HOST=http://...
OLLAMA_PORT=11434
OPENAI_API_KEY=sk-proj-..
```

Die Namen der Hosts und API Keys werden am Anfang des Hackathons mitgeteilt.

# Next steps
Ihr könnt das vorliegende Python Paket um weitere Funktionalitän erweitern. Beispielsweise sind folgendes **Features** sinnvoll:
- simples WebUI mit [Flask](https://github.com/pallets/flask) oder [gradio](https://github.com/gradio-app/gradio)
- Auslesen der Webcam per [opencv](https://github.com/opencv/opencv-python)

# Mögliche Bibliotheken und Tools
Die nachfolge Auflisting ist eher als Inspiration gedacht. Es gibt eine große Menge an open-source Tools für verschiedene Aufgaben. Teils gibt es schon Ansätze wie lang-segment-anything oder GPT4o, die ohne fine-tuning (d.h. Training auf GPU) zur Erkennung von Spielkarten verwendet werden können. Fine-tuning von YoloV11 mit `Ultralytics` oder dem neuesten Ansatz `GLEE` könnte jedoch eine deutlich höhere Genauigkeit versprechen.

- Layout-Analyse
  - [unstructured](https://github.com/Unstructured-IO/unstructured)
  - [LayoutReader](https://github.com/ppaanngggg/layoutreader?tab=readme-ov-file)
- Objekterkennung
  - [ultralytics](https://github.com/ultralytics) (fine-tuning notwendig)
  - [Glee](https://github.com/FoundationVision/GLEE) (fine-tuning notwendig)
  - [Lang-Segment-Anything](https://github.com/luca-medeiros/lang-segment-anything)  
