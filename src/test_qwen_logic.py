import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from lib.ollama_client import OllamaClient

def main():
    client = OllamaClient(model="qwen3:30b")
    
    outdir = Path("data/output_optimized")
    schema_context = (outdir / "analysis_local.md").read_text(encoding='utf-8')
    
    system_prompt = (
        "Eres un historiador experto y un administrador de bases de datos. "
        "Estás ayudando a analizar una base de datos de registros genealógicos sacramentales (siglos XVII-XVIII) de Valencia.\n\n"
        f"--- ESQUEMA TÉCNICO ---\n{schema_context}\n\n"
        "INSTRUCCIONES:\n"
        "- Responde directamente, con un tono profesional e histórico.\n"
        "- Si te piden código SQL, proporciónalo en bloques Markdown basándote estrictamente en el esquema.\n"
    )
    
    queries = [
        "¿Cómo se relacionan las tablas DatosPersonales y Personas? Quiero saber cómo encontrar a los padres de un bautizado.",
        "¿Puedes darme una consulta SQL para buscar a todas las personas nacidas en 1650?"
    ]
    
    print("\n" + "="*50)
    for q in queries:
        print(f"\nPREGUNTA:\n{q}")
        prompt = f"{system_prompt}\n\AHORA RESPONDE LA SIGUIENTE PREGUNTA:\nUSUARIO: {q}\nASISTENTE:\n"
        resp = client.call_generate(prompt).strip()
        print(f"\nRESPUESTA AI:\n{resp}")
        print("-" * 50)

if __name__ == "__main__":
    main()
