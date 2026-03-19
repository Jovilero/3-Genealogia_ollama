# Protocolo de Seguridad de Antigravity (Antigravity Safety Protocol)

Para evitar interrupciones accidentales en el flujo de trabajo del usuario, se establecen las siguientes reglas de comportamiento vinculantes:

## 1. Protección de Procesos de Larga Duración
- **REGLA DE ORO:** NUNCA matar un proceso que lleve más de 10 minutos en ejecución sin pedir confirmación explícita al usuario. No importa si el proceso parece ineficiente o si hay una alternativa mejor; el tiempo del usuario es sagrado.
- **Auditoría Previa:** Antes de proponer o ejecutar un `taskkill` o similar, investigar el origen del proceso, su tiempo de CPU y su impacto en los archivos de salida.

## 2. Validación de Resumen (Resume Check)
- Al reanudar procesos, verificar siempre el estado real del disco (número de archivos, tamaño de logs) comparándolo con la salida esperada.
- Si hay una discrepancia entre lo que "creemos" que falta y lo que el usuario reporta, DETENERSE e investigar antes de continuar.

## 3. Comunicación de Riesgos
- Si se detecta un proceso ineficiente, PROPONER matarlo y ofrecer una alternativa, pero esperar a que el usuario diga "Sí" o "Dale" antes de actuar.
