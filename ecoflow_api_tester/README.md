# EcoFlow API Tester

Lokale testpagina om EcoFlow Cloud API-connectiviteit los van Home Assistant te controleren.

Start:

```bash
cd tools/ecoflow_api_tester
python3 server.py
```

Open daarna:

```text
http://127.0.0.1:8765
```

Tests:

- device-list ophalen
- quota/all voor een gekozen serienummer
- selected quota's testen
- ruwe EcoFlow response en signature-variant bekijken

De secret key wordt alleen in het lokale Python-proces gebruikt voor signing.
