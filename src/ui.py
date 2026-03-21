import streamlit as st
from pathlib import Path
import sys
import os
import time

# Añadir el directorio raíz al path temporalmente para poder importar lib de src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.lib.ollama_client import OllamaClient
from src.lib.sql_processor import SQLProcessor
from src.lib.db_executor import DBExecutor
import re
import io
import pandas as pd
from backup_db import run_backup

def load_text(path: Path) -> str:
    """Carga texto desde un archivo de forma segura."""
    if path.exists():
        return path.read_text(encoding='utf-8')
    return "*No disponible.*"

def load_context(outdir: Path, include_report: bool) -> str:
    """Construye el contexto del prompt del sistema para el LLM."""
    schema_path = outdir / "analysis_local.md"
    schema_text = load_text(schema_path)
    
    context = (
        "Eres un historiador experto y un administrador de bases de datos. "
        "Estás ayudando a analizar una base de datos de registros genealógicos sacramentales (siglos XVII-XVIII).\n\n"
        f"--- ESQUEMA TÉCNICO ---\n{schema_text}\n\n"
    )

    if include_report:
        report_path = outdir / "final_report.md"
        report_text = load_text(report_path)
        if report_text != "*No disponible.*":
            context += f"--- CONTEXTO HISTÓRICO Y RESUMEN ---\n{report_text[:10000]}\n\n"
            
    context += (
        "INSTRUCCIONES:\n"
        "- Responde directamente, con un tono profesional e histórico.\n"
        "- Si te piden código SQL, proporciónalo en bloques Markdown basándote estrictamente en el esquema."
    )
    return context

def build_prompt_with_history(system_prompt: str, history: list, new_query: str) -> str:
    """Construye el prompt completo inyectando el historial reciente."""
    max_history = 6 # pares (user, asis) x 2
    recent_history = history[-max_history:] if len(history) > max_history else history
    
    prompt = system_prompt + "\n\n"
    if recent_history:
        prompt += "--- HISTORIAL RECIENTE ---\n"
        for msg in recent_history:
            role = "USUARIO" if msg["role"] == "user" else "ASISTENTE"
            prompt += f"{role}: {msg['content']}\n\n"
            
    prompt += f"AHORA RESPONDE:\nUSUARIO: {new_query}\nASISTENTE:\n"
    return prompt

