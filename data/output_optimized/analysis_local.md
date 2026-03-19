# Esquema (Skeleton Analysis)
## DatosPersonales
**PK**: -

| Col | Tipo |
|---|---|
| registro | bigint |
| nombre | character |
| apellido1 | character |
| apellido2 | character |
| lugarsacramento | character |
| oficiante | character |
| profesion | character |
| profesionpadre | character |
| fechanacimiento | character |
| fechasacramento | character |
| residencia | character |
| lugarinscripcion | character |
| notas | character |

## Personas
**PK**: -

| Col | Tipo |
|---|---|
| ID | bigint |
| registro | integer |
| relacion | character |
| nombre | character |
| apellido1 | character |
| apellido2 | character |
| lugarnacimiento | character |
| CONSTRAINT | max8registros |

## Registros
**PK**: -

| Col | Tipo |
|---|---|
| Registro | bigint |
| Sacramentos | integer |
| Libro | character |
| Folio | character |
| Asiento | character |
| Sexo | "char" |
| Subcon | integer |

## Sacramentos
**PK**: -

| Col | Tipo |
|---|---|
| id | integer |
| Sacramentos | character |

