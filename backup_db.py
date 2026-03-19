import os
import subprocess
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL", "")

if not db_url.startswith("postgresql"):
    print("El backup automático solo está configurado para PostgreSQL.")
    exit(1)

parsed = urlparse(db_url)
username = parsed.username
password = parsed.password
host = parsed.hostname
port = str(parsed.port or 5432)
dbname = parsed.path.lstrip("/")

os.makedirs("backup", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = f"backup/arx_backup_{timestamp}.dump"

print(f"Iniciando volcado de seguridad a {backup_file}...")
try:
    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password
        
    cmd = [
        "pg_dump",
        "-h", host,
        "-p", port,
        "-U", username,
        "-F", "c",
        "-f", backup_file,
        dbname
    ]
    subprocess.run(cmd, env=env, check=True)
    print(f"✅ ¡Copia de seguridad completada con éxito! Archivo guardado en: {backup_file}")
except Exception as e:
    print(f"❌ Fallo crítico al ejecutar el resguardo: {e}")
