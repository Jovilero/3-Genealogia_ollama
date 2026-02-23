# Genealogia Ollama 🧬🤖

Este proyecto es una herramienta de análisis de bases de datos genealógicas (específicamente volcados SQL como `arxv_DB.txt`) diseñada para funcionar de forma **100% local**, garantizando la privacidad de los datos y eliminando costes de API externas.

## 🎯 Propósito del Proyecto
El objetivo principal es procesar archivos SQL de gran tamaño para extraer y documentar su estructura (esquemas, relaciones y lógica de datos) utilizando un enfoque híbrido:

1.  **Análisis Local (Regex)**: Una extracción determinística y rápida de tablas, columnas, claves primarias y foráneas utilizando expresiones regulares.
2.  **Análisis Inteligente (Ollama/AI)**: Uso del modelo local `qwen2.5-coder:14b` para explicar semánticamente el propósito de cada tabla y la lógica de las relaciones capturadas en los fragmentos SQL.

## 🚀 Características Principales
- **Local-First**: Procesa todo en tu máquina usando Ollama.
- **Sistema de Reanudación (Resume)**: Si el proceso se detiene, el script detecta automáticamente los archivos ya generados y continúa desde el último punto, ahorrando tiempo y cómputo.
- **Escalabilidad**: Divide archivos gigantes en trozos (chunks) configurables para procesar Gbs de datos sin saturar la memoria.
- **Trazabilidad**: Genera logs detallados en `process.log` para seguir el análisis.

## 🛠️ Requisitos
- **Python 3.10+**
- **Ollama** funcionando con el modelo `qwen2.5-coder:14b` (o cualquier otro modelo que especifiques).
- Dependencias: `requests`

## 📋 Uso
Instala las dependencias:
```bash
pip install requests
```

Ejecuta el análisis:
```bash
python src/main.py --sql path/to/your/db.sql --outdir ./data/output
```

### Opciones adicionales:
- `--chunk-size`: Cambia el tamaño de los trozos (por defecto 200,000 caracteres).
- `--model`: Especifica un modelo de Ollama diferente.
- `--no-resume`: Fuerza el análisis completo desde cero.

## 📁 Estructura de Salida
En la carpeta de salida (outdir) encontrarás:
- `analysis_local.md`: El esquema técnico puro extraído por Regex.
- `analysis_ollama_combined.txt`: El análisis semántico completo generado por la IA.
- `api_chunk_###.txt`: Los fragmentos individuales de la respuesta de la IA.
- `process.log`: El registro de toda la ejecución.
