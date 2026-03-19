def execute_query(sql: str) -> list[dict]:
    """Execute a SQL query against the genealogical database.
    Currently this is a stub; in production it would connect to the DB.
    Returns a list of row dictionaries.
    """
    # Placeholder implementation – raise NotImplementedError to indicate missing DB.
    raise NotImplementedError("Database execution not implemented in this context.")

import sys
from pathlib import Path
from lib.ollama_client import OllamaClient

def print_help():
    print("\n💡 Comandos Disponibles:")
    print("   !schema   - Muestra el esquema técnico de la base de datos")
    print("   !tablas   - Lista las tablas disponibles")
    print("   !historia - Muestra el resumen ejecutivo (si existe)")
    print("   !borrar   - Borra el historial de la conversación actual")
    print("   !ayuda    - Muestra este mensaje")
    print("   salir     - Termina la sesión\n")

def main():
    parser = argparse.ArgumentParser(description="Consulta interactiva de la base de datos genealógica")
    parser.add_argument("--outdir", type=Path, required=True, help="Carpeta donde están los resultados del análisis")
    parser.add_argument("--model", default="qwen3:30b", help="Modelo Ollama a usar")
    parser.add_argument("--report", action="store_true", help="Cargar también el informe final consolidado como contexto")
    args = parser.parse_args()

    local_md = args.outdir / "analysis_local.md"
    combined_txt = args.outdir / "analysis_ollama_combined.txt"
    final_report = args.outdir / "final_report.md"
    doc_md = args.outdir / "database_documentation.md"

    if not local_md.exists():
        print(f"❌ Error: No se encuentra el esquema base en {local_md}")
        return

    print("📖 Cargando contexto base...")
    schema_context = local_md.read_text(encoding='utf-8')
    
    # Construir el contexto del sistema
    system_context = (
        "Eres un historiador experto y un administrador de bases de datos. "
        "Estás ayudando a analizar una base de datos de registros genealógicos sacramentales (siglos XVII-XVIII) de Valencia.\n\n"
        f"--- ESQUEMA TÉCNICO ---\n{schema_context}\n\n"
    )

    if args.report and final_report.exists():
        print("📑 Cargando informe final como contexto extendido...")
        report_text = final_report.read_text(encoding='utf-8')
        # Extraer solo el resumen ejecutivo e info valiosa para no desbordar el contexto
        system_context += f"--- CONTEXTO HISTÓRICO Y RESUMEN ---\n{report_text[:10000]}\n\n"
    elif combined_txt.exists():
        print("📑 Cargando muestra de análisis combinado...")
        sample_analysis = combined_txt.read_text(encoding='utf-8')[:15000] # Limitar a 15K chars
        system_context += f"--- OBSERVACIONES DEL ANÁLISIS ---\n{sample_analysis}\n\n"

    system_context += (
        "INSTRUCCIONES:\n"
        "- Responde directamente, con un tono profesional e histórico.\n"
        "- Si te piden código SQL, proporciónalo en bloques Markdown basándote estrictamente en el esquema.\n"
        "- Usa el historial de la conversación para dar respuestas más precisas y contextuales."
    )

    client = OllamaClient(model=args.model)
    
    # Historial de conversación para model API (si usáramos chat api de Ollama, 
    # pero aquí simularemos añadiendo al prompt para call_generate)
    conversation_history = []
    MAX_HISTORY = 6  # Mantener las últimas 6 interacciones (3 pares Q&A)

    print("\n" + "="*50)
    print("🏛️  CONSULTA GENEALÓGICA INTERACTIVA")
    print("="*50)
    print(f"✅ Listo. Conectado al modelo {args.model}.")
    print("Escribe '!ayuda' para ver comandos especiales o 'salir' para terminar.\n")

    while True:
        try:
            query = input("❓ Pregunta: ").strip()
            q_lower = query.lower()
            
            if q_lower in ["salir", "exit", "quit"]:
                break
            if not query:
                continue
                
            # --- Comandos Especiales ---
            if q_lower == "!ayuda":
                print_help()
                continue
            elif q_lower == "!schema":
                print(f"\n📊 ESQUEMA:\n{schema_context}\n")
                continue
            elif q_lower == "!tablas":
                print("\n📋 TABLAS DETECTADAS: DatosPersonales, Personas, Registros, Sacramentos\n")
                continue
            elif q_lower == "!historia":
                if doc_md.exists():
                    print("\n📜 RESUMEN DEL DOCUMENTO:\n" + doc_md.read_text(encoding='utf-8')[:1000] + "...\n")
                else:
                    print("\n❌ Documentación no disponible.\n")
                continue
            elif q_lower == "!borrar":
                conversation_history.clear()
                print("\n🧹 Historial de conversación borrado.\n")
                continue

            # --- Generar Prompt con Historial ---
            history_text = ""
            if conversation_history:
                history_text = "--- HISTORIAL DE CONVERSACIÓN RECIENTE ---\n"
                for i, msg in enumerate(conversation_history):
                    role = "USUARIO" if i % 2 == 0 else "ASISTENTE"
                    history_text += f"{role}: {msg}\n\n"
                history_text += "---------------------------------------\n\n"

            prompt = f"{system_context}\n\n{history_text}AHORA RESPONDE LA SIGUIENTE PREGUNTA:\nUSUARIO: {query}\nASISTENTE:\n"

            print("🤖 Pensando...")
            response = client.call_generate(prompt).strip()
            
            print(f"\n📝 Respuesta:\n{response}\n")
            print("-" * 50)
            
            # Actualizar historial
            conversation_history.append(query)
            conversation_history.append(response)
            
            # Recortar historial si excede el máximo
            if len(conversation_history) > MAX_HISTORY * 2:
                conversation_history = conversation_history[-(MAX_HISTORY * 2):]

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Error al consultar: {e}")

if __name__ == "__main__":
    main()