def main():
    st.set_page_config(page_title="Genealogia Ollama", page_icon="🧬", layout="wide")
    
    st.sidebar.title("Configuración ⚙️")
    outdir_input = st.sidebar.text_input("Directorio de Análisis", value="./data/output_optimized")
    model_input = st.sidebar.text_input("Modelo Ollama", value="qwen3:30b")
    num_ctx_input = st.sidebar.number_input("Ventana de Contexto (Tokens)", value=8192, step=1024, help="Aumentar permite leer esquemas más largos pero requiere más memoria (RAM/VRAM). 8192 es el máximo sugerido para tu PC de 32GB.")
    include_report = st.sidebar.checkbox("Incluir Informe en Contexto", value=True)

    
    if st.sidebar.button("Borrar Historial de Chat"):
        st.session_state.messages = []
        st.session_state.sql_messages = []
        st.rerun()

    def get_chat_markdown(messages):
        md = "# Historial de Chat IA (Genealogia)\n\n"
        for msg in messages:
            role = "🗣️ **USUARIO**" if msg["role"] == "user" else "🤖 **ASISTENTE**"
            md += f"{role}\n{msg['content']}\n\n---\n\n"
        return md

    if st.session_state.get("messages"):
        st.sidebar.download_button(
            label="📄 Descargar Chat Histórico (.md)",
            data=get_chat_markdown(st.session_state.messages),
            file_name="chat_genealogia.md",
            mime="text/markdown"
        )

    outdir = Path(outdir_input)
    
    st.title("🧬🤖 Genealogia Ollama")
    
    tab_chat, tab_sql, tab_schema, tab_report, tab_admin = st.tabs(["💬 Autómata Histórico", "💻 Experto SQL", "📊 Grafo de Esquema", "📑 Informe Ejecutivo", "🛠️ Administración"])
    
    # Init session state para mensajeria
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "sql_messages" not in st.session_state:
        st.session_state.sql_messages = []
    if "db_executor" not in st.session_state:
        st.session_state.db_executor = DBExecutor()

    # --- TAB: CHAT HISTÓRICO ---
    with tab_chat:
        st.caption(f"Conectado a: `{model_input}` | Datos: `{outdir}`")
        
        # Mostrar historial
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        # Input del usuario
        if prompt := st.chat_input("Pregunta sobre la base de datos..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner("Consultando los archivos y pensando..."):
                    context = load_context(outdir, include_report)
                    full_prompt = build_prompt_with_history(context, st.session_state.messages[:-1], prompt)
                    
                    try:
                        start_time = time.time()
                        # Temperatura normal para chat humano
                        client = OllamaClient(model=model_input, num_ctx=num_ctx_input, temperature=0.7)
                        bar = st.progress(0, text="Llamando a Ollama...")

                        for i in range(1, 101, 10):
                            time.sleep(0.05)
                            bar.progress(i)
                        
                        response = client.call_generate(full_prompt)
                        bar.empty()
                        total_time = time.time() - start_time
                        
                        st.markdown(response)
                        st.caption(f"⏱️ **Métricas:** Tiempo de respuesta: `{total_time:.2f}s` | Modelo: `{model_input}`")
                        
                        st.session_state.messages.append({"role": "assistant", "content": response})

                    except Exception as e:
                        error_str = str(e)
                        if "Max retries" in error_str or "ConnectionRefused" in error_str or "10061" in error_str:
                            st.error(f"🔌 **Ollama no está disponible.**\n\nParece que el servidor local de Ollama no está en ejecución. Por favor, asegúrate de abrir la aplicación de Ollama en tu equipo antes de usar el chat.")
                        else:
                            st.error(f"❌ **Error inesperado:** {e}")

    # --- TAB: EXPERTO SQL ---
    with tab_sql:
        st.caption("Asistente IA especializado estrictamente en generar consultas SQL basadas en tu esquema.")
        
        for msg in st.session_state.sql_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        if prompt_sql := st.chat_input("Escribe tu petición (Ej: 'Muestra todos los sacramentos de 1750')..."):
            st.session_state.sql_messages.append({"role": "user", "content": prompt_sql})
            with st.chat_message("user"):
                st.markdown(prompt_sql)
                
            with st.chat_message("assistant"):
                with st.spinner("Generando SQL y ejecutando en BD local..."):
                    schema_path = outdir / "analysis_local.md"
                    schema_text = load_text(schema_path)
                    
                    sql_context = (
                        "Eres un experto en bases de datos y SQL. Tu única tarea es devolver código SQL puro. "
                        "DEBES DEVOLVER SOLO CÓDIGO SQL dentro de un bloque ```sql ... ``` sin ninguna otra explicación o texto.\n\n"
                        f"--- ESQUEMA DE LA BASE DE DATOS ---\n{schema_text}"
                    )
                    
                    current_prompt = prompt_sql
                    history_slice = st.session_state.sql_messages[:-1]
                    max_retries = 3
                    
                    start_total_time = time.time()
                    
                    for attempt in range(max_retries):
                        full_prompt = build_prompt_with_history(sql_context, history_slice, current_prompt)
                        try:
                            llm_start = time.time()
                            # Temperatura 0.0 para ser matemáticamente determinista y escribir SQL sin inventos
                            client = OllamaClient(model=model_input, num_ctx=num_ctx_input, temperature=0.0)
                            response = client.call_generate(full_prompt)
                            llm_time = time.time() - llm_start

                            
                            # Renderizamos la respuesta en la UI
                            if attempt > 0:
                                st.markdown(f"**🔄 Auto-corrección (Intento {attempt+1}):**\n" + response)
                            else:
                                st.markdown(response)
                                
                            st.session_state.sql_messages.append({"role": "assistant", "content": response})
                            
                            # Extraer SQL y ejecutar
                            sql_match = re.search(r"```sql\s*(.*?)\s*```", response, re.DOTALL | re.IGNORECASE)
                            if sql_match:
                                sql_query = sql_match.group(1).strip()
                                df = st.session_state.db_executor.execute_to_df(sql_query)
                                
                                st.success("✅ Consulta ejecutada con éxito.")
                                
                                total_time = time.time() - start_total_time
                                with st.expander(f"📊 Métricas de Rendimiento ({model_input})"):
                                    st.markdown(f"- **⏱️ Tiempo Total Bucle:** `{total_time:.2f}s`\n"
                                                f"- **🧠 Tiempo Inferencia LLM (Última):** `{llm_time:.2f}s`\n"
                                                f"- **🔁 Reintentos Auto-curación:** `{attempt}`\n"
                                                f"- **📏 Longitud Respuesta:** `{len(response)} chars`")
                                                
                                st.dataframe(df, use_container_width=True)
                                
                                # --- Fase 16: Visualización Dinámica ---
                                if not df.empty and len(df) > 1:
                                    cols = df.columns.tolist()
                                    date_cols = [c for c in cols if any(k in c.lower() for k in ["fecha", "ano", "año"])]
                                    cat_cols = [c for c in cols if df[c].dtype == "object" and not any(k in c.lower() for k in ["fecha", "ano", "año", "notas"])]

                                    v_col1, v_col2 = st.columns(2)
                                    
                                    # Visualización Temporal
                                    with v_col1:
                                        if date_cols:
                                            d_col = date_cols[0]
                                            st.subheader("📈 Tendencia Temporal")
                                            # Limpiar fechas aproximadas (ej: 1750?) y agrupar
                                            temp_df = df.copy()
                                            temp_df[d_col] = temp_df[d_col].astype(str).str.extract(r"(\d{4})")
                                            temp_df = temp_df.dropna(subset=[d_col])
                                            if not temp_df.empty:
                                                chart_data = temp_df.groupby(d_col).size()
                                                st.line_chart(chart_data)
                                    
                                    # Visualización Categórica
                                    with v_col2:
                                        if cat_cols:
                                            c_col = cat_cols[0]
                                            st.subheader(f"📊 Top 10: {c_col}")
                                            cat_counts = df[c_col].value_counts().head(10)
                                            st.bar_chart(cat_counts)
                                
                                # --- Fase 12: Data Insights (Auto-Interpretación) ---

                                if not df.empty and "Resultado" not in df.columns:
                                    with st.spinner("La IA está interpretando los datos resultantes..."):
                                        df_csv = df.head(10).to_csv(index=False)
                                        insight_context = (
                                            "Eres un historiador experto en registros parroquiales genealógicos. "
                                            "El usuario ha ejecutado una consulta SQL y ha obtenido los siguientes datos en formato CSV de la base de datos:\n\n"
                                            f"```csv\n{df_csv}\n```\n\n"
                                            "El sistema también ha generado gráficos automáticos de tendencia o distribución si los datos lo permitían. "
                                            "Escribe un único párrafo corto (máximo 3 frases) analizando estos datos y mencionando posibles tendencias o patrones históricos que se observen. Sé directo y profesional."
                                        )

                                        insight_client = OllamaClient(model=model_input, num_ctx=num_ctx_input, temperature=0.7)
                                        insight_response = insight_client.call_generate(insight_context)
                                        
                                        st.info(f"💡 **Insight Histórico:**\n{insight_response}")
                                
                                # --- Fase 17: Exportación y Biografía ---
                                if not df.empty:
                                    st.divider()
                                    e_col1, e_col2 = st.columns(2)
                                    
                                    with e_col1:
                                        # Exportar a Excel
                                        output = io.BytesIO()
                                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                            df.to_excel(writer, index=False, sheet_name='Resultados')
                                        st.download_button(
                                            label="📥 Descargar Resultados (.xlsx)",
                                            data=output.getvalue(),
                                            file_name=f"consulta_{int(time.time())}.xlsx",
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                        )

                                    with e_col2:
                                        # Generar Biografía (si hay Datos Personales)
                                        if "nombre" in df.columns and "apellido1" in df.columns:
                                            if st.button("✨ Generar Narrativa Biográfica (IA)"):
                                                with st.spinner("La IA está redactando la historia de vida..."):
                                                    # Tomamos la primera fila como sujeto
                                                    sujeto = df.iloc[0].to_dict()
                                                    bio_prompt = (
                                                        "Eres un historiador novelista. A partir de estos datos técnicos de un registro genealógico, "
                                                        "escribe un relato biográfico fluido y evocador (máximo 150 palabras) sobre la vida de esta persona. "
                                                        "Incluye detalles de su profesión, familia y lugar si están disponibles.\n\n"
                                                        f"DATOS: {sujeto}"
                                                    )
                                                    bio_client = OllamaClient(model=model_input, num_ctx=num_ctx_input, temperature=0.8)
                                                    story = bio_client.call_generate(bio_prompt)
                                                    st.write("📜 **Relato Biográfico:**")
                                                    st.info(story)
                                
                                break # Éxito, salimos del bucle de auto-healing

                            else:
                                st.info("ℹ️ No se detectó código SQL puro (bloque ```sql) en la respuesta.")

                                break

                                
                        except Exception as e:
                            err_str = str(e)
                            if "Ollama" in err_str or "Max retries" in err_str:
                                st.error(f"❌ Error conectando a la Inteligencia Artificial: {err_str}")
                                break # Si falla la IA, no tiene sentido reintentar el auto-healing SQL
                            
                            st.error(f"⚠️ Error en Base de Datos: {err_str}")
                            
                            if attempt < max_retries - 1:
                                st.warning("Realizando auto-corrección mediante IA...")
                                current_prompt = f"El SQL falló con este error de base de datos:\n{err_str}\nPor favor, corrige la sintaxis de la consulta y devuelve únicamente un bloque ```sql ... ``` arreglado."
                                history_slice = st.session_state.sql_messages.copy()
                                st.session_state.sql_messages.append({"role": "user", "content": current_prompt})
                            else:
                                st.error("❌ Límite de auto-correcciones alcanzado. Verifica la consulta manualmente.")

    # --- TAB: SCHEMA ---
    with tab_schema:
        st.subheader("Esquema Entidad-Relación (ER)")
        skeleton_path = outdir / "skeleton.sql"
        if skeleton_path.exists():
            text = skeleton_path.read_text(encoding="utf-8", errors="ignore")
            schema_dict = SQLProcessor.parse_schema_local(text)
            mermaid_code = SQLProcessor.schema_to_mermaid(schema_dict)
            st.markdown(f"```mermaid\n{mermaid_code}\n```")
        else:
            st.info("No se encontró `skeleton.sql` para renderizar el grafo interactivo.")

        st.divider()
        st.subheader("Diccionario de Datos")
        if not (outdir / "analysis_local.md").exists():
            st.warning("No se encontró el archivo `analysis_local.md`. Ejecuta la extracción (run) primero.")
        else:
            st.markdown(load_text(outdir / "analysis_local.md"))

    # --- TAB: REPORT ---
    with tab_report:
        if not (outdir / "final_report.md").exists():
            st.warning("No se encontró el archivo `final_report.md`. Genera el informe (report) primero.")
        else:
            st.markdown(load_text(outdir / "final_report.md"))

    # --- TAB: ADMIN ---
    with tab_admin:
        st.header("🛠️ Panel de Administración y Seguridad")
        st.subheader("🏰 Bóveda de Backups")
        
        if st.button("🚀 Crear Copia de Seguridad Ahora"):
            with st.spinner("Ejecutando pg_dump en el servidor..."):
                success, result = run_backup()
                if success:
                    st.success(f"Archivo creado exitosamente: `{result}`")
                else:
                    st.error(f"Error en el backup: {result}")
        
        st.divider()
        st.subheader("📂 Archivos de Resguardo Locales")
        backup_dir = Path("backup")
        if backup_dir.exists():
            backups = sorted(list(backup_dir.glob("*.dump")), key=os.path.getmtime, reverse=True)
            if backups:
                for b in backups[:10]:
                    size_mb = os.path.getsize(b) / (1024*1024)
                    st.text(f"📄 {b.name} ({size_mb:.2f} MB)")
            else:
                st.info("No hay archivos de backup en la carpeta `/backup`.")
        else:
            st.info("Aún no se ha creado la carpeta de backups.")

if __name__ == "__main__":
    main()
