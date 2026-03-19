"""
generate_report.py — Genera un informe final consolidado y legible.

Lee todos los chunks de análisis generados por el proceso principal y produce
un 'final_report.md' bien estructurado con resumen ejecutivo (vía Ollama),
highlights clave y estadísticas del análisis.

Uso:
    python generate_report.py --outdir ../data/output_optimized [--model MODEL]
                              [--sample-size N] [--no-ai]
"""
import re
import random
import logging
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Añadir el directorio padre al path para importar lib
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_chunks(outdir: Path) -> list[tuple[int, str]]:
    """Carga todos los chunks disponibles, ordenados por índice."""
    chunks = []
    for f in outdir.glob("api_chunk_*.txt"):
        m = re.search(r"chunk_(\d+)", f.name)
        if m:
            idx = int(m.group(1))
            text = f.read_text(encoding="utf-8", errors="ignore").strip()
            if text:  # Ignorar chunks vacíos
                chunks.append((idx, text))
    chunks.sort(key=lambda x: x[0])
    logging.info(f"  → {len(chunks)} chunks cargados.")
    return chunks


def sample_chunks(chunks: list[tuple[int, str]], n: int) -> list[tuple[int, str]]:
    """Toma una muestra estratificada de n chunks para el resumen AI."""
    if len(chunks) <= n:
        return chunks
    # Muestra del inicio, medio y final para representatividad
    third = n // 3
    start = chunks[:third]
    middle_start = len(chunks) // 2 - third // 2
    middle = chunks[middle_start : middle_start + third]
    end = chunks[-third:]
    sampled = start + middle + end
    # Eliminar duplicados por índice y ordenar
    seen = set()
    result = []
    for c in sampled:
        if c[0] not in seen:
            seen.add(c[0])
            result.append(c)
    return sorted(result, key=lambda x: x[0])


def extract_stats(chunks: list[tuple[int, str]]) -> dict:
    """Extrae estadísticas básicas de los chunks."""
    total_chars = sum(len(t) for _, t in chunks)
    # Buscar tablas mencionadas
    table_mentions: dict[str, int] = {}
    for _, text in chunks:
        for table in ["DatosPersonales", "Personas", "Registros", "Sacramentos"]:
            count = text.lower().count(table.lower())
            if count:
                table_mentions[table] = table_mentions.get(table, 0) + count

    # Detectar menciones a años (siglos XVII-XVIII)
    years = re.findall(r'\b(1[6-7]\d{2})\b', " ".join(t for _, t in chunks[:200]))
    year_counter: dict[str, int] = {}
    for y in years:
        decade = y[:3] + "0s"
        year_counter[decade] = year_counter.get(decade, 0) + 1

    return {
        "total_chunks": len(chunks),
        "total_chars": total_chars,
        "total_mb": total_chars / 1_048_576,
        "table_mentions": table_mentions,
        "top_decades": sorted(year_counter.items(), key=lambda x: -x[1])[:5],
    }


def build_executive_prompt(sample_text: str, schema_text: str) -> str:
    """Construye el prompt para el resumen ejecutivo."""
    return (
        "Eres un experto en genealogía histórica e historia de Valencia (España). "
        "A continuación tienes el esquema de una base de datos genealógica del siglo XVII-XVIII "
        "y una muestra del análisis AI realizado sobre sus datos.\n\n"
        f"## ESQUEMA:\n{schema_text}\n\n"
        f"## MUESTRA DE ANÁLISIS (fragmentos seleccionados):\n{sample_text[:8000]}\n\n"
        "## TAREA:\n"
        "Escribe un resumen ejecutivo en español (400-600 palabras) con:\n"
        "1. Descripción del propósito histórico de esta base de datos\n"
        "2. Los principales hallazgos sobre la estructura de los datos\n"
        "3. El valor genealógico de la información preservada\n"
        "4. Posibles usos para investigación histórica\n\n"
        "Usa un tono académico pero accesible. Responde SOLO con el resumen, sin títulos."
    )


