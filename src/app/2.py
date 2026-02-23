#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Analiza un .sql con dos métodos en una sola ejecución:

A) API (gpt-4o-mini) SIN archivos adjuntos: envía el .sql por CHUNKS como input_text.
   - Guarda cada respuesta de chunk en outdir/api_chunk_###.txt
   - Mantiene índice outdir/api_index.tsv
   - Reanudación con --resume

B) Local (regex): extrae tablas/columnas/PK/FK → outdir/analysis_local.md

Uso:
  export OPENAI_API_KEY="<SU_API_KEY_AQUI>"
  python main.py --sql /ruta/arxv_DB.txt --outdir ./data/output
  # reanudar si hubo corte:
  python main.py --sql /ruta/arxv_DB.txt --outdir ./data/output --resume
"""

import argparse, os, re, time
from openai import OpenAI

# Tamaño de chunk en caracteres (texto). Ajusta según tu caso.
DEFAULT_CHUNK_CHARS = 200_000
MAX_RETRIES = 3
SLEEP_BASE = 2  # backoff base

# ---------------------------
# LOCAL: análisis de esquema con regex
# ---------------------------
def parse_schema_local(sql_text: str):
    """Extrae tablas/columnas/PK/FK de forma sencilla (regex)."""
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
        "Si el fragmento está incompleto, indica límites y referencias cruzadas.\n\n"
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
        except Exception as e:
            if attempt == MAX_RETRIES:
                raise
            time.sleep(SLEEP_BASE * attempt)

# ---------------------------
# UTIL: reanudar
# ---------------------------
def detect_completed_chunks(outdir: str):
    """Devuelve set de índices (int) de chunks ya guardados como api_chunk_###.txt"""
    done = set()
    if not os.path.isdir(outdir):
        return done
    for name in os.listdir(outdir):
        m = re.match(r"api_chunk_(\d{3})\.txt$", name)
        if m:
            done.add(int(m.group(1)))
    return done

def ensure_outdir(outdir: str):
    os.makedirs(outdir, exist_ok=True)

# ---------------------------
# MAIN
# ---------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sql", "--fichero_datos", dest="sql", required=True,
                    help="Ruta al dump .sql (puede no tener extensión)")
    ap.add_argument("--outdir", required=True, help="Carpeta de salida")
    ap.add_argument("--model", default="gpt-4o-mini", help="Modelo para la API (por defecto: gpt-4o-mini)")
    ap.add_argument("--chunk-chars", type=int, default=DEFAULT_CHUNK_CHARS,
                    help=f"Tamaño de chunk en caracteres (por defecto: {DEFAULT_CHUNK_CHARS})")
    ap.add_argument("--resume", action="store_true", help="Reanudar: no reprocesar chunks ya guardados")
    args = ap.parse_args()

    ensure_outdir(args.outdir)
    client = OpenAI()

    # ===========
    # Carga archivo en streaming para no romper RAM
    # ===========
    print(f"\n📤 Enviando por chunks (TEXTO) a la API: {args.sql}")
    api_index_path = os.path.join(args.outdir, "api_index.tsv")
    combined_path = os.path.join(args.outdir, "analysis_api_combined.txt")

    done = detect_completed_chunks(args.outdir) if args.resume else set()
    next_idx = 1

    # Procesar por trozos de caracteres
    with open(args.sql, "r", encoding="utf-8", errors="ignore") as f_in:
        buffer = f_in.read(args.chunk_chars)
        while buffer:
            idx = next_idx
            next_idx += 1

            # si reanudamos y ya existe el archivo de este chunk, saltamos
            if args.resume and idx in done:
                print(f"⏭️  Chunk {idx:03d} ya existe, salto.")
                buffer = f_in.read(args.chunk_chars)
                continue

            print(f"🤖 Analizando chunk {idx:03d} (len={len(buffer):,} chars) con {args.model}…")
            prompt = build_prompt(buffer, idx)
            out_text = call_openai_chunk_text(client, args.model, prompt)

            # guardar salida de chunk
            chunk_out = os.path.join(args.outdir, f"api_chunk_{idx:03d}.txt")
            with open(chunk_out, "w", encoding="utf-8") as w:
                w.write(out_text or "")

            # apéndice índice
            with open(api_index_path, "a", encoding="utf-8") as idxf:
                idxf.write(f"{idx}\t{len(buffer)}\t{chunk_out}\n")

            # siguiente chunk
            buffer = f_in.read(args.chunk_chars)

    # Combinar todo en un solo archivo (ordenado)
    chunk_files = sorted(
        [fn for fn in os.listdir(args.outdir) if re.match(r"api_chunk_\d{3}\.txt$", fn)]
    )
    with open(combined_path, "w", encoding="utf-8") as out_all:
        for fn in chunk_files:
            out_all.write(f"===== {fn} =====\n")
            with open(os.path.join(args.outdir, fn), "r", encoding="utf-8", errors="ignore") as cf:
                out_all.write(cf.read() + "\n\n")
    print(f"📊 Resultado API combinado: {combined_path}")

    # ===========
    # Opción B: análisis local del SQL completo (conviene leerlo una vez más)
    # ===========
    print("\n🔍 Analizando en local (regex)…")
    with open(args.sql, "r", encoding="utf-8", errors="ignore") as f_all:
        full_text = f_all.read()

    schema = parse_schema_local(full_text)
    local_md_path = os.path.join(args.outdir, "analysis_local.md")
    write_local_markdown(schema, local_md_path)
    print(f"📘 Resultado local: {local_md_path}")

    print("\n✅ Listo. Compara `analysis_api_combined.txt` con `analysis_local.md`.")
    print("   Índice de chunks (API):", api_index_path)

if __name__ == "__main__":
    main()

#ejecución:# Dentro de tu venv
"""
export OPENAI_API_KEY="<SU_API_KEY_AQUI>"

/mnt/a/3-Ocio/4-Programacion/1-RepositoriosGIT/2-Genealogia_gpt_api/.venv/bin/python \
  /mnt/a/3-Ocio/4-Programacion/1-RepositoriosGIT/2-Genealogia_gpt_api/src/main.py \
  --sql /mnt/a/3-Ocio/4-Programacion/1-RepositoriosGIT/2-Genealogia_gpt_api/data/arxv_DB.txt \
  --outdir /mnt/a/3-Ocio/4-Programacion/1-RepositoriosGIT/2-Genealogia_gpt_api/data/output \
  --model gpt-4o-mini \
  --chunk-chars 200000 2>&1 | tee /mnt/a/3-Ocio/4-Programacion/1-RepositoriosGIT/2-Genealogia_gpt_api/run_$(date +%Y%m%d_%H%M).log
"""
#Si rompe:
"""
/mnt/a/.../.venv/bin/python /mnt/a/.../src/main.py \
--sql /mnt/a/.../data/arxv_DB.txt \
--outdir /mnt/a/.../data/output \
--resume 2>&1 | tee -a /mnt/a/.../run_resume_$(date +%Y%m%d_%H%M).log

"""