#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Detecta el tipo de fichero sin extensión.
- Comprueba cabeceras de texto
- Intenta adivinar si es SQL (CREATE/INSERT)
- Si está disponible, usa python-magic para tipo MIME real

Nota de mantenimiento:
- Este archivo actúa como referencia canónica para su copia homóloga en
    2-Genealogia_gpt_api/src/detectar_extension.py.
"""

import argparse
import os

def guess_type(path):
    # Leer primeras líneas como texto
    with open(path, "rb") as f:
        head = f.read(2048)  # primeros 2 KB
    try:
        text = head.decode("utf-8", errors="ignore")
    except Exception:
        return "Binario (no texto)"

    lowered = text.lower()
    if "create table" in lowered or "insert into" in lowered or "alter table" in lowered:
        return "SQL dump (texto con sentencias SQL)"
    if lowered.startswith("pk\x03\x04"):
        return "ZIP (binario comprimido)"
    if lowered.startswith("%pdf"):
        return "PDF"
    if lowered.startswith("{") or lowered.startswith("["):
        return "JSON (probable)"
    return "Texto (sin patrones SQL claros)"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="Ruta al fichero sin extensión")
    args = ap.parse_args()

    print(f"📂 Analizando: {args.file}")
    print(f"📏 Tamaño: {os.path.getsize(args.file)} bytes")

    tipo = guess_type(args.file)
    print(f"🔎 Tipo detectado: {tipo}")

    try:
        import magic  # python-magic opcional
        mime = magic.from_file(args.file, mime=True)
        print(f"📑 MIME (libmagic): {mime}")
    except ImportError:
        print("ℹ️  Instala 'python-magic' para detección MIME más precisa (pip install python-magic)")

if __name__ == "__main__":
    main()
