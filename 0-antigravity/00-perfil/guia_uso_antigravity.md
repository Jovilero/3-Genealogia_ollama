# Guía de uso: Antigravity AI
> Basada en [best practices de Claude Code](https://code.claude.com/docs/en/best-practices), adaptada a Antigravity (Google DeepMind).
> Última actualización: 2026-02-21

---

> [!NOTE]
> Esta guía es **viva**: la iremos actualizando a medida que aprendamos cómo trabajamos mejor juntos.

---

## 1. El flujo óptimo: Explorar → Planificar → Ejecutar → Verificar

No pidas directamente que "haga X". El resultado es mejor si seguimos estas fases:

```
# 1. Explorar (lee el contexto)
"lee los archivos de /src/auth y entiende cómo funcionan las sesiones"

# 2. Planificar (genera un plan antes de tocar código)
"¿qué hay que cambiar para añadir OAuth de Google? crea un plan"
→ Antigravity escribe el plan en 0-antigravity/plan_<tema>.md

# 3. Ejecutar
"implementa el plan"

# 4. Verificar
"ejecuta los tests y arregla los fallos"
```

**¿Por qué?** Si pides directamente "implementa OAuth", salto pasos y puedo cometer errores que cuestan mucho contexto corregir.

---

## 2. Da contexto específico, no descripciones vagas

| ❌ Vago | ✅ Específico |
|---------|--------------|
| "¿qué mejorarías de este archivo?" | "¿qué mejorarías en `conversor+ponedor+exe.py` en términos de seguridad y mantenibilidad?" |
| "arregla el bug" | "hay un bug en `prova18-4funcional2.py` línea 55: falla si el nombre de carpeta tiene espacios" |
| "haz que funcione" | "el script falla con `ImportError: No module named request`. Corrígelo" |

**Regla de oro:** cuanto más específico seas, menos iteraciones necesitamos.

---

## 3. Cómo referenciar contenido eficientemente

- **Archivos**: menciona la ruta o tenlos abiertos en el editor — los veo en el contexto automáticamente.
- **Errores**: pega el traceback completo directamente en el chat.
- **Imágenes**: puedes pegar capturas de pantalla directamente.
- **URLs**: pégalas tal cual, las leo (como hice con esta guía).
- **Logs largos**: guárdalos en un `.txt` en `0-antigravity/` y dime el nombre.

---

## 4. Gestiona el contexto de la conversación

El contexto es finito. Si se llena de intentos fallidos o temas mezclados, la calidad baja.

### Cuándo empezar una conversación nueva
- Al cambiar de proyecto completamente.
- Después de muchas correcciones fallidas sobre el mismo tema.
- Cuando la conversación está muy larga y noto que "olvido" cosas anteriores.

### Patrón anti-"kitchen sink"
> ❌ No: en la misma sesión mezclar "arregla el scraper" + "explícame Git" + "crea una web"  
> ✅ Sí: una sesión por tema o proyecto

### Correcciones que no funcionan
Si me corriges dos veces y sigo equivocándome, **no corrijas una tercera vez**. En su lugar:
1. Para y piensa qué parte del prompt original fue ambigua.
2. Empieza de nuevo con un prompt más preciso que incluya lo aprendido.

---

## 5. Dónde guardar las cosas (nuestra convención)

| Tipo de archivo | Carpeta |
|----------------|---------|
| Análisis, informes, guías | `0-antigravity/` |
| Planes de implementación | `0-antigravity/plan_<proyecto>.md` |
| Documentación de proyectos | En la carpeta del propio proyecto como `README.md` |
| Código fuente nuevo | En la carpeta del proyecto correspondiente |

**Formato por defecto:** `.md` salvo que pidas otro formato explícitamente.

---

## 6. Patrones de prompt eficientes

### Para tareas de código
```
contexto: [qué hace el proyecto]
problema: [qué falla o qué quiero añadir]
restricciones: [lenguaje, librerías, estilo]
verificación: [cómo sé que está bien: tests, output esperado]
```

### Para análisis
```
analiza [archivo/carpeta] buscando [criterio concreto: seguridad / rendimiento / duplicación]
```

### Para refactorizaciones
```
refactoriza [archivo] para [objetivo]. No cambies el comportamiento externo.
genera tests antes de refactorizar para verificar que no se rompe nada.
```

### Para preguntas sobre el código
```
explícame cómo funciona [función/módulo] en [archivo]
```

---

## 7. Errores comunes a evitar

| Error | Por qué es malo | Cómo evitarlo |
|-------|-----------------|---------------|
| Pedir implementación sin contexto | Hago suposiciones erróneas | Pide primero el plan |
| Correcciones repetidas del mismo error | Se contamina el contexto | Reformula el prompt inicial |
| Mezclar temas en una conversación | Baja la precisión en todos | Una sesión por tema |
| "Hazlo funcionar" sin decir qué falla | No sé qué probar | Incluye el error exacto |
| Investigaciones sin acotar | Leo cientos de archivos y lleno contexto | Acota: "solo mira X e Y" |

---

## 8. Cómo pedirme que aprenda tus preferencias

Puedo almacenar preferencias como **workflows** reutilizables. Ejemplos:

```
"crea un workflow para refactorizar scripts Python con os.system()"
"crea un workflow para analizar seguridad de nuevos proyectos"
```

Los guardo en `.agent/workflows/<nombre>.md` y los aplico automáticamente cuando los mencionas.

---

## 9. Aprovecha el trabajo en paralelo

Puedo leer y modificar múltiples archivos a la vez. En lugar de:
> "primero arregla A, luego B, luego C"

Di:
> "arregla A, B y C" (si son independientes entre sí)

Esto reduce el número de turnos a la mitad o más.

---

## 10. Verificación: no confíes ciegamente, verifica

Aunque genere código que parece correcto, **siempre verifica**:
- Pídeme que genere tests antes de implementar.
- Si es una UI, usa el navegador para ver el resultado.
- Si es un script, pídeme que lo ejecute y muestre el output.

> [!IMPORTANT]
> Si no puedes verificarlo, no lo uses en producción.

---

## Nota sobre tokens y eficiencia

- **Respuestas largas en chat** = consumen contexto en cada turno siguiente. ✅ Mejor en archivo .md.
- **Preguntas cortas** = el chat es igual de eficiente.
- **Análisis de carpetas grandes** = pide que acote la búsqueda para no llenar contexto.
- **Conversaciones largas** = considera empezar nueva sesión para tareas no relacionadas.
