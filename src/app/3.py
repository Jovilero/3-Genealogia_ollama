#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Analiza un .sql en dos modos:

A) API (gpt-4o-mini): manda el SQL por chunks como texto → guarda cada chunk y combina todo.
B) Local (regex): analiza CREATE TABLE, columnas, PK/FK → guarda un Markdown.

Configura las rutas y parámetros en las variables al inicio.
"""

import os, re, time
from openai import OpenAI

# ========================
# CONFIGURACIÓN
# ========================
SQL_FILE = "/mnt/a/3-Ocio/4-Programacion/1-RepositoriosGIT/2-Genealogia_gpt_api/data/arxv_DB.txt"
OUTDIR   = "/mnt/a/3-Ocio/4-Programacion/1-RepositoriosGIT/2-Genealogia_gpt_api/data/output"
MODEL    = "gpt-4o-mini"
CHUNK_CHARS = 200_000   # caracteres por chunk
RESUME   = True         # reanudar si hay chunks ya procesados
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

def call_openai_chunk_text(client: OpenAI, model: str, prompt: str):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.responses.create(
                model=model,
                input=[{"role": "user", "content": prompt}]
            )
            return resp.output_text
        except Exception:
            if attempt == MAX_RETRIES:
                raise
            time.sleep(SLEEP_BASE * attempt)

# ---------------------------
# UTIL: reanudar
# ---------------------------
def detect_completed_chunks(outdir: str):
    done = set()
    if not os.path.isdir(outdir):
        return done
    for name in os.listdir(outdir):
        m = re.match(r"api_chunk_(\d{3})\.txt$", name)
        if m:
            done.add(int(m.group(1)))
    return done

# ---------------------------
# MAIN
# ---------------------------
def main():
    os.makedirs(OUTDIR, exist_ok=True)
    client = OpenAI()

    # ===========
    # API (chunks)
    # ===========
    print(f"\n📤 Enviando por chunks (TEXTO) a la API: {SQL_FILE}")
    api_index_path = os.path.join(OUTDIR, "api_index.tsv")
    combined_path = os.path.join(OUTDIR, "analysis_api_combined.txt")

    done = detect_completed_chunks(OUTDIR) if RESUME else set()
    next_idx = 1

    with open(SQL_FILE, "r", encoding="utf-8", errors="ignore") as f_in:
        buffer = f_in.read(CHUNK_CHARS)
        while buffer:
            idx = next_idx
            next_idx += 1

            if RESUME and idx in done:
                print(f"⏭️  Chunk {idx:03d} ya existe, salto.")
                buffer = f_in.read(CHUNK_CHARS)
                continue

            print(f"🤖 Analizando chunk {idx:03d} (len={len(buffer):,} chars) con {MODEL}…")
            prompt = build_prompt(buffer, idx)
            out_text = call_openai_chunk_text(client, MODEL, prompt)

            chunk_out = os.path.join(OUTDIR, f"api_chunk_{idx:03d}.txt")
            with open(chunk_out, "w", encoding="utf-8") as w:
                w.write(out_text or "")

            with open(api_index_path, "a", encoding="utf-8") as idxf:
                idxf.write(f"{idx}\t{len(buffer)}\t{chunk_out}\n")

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
    # LOCAL (regex)
    # ===========
    print("\n🔍 Analizando en local (regex)…")
    with open(SQL_FILE, "r", encoding="utf-8", errors="ignore") as f_all:
        full_text = f_all.read()

    schema = parse_schema_local(full_text)
    local_md_path = os.path.join(OUTDIR, "analysis_local.md")
    write_local_markdown(schema, local_md_path)
    print(f"📘 Resultado local: {local_md_path}")

    print("\n✅ Listo. Compara `analysis_api_combined.txt` con `analysis_local.md`.")
    print("   Índice de chunks (API):", api_index_path)

if __name__ == "__main__":
    main()
