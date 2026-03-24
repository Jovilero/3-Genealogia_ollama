# Auditoria de estado y ramas (2026-03-23)

## Estado actual
- Rama activa: main
- Tracking: origin/main
- Divergencia: ahead 2 commits
- Working tree: sucia

## Cambios locales detectados
- src/ui.py (modificado)
- docs/ (no trackeado)

## Decision operativa
- No push directo a main en estado sucio.
- Crear rama de trabajo: feat/ui-doc-sync-20260323.
- Separar commits:
  1) cambios funcionales de ui
  2) cambios de documentacion
- Ejecutar validacion minima antes de PR.

## Riesgo principal
- Mezcla de cambios funcionales y documentales dificulta revision y rollback.