def generate_markdown_report(
    outdir: Path,
    chunks: list[tuple[int, str]],
    stats: dict,
    executive_summary: str,
    schema_md: str,
    doc_md: str,
    generation_date: str,
) -> str:
    """Construye el contenido completo del informe en Markdown."""
    max_idx = max(idx for idx, _ in chunks) if chunks else 0
    min_idx = min(idx for idx, _ in chunks) if chunks else 0

    table_rows = "\n".join(
        f"| `{t}` | {c} menciones |"
        for t, c in sorted(stats["table_mentions"].items(), key=lambda x: -x[1])
    )
    decade_rows = "\n".join(
        f"| {d} | {c} |" for d, c in stats["top_decades"]
    )

    # Seleccionar extractos destacados (chunks no vacíos con más de 500 chars)
    highlights = [
        (idx, text[:600] + "...")
        for idx, text in chunks
        if len(text) > 500
    ]
    # Tomar muestra estratificada de 5 highlights
    sampled_hl = []
    if highlights:
        step = max(1, len(highlights) // 5)
        sampled_hl = highlights[::step][:5]

    highlight_sections = "\n\n".join(
        f"##### Chunk #{idx}\n> {text.replace(chr(10), ' ').replace(chr(13), '')}"
        for idx, text in sampled_hl
    )

    report = f"""# 📜 Informe Final — Base de Datos Genealógica Parroquial

**Generado:** {generation_date}
**Proyecto:** Genealogia Ollama (Análisis 100% Local con `qwen3:30b`)
**Datos fuente:** `data/arxv_DB.txt` — Registros parroquiales de Valencia (s. XVII-XVIII)

---

## 🎯 Resumen Ejecutivo

{executive_summary}

---

## 📊 Estadísticas del Análisis

| Métrica | Valor |
|---|---|
| **Chunks procesados** | {stats['total_chunks']:,} (de chunk _{min_idx}_ a _{max_idx}_) |
| **Volumen analizado** | {stats['total_mb']:.1f} MB de respuestas AI |
| **Caracteres generados** | {stats['total_chars']:,} |

### Frecuencia de Tablas en el Análisis

| Tabla | Frecuencia |
|---|---|
{table_rows}

### Décadas más referenciadas

| Década | Menciones |
|---|---|
{decade_rows}

---

## 🏗️ Estructura de la Base de Datos

{schema_md}

---

## 🗺️ Diagrama Entidad-Relación

```mermaid
erDiagram
    SACRAMENTOS ||--o{{ REGISTROS : "define tipo"
    REGISTROS ||--o{{ DATOSPERSONALES : "contiene info de"
    REGISTROS ||--o{{ PERSONAS : "tiene familiares en"

    REGISTROS {{
        bigint Registro PK
        integer Sacramentos FK
        string Libro
        string Folio
        string Asiento
        char Sexo
    }}
    DATOSPERSONALES {{
        bigint registro FK
        string nombre
        string apellido1
        string apellido2
        date fechanacimiento
        string lugarsacramento
        string residencia
        string notas
    }}
    PERSONAS {{
        bigint ID PK
        bigint registro FK
        string relacion
        string nombre
        string apellido1
        string apellido2
        string lugarnacimiento
    }}
    SACRAMENTOS {{
        integer id PK
        string Sacramentos
    }}
```

---

## 💬 Cómo Consultar la Base de Datos

Usa el script de consulta interactiva para hacer preguntas en lenguaje natural:

```bash
cd src
..\.venv_win\Scripts\python.exe query_db.py --outdir ..\data\output_optimized
```

### Ejemplos de preguntas:

- *"¿Qué tipos de sacramentos existen?"*
- *"¿Cómo se relacionan la tabla DatosPersonales y Personas?"*
- *"¿Qué información hay sobre los padres de los bautizados?"*
- *"Dame una consulta SQL para buscar personas de Torrent"*
- *"¿Cuántos registros aproximados tiene la base de datos?"*

### Comandos especiales en la interfaz de consulta:
- `!schema` — Muestra el esquema de tablas
- `!tablas` — Lista las tablas disponibles
- `!ayuda` — Muestra ayuda
- `salir` — Cierra la consulta

---

## 📋 Extractos Destacados del Análisis AI

Los siguientes fragmentos son muestra representativa del análisis obtenido:

{highlight_sections}

---

## 🔧 Otros Ficheros Generados

| Fichero | Descripción |
|---|---|
| `analysis_local.md` | Esquema técnico extraído por regex |
| `database_documentation.md` | Documentación estructurada de la BD |
| `analysis_ollama_combined.txt` | Análisis AI combinado (todos los chunks) |
| `process.log` | Log completo del proceso de análisis |
| `skeleton.sql` | Esquema SQL sin datos masivos (para análisis) |

---

*Informe generado automáticamente por `generate_report.py` · Proyecto Genealogia Ollama*
"""
    return report


def main():
    parser = argparse.ArgumentParser(description="Genera el informe final del análisis genealógico")
    parser.add_argument("--outdir", type=Path, default=Path("data/output_optimized"),
                        help="Carpeta de salida del análisis")
    parser.add_argument("--model", default="qwen3:30b", help="Modelo Ollama para el resumen")
    parser.add_argument("--sample-size", type=int, default=30,
                        help="Número de chunks a muestrear para el resumen AI")
    parser.add_argument("--no-ai", action="store_true",
                        help="Saltar el resumen ejecutivo AI (más rápido, offline)")
    args = parser.parse_args()

    if not args.outdir.exists():
        logging.error(f"El directorio no existe: {args.outdir}")
        sys.exit(1)

    logging.info("🚀 Iniciando generación de informe final...")

    # 1. Cargar chunks
    logging.info("📂 Cargando chunks de análisis...")
    chunks = load_chunks(args.outdir)
    if not chunks:
        logging.error("No se encontraron chunks. Ejecuta primero el análisis principal.")
        sys.exit(1)

    # 2. Extraer estadísticas
    logging.info("📊 Calculando estadísticas...")
    stats = extract_stats(chunks)

    # 3. Cargar ficheros de soporte
    schema_md = ""
    local_md_path = args.outdir / "analysis_local.md"
    if local_md_path.exists():
        schema_md = local_md_path.read_text(encoding="utf-8")

    doc_md = ""
    doc_path = args.outdir / "database_documentation.md"
    if doc_path.exists():
        doc_md = doc_path.read_text(encoding="utf-8")

    # 4. Generar resumen ejecutivo con AI (o placeholder)
    executive_summary = ""
    if args.no_ai:
        logging.info("⏭️  Saltando resumen AI (--no-ai activo)...")
        executive_summary = (
            "*Resumen ejecutivo no generado (flag --no-ai activo). "
            "Ejecuta sin --no-ai para obtener el análisis completo.*"
        )
    else:
        logging.info(f"🤖 Generando resumen ejecutivo con Ollama ({args.model})...")
        try:
            from lib.ollama_client import OllamaClient
            client = OllamaClient(model=args.model)
            sampled = sample_chunks(chunks, args.sample_size)
            sample_text = "\n\n---\n\n".join(
                f"[Chunk {idx}]:\n{text[:300]}" for idx, text in sampled
            )
            prompt = build_executive_prompt(sample_text, schema_md)
            executive_summary = client.call_generate(prompt)
            logging.info("✅ Resumen ejecutivo generado.")
        except Exception as e:
            logging.error(f"Error al generar resumen AI: {e}")
            executive_summary = (
                f"*Error al generar el resumen ejecutivo: {e}. "
                "Verifica que Ollama esté activo.*"
            )

    # 5. Construir informe
    logging.info("📝 Construyendo informe Markdown...")
    generation_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    report_content = generate_markdown_report(
        outdir=args.outdir,
        chunks=chunks,
        stats=stats,
        executive_summary=executive_summary,
        schema_md=schema_md,
        doc_md=doc_md,
        generation_date=generation_date,
    )

    # 6. Guardar
    output_path = args.outdir / "final_report.md"
    output_path.write_text(report_content, encoding="utf-8")
    size_kb = output_path.stat().st_size / 1024
    logging.info(f"✨ Informe guardado: {output_path} ({size_kb:.0f} KB)")
    print(f"\n✅ ¡Informe generado con éxito!")
    print(f"   📄 {output_path.resolve()}")
    print(f"   📏 {size_kb:.0f} KB — {stats['total_chunks']:,} chunks procesados")


if __name__ == "__main__":
    main()
