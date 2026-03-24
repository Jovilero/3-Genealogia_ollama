# 🧬 Genealogia Ollama — Referencia Técnica del Proyecto

> Actualizado: 2026-03-24 · Rama activa: `main` (sincronizada con `origin/main`)

---

## 📌 Propósito del Proyecto

Analizador **local** e inteligente de bases de datos genealógicas SQL (archivos de 1.3 GB+) usando LLMs locales vía **Ollama**.

- Procesa dump SQL de registros parroquiales históricos (siglos XVII–XVIII).
- Arquitectura **zero-cloud**: todos los datos quedan en disco local.
- Extrae esquema por Regex (rápido, determinista) + análisis semántico por LLM (profundo).
- Interfaz web Streamlit + CLI unificada + Chat interactivo.

---

## 🗂️ Árbol de Archivos Clave

```
3-Genealogia_ollama/
├── genealogia.py              # CLI unificada (punto de entrada principal)
├── requirements.txt           # Dependencias Python
├── Dockerfile / docker-compose.yaml
├── .env / .env.example        # Config de entorno
├── .gitignore
├── .pre-commit-config.yaml    # Hooks: black, ruff, mypy
├── .github/
│   └── copilot-instructions.md  # Contexto automático para GitHub Copilot
├── backup_db.py               # Backup pg_dump
├── check_db_size.py
├── verify_db_copy.py
├── upgrade_model.py
│
├── src/
│   ├── __init__.py
│   ├── main.py                # Analizador original (chunks + Ollama secuencial)
│   ├── main_optimized.py      # Analizador con ThreadPoolExecutor (USAR ESTE)
│   ├── ui.py                  # Interfaz Streamlit (462 líneas)
│   ├── query_db.py            # Chat CLI interactivo
│   ├── check_status.py        # Monitor de integridad/progreso
│   ├── generate_report.py     # Generador de final_report.md
│   ├── resume_full_run.py     # Reanudación de procesos interrumpidos
│   ├── detectar_extension.py  # Detección de tipo de archivo SQL (referencia canónica)
│   └── lib/
│       ├── ollama_client.py      # Cliente HTTP Ollama con caché y paralelismo
│       ├── sql_processor.py      # Parser SQL + generador Mermaid ER
│       ├── db_executor.py        # Ejecutor SQL seguro sobre SQLAlchemy
│       └── cartography_bridge.py # Puente no destructivo con repo 6 (genealogia-cartografia-pro)
│
├── tests/
│   ├── test_critical_path.py  # Tests de DBExecutor, OllamaClient, Mermaid
│   ├── test_cli.py
│   ├── test_parsing.py
│   ├── test_ollama_mock.py
│   ├── test_sql_processor.py
│   ├── test_io_resume.py
│   ├── test_system_health.py
│   └── test_ui.py
│
├── data/
│   ├── arxv_DB.txt            # Dump SQL original (~1.3 GB, NO versionado)
│   ├── sample_sql.txt
│   └── output_optimized/      # Entregables: analysis_local.md, final_report.md, chunks
│
└── docs/
    └── WORKLOG/
        ├── README.md
        ├── 2026-03-23_1905_estado_inicial.md
        └── 2026-03-23_auditoria_estado_y_ramas.md
```

---

## 🚀 Comandos CLI Principales

El punto de entrada es **siempre `genealogia.py`**:

| Comando | Script subyacente | Descripción |
|---|---|---|
| `python genealogia.py run --sql data/arxv_DB.txt --outdir data/output_optimized` | `src/main_optimized.py` | Análisis completo (skeleton + Ollama paralelo) |
| `python genealogia.py status --outdir data/output_optimized` | `src/check_status.py` | Progreso e integridad de chunks |
| `python genealogia.py report --outdir data/output_optimized` | `src/generate_report.py` | Genera `final_report.md` |
| `python genealogia.py web` | `src/ui.py` vía Streamlit | Interfaz web completa |
| `python genealogia.py chat --outdir data/output_optimized` | `src/query_db.py` | Chat CLI con historial |

