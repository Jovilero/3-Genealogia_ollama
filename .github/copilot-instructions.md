# GitHub Copilot — Instrucciones para 3-Genealogia_ollama

> Cargado automáticamente por GitHub Copilot en VS Code.

---

## 👤 Perfil del Desarrollador

- **Dev:** juanj — Python full-stack, énfasis en datos genealógicos, IA local
- **OS:** Windows 11 | **IDE:** VS Code | **Hardware:** RTX 4070 · i7-11700K · 32 GB RAM
- **IA Local:** Ollama (`qwen2.5-coder:14b`, `llama3.1`) — SIEMPRE preferir sobre cloud APIs

---

## 📐 Reglas de Código (No Negociables)

| Regla | Detalle |
|-------|---------|
| **Idioma** | Código/funciones en **inglés**, mensajes/prints en **español** |
| **Type hints** | Siempre en código nuevo (Python 3.10+) |
| **Paths** | `pathlib.Path` — nunca `os.path` |
| **Logging** | Módulo `logging` — nunca `print()` en producción |
| **Secrets** | Solo en `.env` (git-ignored) — nunca hardcoded |
| **SQL** | Prepared statements / parámetros — nunca f-strings con user input |
| **Subprocess** | `subprocess.run(["cmd", "arg"])` — nunca `shell=True` |
| **Commits** | Conventional Commits: `feat:`, `fix:`, `refactor:`, `chore:` |
| **Local-first** | Datos genealógicos = privados → Ollama local, NUNCA APIs cloud externas |

---

## 🔄 Workflow O-P-E-V

Para tareas complejas: **Explorar → Planificar** (esperar confirmación) **→ Ejecutar → Verificar**

---

## 🗂️ Contexto del Proyecto

- **Propósito:** Analizador local de bases de datos genealógicas SQL usando LLMs via Ollama
- **Arquitectura:** `genealogia.py` CLI → `SQLProcessor` → `OllamaClient` (paralelo) → `data/output_optimized/`
- **Modelo Ollama activo:** `qwen2.5-coder:14b` en `localhost:11434`
- **Datos sensibles:** BD genealógica SQL — registros históricos de personas, datos personales → NUNCA cloud
- **Stack:** Python 3.10+ · ollama client · Docker · Streamlit (UI) · pytest
- **Estructura:**
  - `genealogia.py` — CLI principal (comandos: `run`, `status`, `report`, `web`, `chat`)
  - `src/` — Módulos de procesamiento
  - `data/` — Dumps SQL y outputs (NO commitear datos reales)
  - `docs/` — Documentación

### Comandos clave
```bash
python genealogia.py run      # Procesar BD
python genealogia.py status   # Diagnóstico
python genealogia.py web      # Lanzar Streamlit UI
python genealogia.py chat     # Chat interactivo CLI
```

### Contexto Ollama
- Verificar disponibilidad: `curl http://localhost:11434/api/tags`
- Si el modelo no está cargado, hacer pull: `ollama pull qwen2.5-coder:14b`
- RTX 4070 puede correr 14b sin offload a CPU

### Pendientes conocidos
- Añadir `.pre-commit-config.yaml`
- Migrar `requirements.txt` a `pyproject.toml`
- Aumentar cobertura de tests (actualmente parcial)
