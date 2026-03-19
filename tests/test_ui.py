import pytest
from pathlib import Path
from src.ui import load_text, load_context, build_prompt_with_history

def test_load_text_missing_file():
    # Una ruta que no existe debe devolver el fallback
    path = Path("archivo_inexistente_999.md")
    result = load_text(path)
    assert result == "*No disponible.*"

def test_load_context_no_report(tmp_path):
    # Setup entorno mock (crear falsos markdowns en un tmp_path)
    outdir = tmp_path
    (outdir / "analysis_local.md").write_text("CREATE TABLE Test;", encoding="utf-8")
    
    context = load_context(outdir, include_report=False)
    
    assert "CREATE TABLE Test;" in context
    assert "CONTEXTO HISTÓRICO Y RESUMEN" not in context

def test_load_context_with_report(tmp_path):
    outdir = tmp_path
    (outdir / "analysis_local.md").write_text("CREATE TABLE Test;", encoding="utf-8")
    (outdir / "final_report.md").write_text("Este es el gran reporte.", encoding="utf-8")
    
    context = load_context(outdir, include_report=True)
    
    assert "CREATE TABLE Test;" in context
    assert "CONTEXTO HISTÓRICO Y RESUMEN" in context
    assert "Este es el gran reporte." in context

def test_build_prompt_with_history():
    sys_prompt = "Hola, eres un sistema experto."
    history = [
        {"role": "user", "content": "Primera preg"},
        {"role": "assistant", "content": "Primera resp"},
        {"role": "user", "content": "Segunda preg"},
        {"role": "assistant", "content": "Segunda resp"}
    ]
    
    # Supongamos que añadimos la tercera pregunta
    # st.session_state.messages[:-1] representa la historia anterior, excluding the current prompt
    # history in arg IS the history
    
    new_query = "Tercera preg"
    
    prompt = build_prompt_with_history(sys_prompt, history, new_query)
    
    assert "Hola, eres un sistema experto." in prompt
    assert "USUARIO: Primera preg" in prompt
    assert "ASISTENTE: Primera resp" in prompt
    assert "USUARIO: Tercera preg" in prompt
    assert prompt.endswith("ASISTENTE:\n")
