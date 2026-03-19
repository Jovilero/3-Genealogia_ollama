import sys
import subprocess
import pytest
from unittest.mock import patch, MagicMock
import py_compile
import os

# Asegurarnos de que genealogia.py compila correctamente
def test_cli_compiles():
    cli_path = "genealogia.py"
    assert os.path.exists(cli_path)
    py_compile.compile(cli_path)

@patch("subprocess.run")
def test_cli_command_run(mock_run):
    from genealogia import main
    # Simular la llamada: python genealogia.py run --sql dummy.sql
    with patch.object(sys, "argv", ["genealogia.py", "run", "--sql", "dummy.sql"]):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        with pytest.raises(SystemExit) as e:
            main()
            
        assert e.value.code == 0
        
        # Verificar que subprocess llamó al script correcto
        mock_run.assert_called_once()
        args_called = mock_run.call_args[0][0]
        assert "src\\main_optimized.py" in str(args_called[1]) or "src/main_optimized.py" in str(args_called[1])
        assert "--sql" in args_called
        assert "dummy.sql" in args_called

@patch("subprocess.run")
def test_cli_command_web(mock_run):
    from genealogia import main
    with patch.object(sys, "argv", ["genealogia.py", "web"]):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        with pytest.raises(SystemExit) as e:
            main()
            
        assert e.value.code == 0
        
        # Web inyecta streamlit
        args_called = mock_run.call_args[0][0]
        assert "-m" in args_called
        assert "streamlit" in args_called
        assert "run" in args_called
        assert "src\\ui.py" in str(args_called[4]) or "src/ui.py" in str(args_called[4])

@patch("builtins.print")
def test_cli_invalid_command(mock_print):
    from genealogia import main
    with patch.object(sys, "argv", ["genealogia.py", "comandonoinvalido"]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1
        
        # El primer print debe indicar comando desconocido
        mock_print.assert_any_call("❌ Comando desconocido: 'comandonoinvalido'")