> Aliases disponibles: `analyze` = `run`, `query` = `chat`, `ui` = `web`.

---

## 🧩 Arquitectura de Módulos

### `src/lib/ollama_client.py`
- Clase `OllamaClient` con caché en memoria por prompt.
- Parámetros: `url`, `model` (default `qwen3:30b`), `temperature`, `num_ctx` (default 8192).
- Métodos: `call_generate(prompt)` con retry x3, `process_parallel(prompts, max_workers=3)`.

### `src/lib/db_executor.py`
- `DBExecutor` conecta vía SQLAlchemy + `python-dotenv`.
- Lee `DATABASE_URL` del `.env`; si no existe, usa `sqlite:///:memory:`.
- Safeguards: bloquea `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, etc. Solo permite `SELECT`.
- Previene múltiples sentencias concatenadas con `;`.

### `src/lib/sql_processor.py`
- `SQLProcessor.parse_schema_local(text)` → dict con tablas, columnas, PK, FK (Regex).
- `SQLProcessor.schema_to_mermaid(schema_dict)` → código Mermaid ER listo para Streamlit.

### `src/ui.py`
5 pestañas Streamlit:
1. **💬 Autómata Histórico** — Chat con contexto del esquema y del informe.
2. **💻 Experto SQL** — Genera SQL con LLM, ejecuta, muestra tabla, gráficos, Insight IA, Exportar Excel, Narrativa Biográfica.
3. **📊 Grafo de Esquema** — Diagrama Mermaid ER + Diccionario de datos.
4. **📑 Informe Ejecutivo** — Muestra `final_report.md`.
5. **🛠️ Administración** — Botón de backup pg_dump + lista de archivos `.dump`.

**Característica clave SQL tab**: Auto-healing loop (max 3 reintentos). Si la query falla, el LLM recibe el error y lo corrige automáticamente.

---

## 🔧 Dependencias (`requirements.txt`)

```
requests>=2.28.0
pytest>=7.0.0
pytest-mock>=3.10.0
streamlit>=1.30.0
sqlalchemy>=2.0.0
pandas>=2.0.0
python-dotenv>=1.0.0
psycopg2-binary>=2.9.0
openpyxl>=3.1.0
```

Requiere también: **Python 3.10+** y **Ollama** corriendo en `localhost:11434`.

---

## ⚙️ Configuración de Entorno (`.env`)

```env
OPENAI_API_KEY=sk-placeholder-your-key-here   # No usado actualmente
OLLAMA_URL=http://localhost:11434/api/generate
DATABASE_URL=postgresql://user:pass@host:5432/dbname  # Si usas Postgres
```

> Si `DATABASE_URL` no está definida, `DBExecutor` usa `sqlite:///:memory:` (útil para tests).

---

## 🧪 Tests

```bash
python -m pytest          # Ejecuta toda la suite
python -m pytest -v       # Con detalle
python -m pytest tests/test_critical_path.py  # Solo ruta crítica
```

**Cobertura de tests:**

| Archivo | Qué prueba |
|---|---|
| `test_critical_path.py` | DBExecutor, OllamaClient (mock 404), Mermaid ER |
| `test_parsing.py` | Parser SQL Regex |
| `test_ollama_mock.py` | Mocking completo de Ollama |
| `test_sql_processor.py` | SQLProcessor métodos |
| `test_io_resume.py` | Lógica de reanudación de chunks |
| `test_system_health.py` | Salud general del sistema |
| `test_cli.py` | Comandos CLI |
| `test_ui.py` | Componentes Streamlit |

---

## 🌿 Estado Git

### Ramas

| Rama | Commit | Notas |
|---|---|---|
| `main` (**HEAD**) | `8ae5894` | Sincronizada 1:1 con `origin/main` ✅ |
| `origin/main` | `8ae5894` | Sincronizada ✅ |

> ✅ Repositorio limpio. Ramas `feat/ui-doc-sync-20260323` y `safety/2026-03-23-precontinuidad` eliminadas local y remotamente tras el merge.

