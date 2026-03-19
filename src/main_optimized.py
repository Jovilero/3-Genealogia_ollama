"""
main_optimized.py — Motor principal de análisis paralelo.

Este script se encarga de:
1. Generar un 'skeleton' del SQL (sin datos masivos).
2. Realizar un análisis estructural local (regex).
3. Fragmentar el SQL en chunks y analizarlos en paralelo usando Ollama.
4. Consolidar el análisis en ficheros Markdown y TXT.
"""
import argparse
import logging
import math
import sys
from pathlib import Path
from typing import Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from lib.ollama_client import OllamaClient
from lib.sql_processor import SQLProcessor
CHUNK_CHARS = 100_000 # Más pequeño para paralelo
DEFAULT_WORKERS = 3

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

def get_processed_chunks(outdir: Path) -> Set[int]:
    """Detecta qué chunks ya existen en disco."""
    processed = set()
    for f in outdir.glob("api_chunk_*.txt"):
        try:
            # api_chunk_001.txt -> 1
            idx = int(f.name.split('_')[-1].split('.')[0])
            processed.add(idx)
        except: continue
    return processed

def process_chunk(chunk_idx: int, chunk_text: str, client: OllamaClient, outdir: Path):
    """Tarea individual para un hilo."""
    logging.info(f"🧠 Analizando chunk {chunk_idx} ({len(chunk_text):,} chars)...")
    prompt = (
        "Analiza el siguiente fragmento SQL y extrae las tablas, relaciones y propósito.\n"
        f"--- CHUNK {chunk_idx} ---\n```sql\n{chunk_text}\n```"
    )
    try:
        result = client.call_generate(prompt)
        (outdir / f"api_chunk_{chunk_idx:03d}.txt").write_text(result, encoding="utf-8")
        return chunk_idx
    except Exception as e:
        logging.error(f"Fallo en chunk {chunk_idx}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Analizador SQL Modular y Optimizado")
    parser.add_argument("--sql", type=Path, required=True, help="Ruta al dump .sql")
    parser.add_argument("--outdir", type=Path, required=True, help="Carpeta de salida")
    parser.add_argument("--model", default="qwen3:30b", help="Modelo Ollama")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Hilos paralelos")
    parser.add_argument("--no-resume", action="store_true", help="Desactiva reanudación")
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    setup_logging(args.outdir)

    logging.info("🚀 Iniciando GENEALOGIA OPTIMIZADA")
    
    if not args.sql.exists():
        logging.error(f"Fichero no encontrado: {args.sql}")
        return

    # 1. Generar Esqueleto (SKELETON)
    skeleton_path = args.outdir / "skeleton.sql"
    processor = SQLProcessor(rows_to_keep=5)
    processor.generate_skeleton(str(args.sql), str(skeleton_path))

    # 2. Análisis Local
    logging.info("🔍 Análisis Local...")
    skeleton_text = skeleton_path.read_text(encoding="utf-8", errors="ignore")
    schema = processor.parse_schema_local(skeleton_text)
    
    local_md = ["# Esquema (Skeleton Analysis)\n"]
    for t, data in schema.items():
        local_md.append(f"## {t}\n**PK**: {', '.join(data['primary_key']) or '-'}\n\n| Col | Tipo |\n|---|---|\n")
        local_md.append("".join([f"| {c['name']} | {c['type']} |\n" for c in data["columns"]]))
        local_md.append("\n")
    (args.outdir / "analysis_local.md").write_text("".join(local_md), encoding="utf-8")

    # 3. Análisis Ollama Paralelo
    client = OllamaClient(model=args.model)
    total_len = len(skeleton_text)
    parts = math.ceil(total_len / CHUNK_CHARS)
    processed = set() if args.no_resume else get_processed_chunks(args.outdir)

    tasks_to_run = []
    for i in range(parts):
        idx = i + 1
        if idx in processed: continue
        
        start = i * CHUNK_CHARS
        end = min((i + 1) * CHUNK_CHARS, total_len)
        tasks_to_run.append((idx, skeleton_text[start:end]))

    logging.info(f"🤖 Procesando {len(tasks_to_run)} chunks en paralelo con {args.workers} workers...")
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_chunk, idx, text, client, args.outdir): idx for idx, text in tasks_to_run}
        for future in as_completed(futures):
            res = future.result()
            if res: logging.info(f"✅ Chunk {res} completado.")

    # 4. Combinación
    logging.info("Finalizando...")
    chunk_files = sorted(args.outdir.glob("api_chunk_*.txt"))
    with open(args.outdir / "analysis_ollama_combined.txt", "w", encoding="utf-8") as f:
        for cf in chunk_files:
            f.write(f"\n\n{'='*20} {cf.name} {'='*20}\n\n")
            f.write(cf.read_text(encoding="utf-8"))

    logging.info(f"✨ Proceso completado. Revisa {args.outdir}")

if __name__ == "__main__":
    main()
