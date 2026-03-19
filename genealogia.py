import sys
import subprocess
from pathlib import Path

def print_help():
    print("=====================================================")
    print(" 🧬🤖 GENEALOGIA OLLAMA - Interfaz Unificada")
    print("=====================================================")
    print("Uso: python genealogia.py <comando> [opciones]\n")
    print("Comandos disponibles:")
    print("  run     Ejecuta el análisis optimizado de la base de datos.")
    print("          Ej: python genealogia.py run --sql ruta/db.sql --outdir data/output")
    print("  status  Muestra el estado/progreso del análisis.")
    print("          Ej: python genealogia.py status --outdir data/output")
    print("  report  Genera el informe Markdown consolidado final.")
    print("          Ej: python genealogia.py report --outdir data/output")
    print("  web     Ejecuta la Interfaz Gráfica Web interactiva (Streamlit).")
    print("          Ej: python genealogia.py web")
    print("  chat    Inicia la consulta interactiva con el modelo IA.")
    print("          Ej: python genealogia.py chat --outdir data/output --report\n")
    print("Usa 'python genealogia.py <comando> -h' para ver las opciones específicas de cada comando.")
    print("=====================================================")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print_help()
        sys.exit(0)

    command = sys.argv[1].lower()
    args = sys.argv[2:]

    script_map = {
        "run": "src/main_optimized.py",
        "status": "src/check_status.py",
        "report": "src/generate_report.py",
        "chat": "src/query_db.py",
        "web": "src/ui.py",
        # Aliases
        "analyze": "src/main_optimized.py",
        "query": "src/query_db.py",
        "ui": "src/ui.py"
    }

    if command not in script_map:
        print(f"❌ Comando desconocido: '{command}'")
        print_help()
        sys.exit(1)

    # El script que vamos a ejecutar
    script_path = Path(__file__).parent / script_map[command]
    
    if not script_path.exists():
        print(f"❌ Error: No se encuentra el script subyacente '{script_path}'.")
        sys.exit(1)

    # Si es el comando web, inyectar "streamlit run"
    execute_cmd = [sys.executable, str(script_path)] + args
    if command in ["web", "ui"]:
        # Se requiere streamlit instalado
        execute_cmd = [sys.executable, "-m", "streamlit", "run", str(script_path)] + args

    # Executar pasando el control total
    try:
        result = subprocess.run(execute_cmd)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n[Interrumpido por el usuario]")
        sys.exit(130)

if __name__ == "__main__":
    main()
