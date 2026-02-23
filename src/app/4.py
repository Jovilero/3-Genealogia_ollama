#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Analiza un .sql en dos modos:

A) API (gpt-4o-mini) por chunks como TEXTO (no re-sube nada).
   - Guarda cada respuesta en outdir/api_chunk_###.txt
   - Índice en outdir/api_index.tsv
   - Reanuda:
       * detecta chunks locales ya hechos
       * (opcional) salta también los índices que ya veas subidos como 'sql_chunk_###.txt' en tu cuenta

B) Local (regex): CREATE TABLE / columnas / PK / FK → outdir/analysis_local.md
"""

import os, re, time, requests

# ========================
# CONFIGURACIÓN OLLAMA
# ========================
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
DEFAULT_MODEL = "qwen2.5-coder:14b"
SQL_FILE = "/mnt/a/3-Ocio/4-Programacion/1-RepositoriosGIT/2-Genealogia_gpt_api/data/arxv_DB.txt"
OUTDIR   = "/mnt/a/3-Ocio/4-Programacion/1-RepositoriosGIT/2-Genealogia_gpt_api/data/output"

CHUNK_CHARS   = 200_000   # caracteres por chunk
RESUME_LOCAL  = True      # saltar chunks que ya existen en OUTDIR
# ========================

MAX_RETRIES = 3
SLEEP_BASE = 2

# ---------------------------
# LOCAL: análisis de esquema con regex
# ---------------------------
def parse_schema_local(sql_text: str):
    CREATE_RE = re.compile(r"CREATE\s+TABLE\s+[`\"]?(\w+)[`\"]?\s*\((.*?)\);", re.I | re.S)
    COLUMN_RE = re.compile(r"^\s*[`\"]?(\w+)[`\"]?\s+([^\s,]+)", re.I)
    PK_TABLE_RE = re.compile(r"PRIMARY\s+KEY\s*\(([^)]+)\)", re.I)
    FK_RE = re.compile(r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+[`\"]?(\w+)[`\"]?\s*\(([^)]+)\)", re.I)

    schema = {}
    for m in CREATE_RE.finditer(sql_text):
        table = m.group(1)
        body = m.group(2)
        lines = [l.strip() for l in re.split(r",\s*\n", body)]
        cols, pks, fks = [], [], []
        for ln in lines:
            pk_m = PK_TABLE_RE.search(ln)
            if pk_m:
                pks = [c.strip(" `\"") for c in pk_m.group(1).split(",")]
            fk_m = FK_RE.search(ln)
            if fk_m:
                cols_fk = [c.strip(" `\"") for c in fk_m.group(1).split(",")]
                ref_table = fk_m.group(2)
                ref_cols = [c.strip(" `\"") for c in fk_m.group(3).split(",")]
                fks.append({"columns": cols_fk, "ref_table": ref_table, "ref_columns": ref_cols})
            col_m = COLUMN_RE.match(ln)
            if col_m:
                col, typ = col_m.group(1), col_m.group(2)
                cols.append({"name": col, "type": typ})
        schema[table] = {"columns": cols, "primary_key": pks, "foreign_keys": fks}
    return schema

def write_local_markdown(schema: dict, path: str):
    md = ["# Esquema detectado (Local)\n"]
    for t, d in schema.items():
        md.append(f"## {t}\n")
        pk = ", ".join(d["primary_key"]) if d["primary_key"] else "-"
        md.append(f"**Primary Key**: {pk}\n\n")
        md.append("| Columna | Tipo |\n|---|---|\n")
        for c in d["columns"]:
            md.append(f"| {c['name']} | {c['type']} |\n")
        if d["foreign_keys"]:
            md.append("\n**FK**:\n")
            for fk in d["foreign_keys"]:
                md.append(f"- ({', '.join(fk['columns'])}) → {fk['ref_table']}({', '.join(fk['ref_columns'])})\n")
        md.append("\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(md))

# ---------------------------
# API: enviar chunk como texto
# ---------------------------
def build_prompt(chunk_text: str, idx: int):
    return (
        "Analiza ÚNICAMENTE el fragmento SQL entre ```sql ...```.\n"
        "Devuelve una explicación clara y (si es posible) una lista estructurada con:\n"
        "- Tablas y para qué sirven\n"
        "- Columnas principales (nombre y tipo)\n"
        "- Claves primarias y foráneas\n"
        "- Relaciones entre tablas\n"
        "Si el fragmento está incompleto, indica limitaciones.\n\n"
        f"--- FRAGMENTO #{idx} ---\n```sql\n{chunk_text}\n```"
    )

def call_ollama_chunk_text(model, prompt: str):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=300)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            print(f"⚠️ Intento {attempt} fallido: {e}")
            if attempt == MAX_RETRIES:
                raise
            time.sleep(SLEEP_BASE * attempt)

# ---------------------------
# RESUME helpers
# ---------------------------
def detect_completed_chunks_local(outdir: str):
    """Set de índices (int) ya procesados localmente: api_chunk_###.txt"""
    done = set()
    if not os.path.isdir(outdir):
        return done
    for name in os.listdir(outdir):
        m = re.match(r"api_chunk_(\d{3})\.txt$", name)
        if m:
            done.add(int(m.group(1)))
    return done

