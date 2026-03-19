import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text, pool
from sqlalchemy.exc import SQLAlchemyError
import re

from dotenv import load_dotenv

load_dotenv()

class DBExecutor:
    def __init__(self, db_url: str | None = None):
        """
        Inicializa la conexión a la base de datos.
        Busca DATABASE_URL en el entorno si no se proporciona.
        Por defecto usa SQLite en memoria si no hay configuración, útil para pruebas.
        """
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///:memory:")
        try:
            if ":memory:" in self.db_url:
                self.engine = create_engine(self.db_url, echo=False, poolclass=pool.StaticPool, connect_args={'check_same_thread': False})
            else:
                self.engine = create_engine(self.db_url, echo=False)
            logging.info(f"Conexión a BD inicializada: {self.db_url.split('@')[-1]}")
        except Exception as e:
            logging.error(f"Error al crear el motor de base de datos: {e}")
            self.engine = None

    def execute_to_df(self, query: str) -> pd.DataFrame:
        """
        Ejecuta una consulta SQL en la BD y devuelve los resultados en un DataFrame.
        """
        if not self.engine:
            raise ValueError("El motor de la base de datos no está configurado.")
            
        query = query.strip().strip("`").removeprefix("sql").strip()

        # --- SAFEGUARDS DE SEGURIDAD AVANZADOS (FASE 13) ---
        forbidden_keywords = [
            r"\bDROP\b",    r"\bDELETE\b", r"\bUPDATE\b", r"\bINSERT\b", 
            r"\bALTER\b",   r"\bTRUNCATE\b", r"\bREPLACE\b", r"\bGRANT\b", 
            r"\bREVOKE\b",  r"\bCREATE\b", r"\bMERGE\b", r"\bEXEC\b", 
            r"\bEXECUTE\b", r"\bCALL\b", r"\bCOPY\b", r"\bINTO\b", 
            r"\bpg_sleep\b"
        ]
        
        for kw in forbidden_keywords:
            if re.search(kw, query, re.IGNORECASE):
                logging.warning(f"Intento de operación destructiva bloqueado: {query}")
                raise ValueError("🚨 Seguridad Crítica: Solo se permiten operaciones de LECTURA (SELECT). Se ha detectado una palabra reservada prohibida.")
                
        # Prevención de inyecciones SQL que concatenan múltiples sentencias
        if query.count(';') > 1 or (query.count(';') == 1 and not query.strip().endswith(';')):
            logging.warning(f"Intento de ejecución múltiple bloqueado: {query}")
            raise ValueError("🚨 Seguridad Crítica: Múltiples sentencias SQL (concatenadas con ';') no están permitidas.")

        with self.engine.connect() as conn:

            try:
                result = conn.execute(text(query))
                
                # Para updates/inserts en db genéricas a veces hay que hacer commit
                conn.commit()
                
                if result.returns_rows:
                    df = pd.DataFrame(result.fetchall(), columns=result.keys())
                    return df
                else:
                    return pd.DataFrame([{"Resultado": f"Operación completada, {result.rowcount} filas afectadas."}])
            except SQLAlchemyError as e:
                logging.error(f"Fallo ejecutando SQL:\n{query}\nError: {str(e)}")
                raise

