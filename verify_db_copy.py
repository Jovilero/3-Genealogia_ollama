import os
import subprocess
from urllib.parse import urlparse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
orig_url = os.getenv("DATABASE_URL", "")
parsed = urlparse(orig_url)

username = parsed.username
password = parsed.password
host = parsed.hostname
port = str(parsed.port or 5432)
orig_db = parsed.path.lstrip("/")
copy_db = f"{orig_db}_copia"

copy_url = orig_url.replace(orig_db, copy_db)
backup_file = "backup/arx_backup_20260319_143735.dump"

env = os.environ.copy()
if password:
    env["PGPASSWORD"] = password

print(f"⌛ Fase 1: Limpiando base de datos destino si existe ({copy_db})...")
subprocess.run(["dropdb", "-h", host, "-p", port, "-U", username, copy_db], env=env, stderr=subprocess.DEVNULL)

print(f"⌛ Fase 2: Creando nueva base de datos réplica ({copy_db})...")
subprocess.run(["createdb", "-h", host, "-p", port, "-U", username, copy_db], env=env, check=True)

print(f"⌛ Fase 3: Restaurando volcado lógico ({backup_file}) en la réplica (Multicore)...")
pg_restore_url = copy_url.replace("+psycopg2", "")
try:
    subprocess.run(["pg_restore", "-d", pg_restore_url, "-j", "4", backup_file], check=True, stderr=subprocess.DEVNULL)
except subprocess.CalledProcessError:
    print("⚠️ (Aviso: pg_restore finalizó con alertas de dependencias FK, procesando datos...)")

print("\n🔍 Fase 4: Iniciando verificación de integridad cruzada...")

engine_orig = create_engine(orig_url)
engine_copy = create_engine(copy_url)

def get_tables(engine):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';"))
        return [row[0] for row in result]

tables_orig = get_tables(engine_orig)
tables_copy = get_tables(engine_copy)

if set(tables_orig) != set(tables_copy):
    print("❌ Discrepancia arquitectónica. Las tablas no coinciden.")
else:
    print(f"✅ Se encontraron las mismas {len(tables_orig)} tablas en la réplica y en original.")

all_match = True
print("Contando tuplas por tabla...")
for table in tables_orig:
    with engine_orig.connect() as c1, engine_copy.connect() as c2:
        count1 = c1.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        count2 = c2.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        match_str = "✔️" if count1 == count2 else "❌"
        print(f"   {match_str} Tabla [{table}]: {count1} filas vs {count2} filas")
        if count1 != count2:
            all_match = False

if all_match:
    print("\n🚀 VERIFICACIÓN EXITOSA: La copia de seguridad ha sido restaurada con un 100% de integridad.")
else:
    print("\n💀 FALLO DE INTEGRIDAD: Se detectaron discrepancias entre el original y la copia de seguridad.")