def skip_chars_for_chunks(fh, chunks_to_skip: int, chunk_size: int):
    """Avanza el puntero del fichero saltando 'chunks_to_skip' trozos."""
    for _ in range(chunks_to_skip):
        _ = fh.read(chunk_size)

# ---------------------------
# MAIN
# ---------------------------
def main():
    os.makedirs(OUTDIR, exist_ok=True)
    # client = OpenAI()
    print(f"\n📤 Conexion con Ollama local")
    
    # ===========
    # Calcular desde qué índice reanudar (Local only)
    # ===========
    local_done = detect_completed_chunks_local(OUTDIR) if RESUME_LOCAL else set()
    max_local = max(local_done) if local_done else 0

    start_index = max_local + 1  # siguiente a lo ya visto
    if start_index < 1:
        start_index = 1

    print(f"\n📌 Reanudación:")
    print(f"   - Último chunk LOCAL procesado: {max_local if max_local else 'ninguno'}")
    print(f"   ➜ Empezaremos desde el chunk  : {start_index:03d}")

    api_index_path = os.path.join(OUTDIR, "api_index.tsv")
    combined_path = os.path.join(OUTDIR, "analysis_api_combined.txt")

    # ===========
    # OLLAMA (por chunks de TEXTO)
    # ===========
    print(f"\n🤖 Enviando por chunks (TEXTO) a Ollama: {SQL_FILE}")
    idx = 1
    with open(SQL_FILE, "r", encoding="utf-8", errors="ignore") as f_in:
        # saltar lo ya cubierto
        if start_index > 1:
            skip_chars_for_chunks(f_in, start_index - 1, CHUNK_CHARS)
            idx = start_index

        buffer = f_in.read(CHUNK_CHARS)
        while buffer:
            # Si ya existe localmente, saltar
            if RESUME_LOCAL and os.path.exists(os.path.join(OUTDIR, f"api_chunk_{idx:03d}.txt")):
                print(f"⏭️  Chunk {idx:03d} ya existe (local), salto.")
                idx += 1
                buffer = f_in.read(CHUNK_CHARS)
                continue

            print(f"🤖 Analizando chunk {idx:03d} (len={len(buffer):,} chars) con {DEFAULT_MODEL}…")
            prompt = build_prompt(buffer, idx)
            out_text = call_ollama_chunk_text(DEFAULT_MODEL, prompt)

            chunk_out = os.path.join(OUTDIR, f"api_chunk_{idx:03d}.txt")
            with open(chunk_out, "w", encoding="utf-8") as w:
                w.write(out_text or "")

            with open(api_index_path, "a", encoding="utf-8") as idxf:
                idxf.write(f"{idx}\t{len(buffer)}\t{chunk_out}\n")

            idx += 1
            buffer = f_in.read(CHUNK_CHARS)

    # Combinar resultados
    chunk_files = sorted([fn for fn in os.listdir(OUTDIR) if re.match(r"api_chunk_\d{3}\.txt$", fn)])
    with open(combined_path, "w", encoding="utf-8") as out_all:
        for fn in chunk_files:
            out_all.write(f"===== {fn} =====\n")
            with open(os.path.join(OUTDIR, fn), "r", encoding="utf-8", errors="ignore") as cf:
                out_all.write(cf.read() + "\n\n")
    print(f"📊 Resultado API combinado: {combined_path}")

    # ===========
    # LOCAL (regex) – esquema completo
    # ===========
    print("\n🔍 Analizando en local (regex)…")
    with open(SQL_FILE, "r", encoding="utf-8", errors="ignore") as f_all:
        full_text = f_all.read()

    schema = parse_schema_local(full_text)
    local_md_path = os.path.join(OUTDIR, "analysis_local.md")
    write_local_markdown(schema, local_md_path)
    print(f"📘 Resultado local: {local_md_path}")

    print("\n✅ Listo. Reanuda sin re-subir y sin repetir chunks.")
    print("   Índice de chunks (API):", api_index_path)

if __name__ == "__main__":
    main()
"""
python main.py 2>&1 | tee run_$(date +%Y%m%d_%H%M).log
""" 