### Historial de Commits (HEAD → atrás)

```
8ae5894  chore: add .pre-commit-config.yaml (black, ruff, mypy)          [main, origin/main]
0a7d70e  feat: add .github/copilot-instructions.md for Copilot context
dba1b39  feat: add cartography bridge to consume repo 6 CLI
f702025  merge: integrar feat/ui-doc-sync-20260323 en main
d4f22e3  docs: añadir project_reference.md como referencia técnica permanente
ab0b239  docs(sync): declarar detectar_extension como referencia canonica
0eed879  fix(query_db): añadir import argparse para comando chat
6c907c2  docs: eliminar secciones duplicadas en README
f23ef8a  docs: añadir worklog y auditoría 2026-03-23
73b18de  feat(ui): actualizar interfaz Streamlit
dca9575  feat: Phase 16 & 17 - Dynamic Visuals, Excel Export, AI Biographies
debe519  feat: Phases 12-15 - Data Insights, DB Safeguards, Backups, Replica Verification
cd52a99  Professionalization: pathlib, logging, resume logic, README
498c6b0  Alignment: Migrated legacy app/ scripts to local-first Ollama
dc0f865  Initial commit - Clean Base (Sanitized)
```

### Diff `main` → `feat/ui-doc-sync-20260323` (resumen)

| Archivo modificado | Cambios |
|---|---|
| `src/ui.py` | +90 líneas (refactoring UI + fixes persistencia) |
| `src/query_db.py` | +1 línea (import argparse) |
| `src/detectar_extension.py` | +4 líneas (comentario canónico) |
| `readme.md` | -42 líneas (secciones duplicadas eliminadas) |
| `docs/WORKLOG/*.md` | Nuevos: auditoría, estado inicial, README |

---

## 📋 Decisiones Operativas Registradas

1. **No push directo a `main` en estado sucio** → crear rama feature primero.
2. **Separar commits funcionales de documentales** para facilitar revisión y rollback.
3. `detectar_extension.py` es la **referencia canónica** para detectar tipo de archivo SQL.
4. Modelo preferido: **`qwen3:30b`** con `num_ctx=8192` (máximo recomendado en 32 GB RAM).
5. Temperatura: `0.0` para SQL (determinista), `0.7` para chat histórico, `0.8` para narrativa biográfica.

---

## 🚨 Pendientes / Deuda Técnica

- [x] ~~Push de `main` a `origin/main`~~ → ✅ Resuelto 2026-03-24
- [x] ~~Merge de `feat/ui-doc-sync-20260323` a `main`~~ → ✅ Resuelto 2026-03-24
- [x] ~~Limpiar rama `safety/2026-03-23-precontinuidad`~~ → ✅ Eliminada 2026-03-24
- [ ] `src/main.py` vs `src/main_optimized.py`: dos analizadores. Evaluar si eliminar el legacy `main.py`.
- [ ] `test_critical_path.py` contiene CREATE/INSERT que el safeguard bloquearía en producción (funciona solo con `sqlite:///:memory:`).
- [ ] `.env.example` menciona `OPENAI_API_KEY` que actualmente no se usa — limpiar o documentar.
- [ ] `cartography_bridge.py` depende de `genealogia_cartografia_pro` (repo 6) — verificar que ese paquete está instalado en el entorno.

---

## 🐳 Docker

```bash
docker-compose up --build
```

Ollama configurado como `host.docker.internal` para que el contenedor pueda salir a la red local.

---

## 🔄 Flujo de Trabajo Típico (de 0 a consultas)

```
1. Asegurarse de que Ollama está corriendo con qwen3:30b
2. python genealogia.py run --sql data/arxv_DB.txt --outdir data/output_optimized
3. python genealogia.py report --outdir data/output_optimized
4. python genealogia.py web     ← abre la UI en el navegador
     → Tab "Experto SQL": escribe petición en lenguaje natural → SQL automático → resultados
     → Tab "Autómata Histórico": chat libre sobre la BD
5. python genealogia.py status  ← para verificar progreso si el análisis fue interrumpido
```
