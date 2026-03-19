import re
import logging

class SQLProcessor:
    def __init__(self, rows_to_keep: int = 5) -> None:
        self.rows_to_keep = rows_to_keep
        # Regex para detectar bloques de INSERT y COPY
        self.insert_start_pattern = re.compile(r"^INSERT\s+INTO\s+.*?\s+VALUES", re.IGNORECASE)
        self.copy_start_pattern = re.compile(r"^COPY\s+[`\"]?(\w+)[\w.`\"]*?\s*\(.*?\)\s+FROM\s+stdin\s*;", re.IGNORECASE)

    def generate_skeleton(self, sql_filepath: str, output_filepath: str) -> None:
        """Genera un esqueleto del SQL manteniendo esquema y truncando datos (soporta COPY y INSERT)."""
        logging.info(f"Generando esqueleto de {sql_filepath}...")
        
        with open(sql_filepath, 'r', encoding='utf-8', errors='ignore') as f_in, \
             open(output_filepath, 'w', encoding='utf-8') as f_out:
            
            in_data_block = False
            rows_count = 0
            skipped_count = 0
            current_table = "unknown"
            is_copy = False

            for line in f_in:
                clean_line = line.strip()
                
                # Detectar inicio de INSERT
                if self.insert_start_pattern.match(clean_line):
                    in_data_block = True
                    is_copy = False
                    rows_count = 0
                    m = re.search(r"INSERT\s+INTO\s+[`\"]?(\w+)[`\"]?", clean_line, re.I)
                    if m: current_table = m.group(1)
                
                # Detectar inicio de COPY
                elif self.copy_start_pattern.match(clean_line):
                    in_data_block = True
                    is_copy = True
                    rows_count = 0
                    m = self.copy_start_pattern.match(clean_line)
                    if m: current_table = m.group(1)
                    f_out.write(line) # Escribimos la cabecera del COPY
                    continue

                if in_data_block:
                    if is_copy:
                        # En COPY, el bloque termina con \.
                        if clean_line == "\\.":
                            if rows_count >= self.rows_to_keep:
                                f_out.write(f"-- [DATA SKIPPED FOR {current_table}: {skipped_count} lines approx]\n")
                            f_out.write("\\.\n")
                            in_data_block = False
                            skipped_count = 0
                        elif rows_count < self.rows_to_keep:
                            f_out.write(line)
                            rows_count += 1
                        else:
                            skipped_count += 1
                    else:
                        # Lógica INSERT existente
                        if rows_count < self.rows_to_keep:
                            f_out.write(line)
                            rows_count += 1
                        else:
                            skipped_count += 1
                            if clean_line.endswith(";"):
                                f_out.write(f"-- [DATA SKIPPED FOR {current_table}: {skipped_count} lines approx]\n")
                                f_out.write(";\n")
                                in_data_block = False
                                skipped_count = 0
                else:
                    # Otros comandos (CREATE, etc)
                    f_out.write(line)

        
        logging.info(f"Esqueleto generado en {output_filepath}")

    @staticmethod
    def parse_schema_local(sql_text: str):
        """Extrae tablas/columnas/PK/FK usando regex (Copiado de main.py pero modularizado)."""
        # Regex mejorada para soportar esquemas (ab."Tabla") y comillas
        CREATE_RE = re.compile(r"CREATE\s+TABLE\s+(?:[^\s(]+\.)?[\"\`]?(\w+)[\"\`]?\s*\((.*?)\)\s*;", re.I | re.S)
        COLUMN_RE = re.compile(r"^\s*[\"\`]?(\w+)[\"\`]?\s+([^\s,(]+)", re.I)
        PK_TABLE_RE = re.compile(r"PRIMARY\s+KEY\s*\(([^)]+)\)", re.I)
        PK_INLINE_RE = re.compile(r"PRIMARY\s+KEY", re.I)
        FK_RE = re.compile(r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+(?:[^\s(]+\.)?[\"\`]?(\w+)[\"\`]?\s*\(([^)]+)\)", re.I)

        schema = {}
        for m in CREATE_RE.finditer(sql_text):
            table = m.group(1)
            body = m.group(2)
            lines = [l.strip() for l in re.split(r",\s*\n|,\s*$", body)]
            cols = []
            pks = []
            fks = []
            for ln in lines:
                pk_m = PK_TABLE_RE.search(ln)
                if pk_m:
                    pks.extend([c.strip(" `\"") for c in pk_m.group(1).split(",")])
                    continue
                fk_m = FK_RE.search(ln)
                if fk_m:
                    cols_fk = [c.strip(" `\"") for c in fk_m.group(1).split(",")]
                    fks.append({"columns": cols_fk, "ref_table": fk_m.group(2), "ref_columns": [c.strip(" `\"") for c in fk_m.group(3).split(",")]})
                    continue
                col_m = COLUMN_RE.match(ln)
                if col_m:
                    col, typ = col_m.group(1), col_m.group(2)
                    cols.append({"name": col, "type": typ})
                    if PK_INLINE_RE.search(ln):
                        pks.append(col)
            schema[table] = {"columns": cols, "primary_key": pks, "foreign_keys": fks}
        return schema

    @staticmethod
    def schema_to_mermaid(schema: dict) -> str:
        """Convierte el diccionario de esquema en un diagrama ER de Mermaid."""
        lines = ["erDiagram"]
        
        # Primero, definir todas las entidades y sus columnas
        for table_name, data in schema.items():
            lines.append(f"    {table_name} {{")
            for col in data.get("columns", []):
                col_name = col["name"]
                col_type = col["type"].replace(" ", "_") # Mermaid fallará con espacios en tipos
                
                # Marcar PK y FK visualmente
                marker = ""
                if col_name in data.get("primary_key", []):
                    marker = " PK"
                elif any(col_name in fk["columns"] for fk in data.get("foreign_keys", [])):
                    marker = " FK"
                
                lines.append(f"        {col_type} {col_name}{marker}")
            lines.append("    }")
            
        # Segundo, definir las relaciones (foreign keys)
        for table_name, data in schema.items():
            for fk in data.get("foreign_keys", []):
                ref_table = fk["ref_table"]
                # Para ER de Mermaid: EntidadOrigen ||--o{ EntidadDestino : Etiqueta
                # Vamos a asumir una relación de 1 a N de forma genérica
                # ref_table (1) a table_name (N)
                # Sintaxis: ref_table ||--o{ table_name : "referencia"
                fk_cols = ",".join(fk["columns"])
                lines.append(f"    {ref_table} ||--o{{ {table_name} : \"{fk_cols}\"")
                
        return "\n".join(lines)

