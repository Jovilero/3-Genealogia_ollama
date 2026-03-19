import math
import logging
import sys
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from lib.ollama_client import OllamaClient

def main():
    outdir = Path("data/output_optimized")
    sql_file = Path("data/arxv_DB.txt")
    model = "qwen3:30b"
    workers = 3
    chunk_chars = 100_000

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logging.info("♻️ Reanudando GRAN ANALISIS (Sin filtrado)")

    if not sql_file.exists():
        logging.error("No se encuentra el SQL")
        return

    text = sql_file.read_text(encoding="utf-8", errors="ignore")
    total_len = len(text)
    parts = math.ceil(total_len / chunk_chars)
    
    # Detectar el último chunk procesado
    processed_indices = []
    for f in outdir.glob("api_chunk_*.txt"):
        try:
            # Extraer número del nombre api_chunk_NNN.txt
            idx = int(re.search(r"chunk_(\d+)", f.name).group(1))
            processed_indices.append(idx)
        except: continue
    
    last_idx = max(processed_indices) if processed_indices else 0
    logging.info(f"📊 Detectados {len(processed_indices)} chunks. El último es el {last_idx}.")

    tasks = []
    # Solo añadimos tareas que sean MAYORES que el último procesado para evitar repetir basura antigua
    for i in range(parts):
        idx = i + 1
        if idx > last_idx:
            tasks.append((idx, text[i*chunk_chars : (i+1)*chunk_chars]))

    logging.info(f"Pendientes: {len(tasks)} de {parts} totales.")
    
    client = OllamaClient(model=model)
    
    def process_chunk(idx, content):
        logging.info(f"🧠 Chunk {idx}...")
        try:
            res = client.call_generate(f"Analiza este SQL:\n{content}")
            (outdir / f"api_chunk_{idx:03d}.txt").write_text(res, encoding="utf-8")
            return idx
        except Exception as e:
            logging.error(f"Error {idx}: {e}")
            return None

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_chunk, idx, t): idx for idx, t in tasks}
        for f in as_completed(futures):
            res = f.result()
            if res: logging.info(f"✅ Chunk {res} OK")

if __name__ == "__main__":
    main()
