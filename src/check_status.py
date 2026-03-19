"""
check_status.py — Diagnóstico del estado del análisis de la BD Genealógica.

Uso:
    python check_status.py [--outdir PATH] [--sql PATH]

Muestra:
 - Chunks presentes y huecos
 - Porcentaje de completitud estimado
 - Tamaño total del análisis generado
"""
import re
import sys
from pathlib import Path

def get_status(outdir: Path) -> dict:
    """Return a dictionary with diagnostic information for the given output directory.
    Mirrors the logic previously printed in main().
    """
    # Verify directory exists
    if not outdir.exists():
        raise FileNotFoundError(f"Output directory does not exist: {outdir}")

    # Count chunk files and detect gaps
    chunk_files = list(outdir.glob("api_chunk_*.txt"))
    chunk_indices = []
    for f in chunk_files:
        m = re.search(r"chunk_(\d+)", f.name)
        if m:
            chunk_indices.append(int(m.group(1)))
    chunk_indices.sort()
    total_found = len(chunk_indices)
    if total_found == 0:
        return {"chunks": 0, "gaps": [], "size_mb": 0.0}
    max_idx = max(chunk_indices)
    min_idx = min(chunk_indices)
    expected_set = set(range(min_idx, max_idx + 1))
    found_set = set(chunk_indices)
    gaps = sorted(expected_set - found_set)

    # Total size of individual chunks
    total_size = sum(f.stat().st_size for f in chunk_files)
    size_mb = total_size / 1_048_576

    return {
        "min_idx": min_idx,
        "max_idx": max_idx,
        "total_chunks": total_found,
        "gaps": gaps,
        "size_mb": size_mb,
        "files": {fname: (outdir / fname).exists() for fname in ["analysis_local.md", "database_documentation.md", "final_report.md", "process.log", "skeleton.sql"]}
    }

def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Diagnóstico del estado del análisis")
    parser.add_argument("--outdir", type=Path, default=Path("data/output_optimized"),
                        help="Carpeta de salida del análisis")
    parser.add_argument("--sql", type=Path, default=Path("data/arxv_DB.txt"),
                        help="Archivo SQL original para calcular totales")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
    args = parser.parse_args()

    try:
        status_data = get_status(args.outdir)
    except FileNotFoundError as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"❌ {e}")
        sys.exit(1)

    if args.json:
        # Completar datos para JSON similar al print
        if args.sql.exists():
            status_data["sql_size_mb"] = args.sql.stat().st_size / 1_048_576
            status_data["estimated_total_chunks"] = int(args.sql.stat().st_size / 100_000) + 1
            status_data["percentage"] = min(100.0, 100 * status_data["total_chunks"] / status_data["estimated_total_chunks"])
        print(json.dumps(status_data, indent=2))
        return

    print("=" * 60)
    print("  🔍 DIAGNÓSTICO - GENEALOGIA OLLAMA")
    print("=" * 60)

    # --- Verificar existencia del outdir ---
    if not args.outdir.exists():
        print(f"❌ No existe el directorio: {args.outdir}")
        sys.exit(1)

    # --- Contar chunks ---
    chunk_files = list(args.outdir.glob("api_chunk_*.txt"))
    chunk_indices = []
    for f in chunk_files:
        m = re.search(r"chunk_(\d+)", f.name)
        if m:
            chunk_indices.append(int(m.group(1)))

    chunk_indices.sort()
    total_found = len(chunk_indices)

    if total_found == 0:
        print("⚠️  No se encontraron chunks de análisis.")
        return

    max_idx = max(chunk_indices)
    min_idx = min(chunk_indices)
    expected_set = set(range(min_idx, max_idx + 1))
    found_set = set(chunk_indices)
    gaps = sorted(expected_set - found_set)

    print(f"\n📁 Directorio: {args.outdir.resolve()}")
    print(f"\n📊 CHUNKS:")
    print(f"   - Rango detectado  : {min_idx} → {max_idx}")
    print(f"   - Total presentes  : {total_found:,}")
    print(f"   - Huecos detectados: {len(gaps)}")
    if gaps and len(gaps) <= 20:
        print(f"   - Huecos           : {gaps}")
    elif gaps:
        print(f"   - Primeros huecos  : {gaps[:10]} ...")

    # --- Tamaño total de salida ---
    total_size = sum(f.stat().st_size for f in chunk_files)
    combined = args.outdir / "analysis_ollama_combined.txt"
    combined_size = combined.stat().st_size if combined.exists() else 0

    print(f"\n💾 TAMAÑO DEL ANÁLISIS:")
    print(f"   - Chunks individuales : {total_size / 1_048_576:.1f} MB")
    if combined.exists():
        print(f"   - Fichero combinado   : {combined_size / 1_048_576:.1f} MB")

    # --- Ficheros de metadatos ---
    print(f"\n📄 FICHEROS DE SOPORTE:")
    for fname in ["analysis_local.md", "database_documentation.md",
                  "final_report.md", "process.log", "skeleton.sql"]:
        p = args.outdir / fname
        status = f"✅ ({p.stat().st_size / 1024:.0f} KB)" if p.exists() else "❌ No existe"
        print(f"   - {fname:<30} {status}")

    # --- Estimación de completitud ---
    if args.sql.exists():
        sql_size_mb = args.sql.stat().st_size / 1_048_576
        # ~100K chars por chunk, ~1 byte per char → rough estimate
        chunk_size_chars = 100_000
        estimated_total_chunks = int(args.sql.stat().st_size / chunk_size_chars) + 1
        pct = min(100.0, 100 * total_found / estimated_total_chunks)
        print(f"\n📈 COMPLETITUD (estimada):")
        print(f"   - Tamaño SQL original: {sql_size_mb:.0f} MB")
        print(f"   - Chunks estimados total: {estimated_total_chunks:,}")
        print(f"   - Chunks completados    : {total_found:,}")
        print(f"   - Porcentaje            : {pct:.1f}%")

        if pct >= 99:
            print("\n✅ El análisis parece COMPLETO. No es necesario reanudar.")
        elif pct >= 80:
            remaining = estimated_total_chunks - total_found
            print(f"\n⚠️  Faltan ~{remaining:,} chunks. Puedes continuar con resume_full_run.py")
        else:
            print(f"\n🔄 El análisis está incompleto. Ejecuta resume_full_run.py para continuar.")
    else:
        print(f"\n⚠️  No se encontró {args.sql} — no se puede calcular completitud.")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
