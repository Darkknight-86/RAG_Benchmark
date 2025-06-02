# UI Micro-service
_Graphical entry-point for humans_

---

## 🎨 Responsibilities
* Provide an optional desktop / web GUI that calls the API Gateway REST endpoints.
* Display LLM answers, document sources and metrics dashboard iframe.
* Offer simple CSV export button (downloads Gateway CSVs).

Two reference front-ends are included:
1. **Tkinter GUI** – lightweight desktop window (`src/rag/tkinter_gui_option.py`).
2. **Flet GUI** – web / native hybrid app (`src/rag/flet_gui_option.py`).

Both talk to `http://localhost:8000` by default.

## 🛠️ Tech Stack
| Variant | Library |
|---------|---------|
| Desktop | `tkinter` (stdlib) |
| Web     | `flet` (Flutter-style Python UI) |

## 🗂️ Layout
```
UI/
 ├── Dockerfile            # (future) – run flet host
 ├── pyproject.toml        # currently empty, add deps if you extend UI
 └── src/rag/
      ├── tkinter_gui_option.py
      └── flet_gui_option.py
```

## 🚀 Running (dev)
### Tkinter
```bash
python src/rag/tkinter_gui_option.py
```
### Flet (web)
```bash
pip install flet   # local only, not yet in pyproject
python src/rag/flet_gui_option.py
# open http://localhost:8550 in your browser
```

> **Note**   The UI layer is optional – you can always hit the Gateway directly via curl / Postman.

## 📜 License
MIT
