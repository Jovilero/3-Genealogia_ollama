import argparse
import logging
import math
import re
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Set

import requests

# ========================
# CONFIGURACIÓN OLLAMA
# ========================
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5-coder:14b"
CHUNK_CHARS = 200_000
MAX_RETRIES = 3

def setup_logging(outdir: Path):
    """Configura el sistema de logs (archivo + consola)."""
    log_file = outdir / "process.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def parse_schema_local(sql_text: str) -> Dict[str, Any]:
    """Extrae tablas/columnas/PK/FK de forma determinística usando regex."""
    CREATE_RE = re.compile(r"CREATE\s+TABLE\s+[`\"]?(\w+)[`\"]?\s*\((.*?)\);", re.I | re.S)
    COLUMN_RE = re.compile(r"^\s*[`\"]?(\w+)[`\"]?\s+([^\s,]+)", re.I)
    PK_TABLE_RE = re.compile(r"PRIMARY\s+KEY\s*\(([^)]+)\)", re.I)
    PK_INLINE_RE = re.compile(r"PRIMARY\s+KEY", re.I)
    FK_RE = re.compile(r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+[`\"]?(\w+)[`\"]?\s*\(([^)]+)\)", re.I)

    schema: Dict[str, Any] = {}
    for m in CREATE_RE.finditer(sql_text):
        table = m.group(1)
        body = m.group(2)
        lines = [l.strip() for l in re.split(r",\s*\n|,\s*$", body)]
        cols: List[Dict[str, str]] = []
        pks: List[str] = []
        fks: List[Dict[str, Any]] = []
        for ln in lines:
            pk_m = PK_TABLE_RE.search(ln)
            if pk_m:
                pks.extend([c.strip(" `\"") for c in pk_m.group(1).split(",")])
                continue
            fk_m = FK_RE.search(ln)
            if fk_m:
                cols_fk = [c.strip(" `\"") for c in fk_m.group(1).split(",")]
                fks.append({"columns": cols_fk, "ref_table": fk_m.group(2), "ref_columns": [c.strip(" `\"") for c in fk_m.group(3).split(",")]})
                continue
            col_m = COLUMN_RE.match(ln)
            if col_m:
                col, typ = col_m.group(1), col_m.group(2)
                cols.append({"name": col, "type": typ})
                if PK_INLINE_RE.search(ln):
                    pks.append(col)
        schema[table] = {"columns": cols, "primary_key": pks, "foreign_keys": fks}
    return schema

def call_ollama(model: str, prompt: str) -> str:
    """Llamada robusta a Ollama local."""
    payload = {"model": model, "prompt": prompt, "stream": False}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
            resp.raise_for_status()
            return resp.json().get("response", "")
        except Exception as e:
            logging.warning(f"Intento {attempt}/{MAX_RETRIES} fallido para Ollama: {e}")
            if attempt == MAX_RETRIES:
                raise
            time.sleep(2 * attempt)
    return ""

def get_processed_chunks(outdir: Path) -> Set[int]:
    """Detecta qué chunks ya existen en disco."""
    processed = set()
    for f in outdir.glob("api_chunk_*.txt"):
        m = re.match(r"api_chunk_(\d+)\.txt", f.name)
        if m:
            processed.add(int(m.group(1)))
    return processed

def main():
    parser = argparse.ArgumentParser(description="Analizador de SQL con Ollama y Regex (Juanj Style)")
    parser.add_argument("--sql", type=Path, required=True, help="Ruta al dump .sql")
    parser.add_argument("--outdir", type=Path, required=True, help="Carpeta de salida")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Modelo Ollama (default: {DEFAULT_MODEL})")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_CHARS, help="Tamaño del chunk en caracteres")
    parser.add_argument("--no-resume", action="store_true", help="Desactiva la reanudación")
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    setup_logging(args.outdir)

    logging.info("🚀 Iniciando proceso de análisis")
    if not args.sql.exists():
        logging.error(f"Fichero SQL no encontrado: {args.sql}")
        return

    full_text = args.sql.read_text(encoding="utf-8", errors="ignore")

    # --- Análisis Local (Deterministic) ---
    logging.info("🔍 Ejecutando análisis Regex local...")
    schema = parse_schema_local(full_text)
    
    local_md = ["# Esquema Detectado (Regex)\n"]
    for t, data in schema.items():
        local_md.append(f"## {t}\n**PK**: {', '.join(data['primary_key']) or '-'}\n\n| Columna | Tipo |\n|---|---|\n")
        for c in data["columns"]:
            local_md.append(f"| {c['name']} | {c['type']} |\n")
        for fk in data["foreign_keys"]:
            local_md.append(f"\n- FK: ({', '.join(fk['columns'])}) -> {fk['ref_table']}\n")
        local_md.append("\n")
    
    (args.outdir / "analysis_local.md").write_text("".join(local_md), encoding="utf-8")
    logging.info(f"📊 Análisis local guardado.")

    # --- Análisis Ollama (AI) ---
    logging.info(f"🤖 Iniciando análisis con Ollama ({args.model})")
    total_len = len(full_text)
    parts = math.ceil(total_len / args.chunk_size)
    processed = set() if args.no_resume else get_processed_chunks(args.outdir)

    for i in range(parts):
        chunk_idx = i + 1
        if chunk_idx in processed:
            logging.info(f"⏭️  Saltando chunk {chunk_idx:03d} (ya procesado)")
            continue

        start = i * args.chunk_size
        end = min((i + 1) * args.chunk_size, total_len)
        chunk_text = full_text[start:end]

        logging.info(f"🧠 Analizando chunk {chunk_idx}/{parts} ({len(chunk_text):,} chars)...")
        prompt = (
            "Analiza el siguiente fragmento SQL y extrae las tablas, relaciones y propósito.\n"
            f"--- CHUNK {chunk_idx} ---\n```sql\n{chunk_text}\n```"
        )
        
        try:
            result = call_ollama(args.model, prompt)
            (args.outdir / f"api_chunk_{chunk_idx:03d}.txt").write_text(result, encoding="utf-8")
        except Exception as e:
            logging.error(f"Fallo crítico en chunk {chunk_idx}: {e}")
            break

    # Combinación final
    final_output = args.outdir / "analysis_ollama_combined.txt"
    chunk_files = sorted(args.outdir.glob("api_chunk_*.txt"))
    with open(final_output, "w", encoding="utf-8") as f:
        for cf in chunk_files:
            f.write(f"\n\n{'='*20} {cf.name} {'='*20}\n\n")
            f.write(cf.read_text(encoding="utf-8"))
    
    logging.info(f"✅ Proceso finalizado. Resultado combinado en: {final_output}")

if __name__ == "__main__":
    main()
