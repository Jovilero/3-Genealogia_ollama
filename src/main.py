#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Analiza un .sql con dos métodos en una sola ejecución:

A) API (gpt-4o-mini) SIN PDFs: envía el .sql por CHUNKS como input_text.
B) Local: regex para extraer tablas/columnas/PK/FK.

Uso:
  export OPENAI_API_KEY="<SU_API_KEY_AQUI>"
  python main.py --sql /ruta/arxv_DB.txt --outdir ./data/output
"""

import argparse, os, re, math, time, requests
from typing import Dict, Any, List

# Configuración Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
DEFAULT_MODEL = "qwen2.5-coder:14b"
CHUNK_CHARS = 200_000
MAX_RETRIES = 3

def parse_schema_local(sql_text: str) -> Dict[str, Any]:
    """Extrae tablas/columns/PK/FK de forma sencilla (regex)."""
    CREATE_RE = re.compile(r"CREATE\s+TABLE\s+[`\"]?(\w+)[`\"]?\s*\((.*?)\);", re.I | re.S)
    COLUMN_RE = re.compile(r"^\s*[`\"]?(\w+)[`\"]?\s+([^\s,]+)", re.I)
    PK_TABLE_RE = re.compile(r"PRIMARY\s+KEY\s*\(([^)]+)\)", re.I)
    PK_INLINE_RE = re.compile(r"PRIMARY\s+KEY", re.I)
    FK_RE = re.compile(r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+[`\"]?(\w+)[`\"]?\s*\(([^)]+)\)", re.I)

    schema: Dict[str, Any] = {}
    for m in CREATE_RE.finditer(sql_text):
        table = m.group(1)
        body = m.group(2)
        # Separar por comas pero cuidando paréntesis si los hubiera (simplificado)
        lines = [l.strip() for l in re.split(r",\s*\n|,\s*$", body)]
        cols: List[Dict[str, str]] = []
        pks: List[str] = []
        fks: List[Dict[str, Any]] = []
        for ln in lines:
            # PK explicito al final: PRIMARY KEY (col)
            pk_m = PK_TABLE_RE.search(ln)
            if pk_m:
                pks.extend([c.strip(" `\"") for c in pk_m.group(1).split(",")])
                continue
                
            # FK
            fk_m = FK_RE.search(ln)
            if fk_m:
                cols_fk = [c.strip(" `\"") for c in fk_m.group(1).split(",")]
                ref_table = fk_m.group(2)
                ref_cols = [c.strip(" `\"") for c in fk_m.group(3).split(",")]
                fks.append({"columns": cols_fk, "ref_table": ref_table, "ref_columns": ref_cols})
                continue

            # Columnas e Inline PK
            col_m = COLUMN_RE.match(ln)
            if col_m:
                col, typ = col_m.group(1), col_m.group(2)
                cols.append({"name": col, "type": typ})
                if PK_INLINE_RE.search(ln):
                    pks.append(col)
                    
        schema[table] = {"columns": cols, "primary_key": pks, "foreign_keys": fks}
    return schema

def call_ollama_chunk(model, chunk_text, idx):
    """Envía un chunk a Ollama local y devuelve el análisis."""
    prompt = (
        "Analiza ÚNICAMENTE el fragmento SQL que adjunto entre ```sql ...```.\n"
        "Explica lo entendido y, si es posible, enumera:\n"
        "- Tablas y para qué sirven\n"
        "- Columnas principales (nombre y tipo)\n"
        "- Claves primarias y foráneas\n"
        "- Relaciones entre tablas\n"
        "Si el fragmento está incompleto, indica limitaciones y referencias cruzadas que dependan de otros trozos.\n\n"
        f"--- FRAGMENTO #{idx} ---\n```sql\n{chunk_text}\n```"
    )
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=300)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            print(f"⚠️ Intento {attempt+1} fallido: {e}")
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2*(attempt+1))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sql", required=True, help="Ruta al dump .sql")
    ap.add_argument("--outdir", required=True, help="Carpeta de salida")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Modelo Ollama (default: {DEFAULT_MODEL})")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    full_text: str = ""
    print(f"\n📤 Leyendo y enviando por chunks → Ollama Local: {args.sql}")
    if not os.path.exists(args.sql):
        print(f"❌ Error: El archivo {args.sql} no existe.")
        return

    with open(args.sql, "r", encoding="utf-8", errors="ignore") as f:
        full_text = f.read()

    # =========================
    # B) Local (Deterministic)
    # =========================
    print("🔍 Analizando en local (regex determinístico)…")
    schema = parse_schema_local(full_text)

    md = ["# Esquema detectado (Local Determinístico)\n"]
    table_data: Dict[str, Any]
    for t, table_data in schema.items():
        md.append(f"## {t}\n")
        pk: str = ", ".join(table_data["primary_key"]) if table_data["primary_key"] else "-"
        md.append(f"**Primary Key**: {pk}\n\n")
        md.append("| Columna | Tipo |\n|---|---|\n")
        col: Dict[str, str]
        for col in table_data["columns"]:
            md.append(f"| {col['name']} | {col['type']} |\n")
        if table_data["foreign_keys"]:
            md.append("\n**FK**:\n")
            fk_data: Dict[str, Any]
            for fk_data in table_data["foreign_keys"]:
                md.append(f"- ({', '.join(fk_data['columns'])}) → {fk_data['ref_table']}({', '.join(fk_data['ref_columns'])})\n")
        md.append("\n")
    
    local_out = os.path.join(args.outdir, "analysis_local.md")
    with open(local_out, "w", encoding="utf-8") as f:
        f.write("".join(md))
    print(f"📊 Resultado local guardado en: {local_out}")
    
    # =========================
    # A) Ollama (AI)
    # =========================
    total_chars = len(full_text)
    parts = math.ceil(total_chars / CHUNK_CHARS)
    print(f"🤖 Preparando análisis con Ollama model: {args.model}")
    print(f"  → Total chars: {total_chars:,} | chunks: {parts}")

    api_results = []
    for i in range(parts):
        start_idx: int = int(i * CHUNK_CHARS)
        end_idx: int = int(min((i+1) * CHUNK_CHARS, total_chars))
        chunk = full_text[start_idx:end_idx]
        print(f"👉 Analizando chunk {i+1}/{parts} (caracteres {start_idx}-{end_idx})...")
        try:
            out = call_ollama_chunk(args.model, chunk, i+1)
            api_results.append(f"--- CHUNK {i+1}/{parts} ---\n{out}\n")
        except Exception as e:
            print(f"❌ Error crítico en chunk {i+1}: {e}")
            api_results.append(f"--- CHUNK {i+1}/{parts} ---\nERROR: {e}\n")

    api_out = os.path.join(args.outdir, "analysis_ollama.txt")
    with open(api_out, "w", encoding="utf-8") as f:
        f.write("\n".join(api_results))
    print(f"📊 Resultado Ollama guardado en: {api_out}")

    print("\n✅ Proceso completado. Compara `analysis_ollama.txt` con `analysis_local.md`.")

if __name__ == "__main__":
    main()
