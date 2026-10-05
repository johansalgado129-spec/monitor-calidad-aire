# Guion breve para la socialización (3–5 minutos)

## Diapositiva 1 — Johan
Nuestro proyecto se llama Monitor de Calidad del Aire. El problema que abordamos es que existen datos públicos sobre contaminantes como PM2.5, NO₂ y O₃, pero para una persona sin conocimientos técnicos no siempre es fácil entender qué significan. Por eso planteamos un aplicativo web en Python que centraliza la consulta, interpreta la información cuando técnicamente es posible y conserva la trazabilidad de la fuente.

## Diapositiva 2 — Santiago
En el diseño funcional tenemos dos actores humanos: el usuario visitante y el administrador. OpenAQ funciona como sistema externo de datos. Los casos principales permiten consultar la calidad del aire, interpretar mediciones, visualizar gráficas, revisar y descargar el historial, y gestionar el historial desde una vista restringida. Los mockups muestran cómo se espera que el usuario realice la consulta desde el navegador.

## Diapositiva 3 — Johan
Las historias de usuario conectan directamente la necesidad con el desarrollo. Las dos de mayor prioridad son consultar una ciudad e interpretar PM2.5, NO₂ y O₃. Después aparecen la visualización e historial y la administración. La idea es que cada historia pueda rastrearse hasta un caso de uso y luego a una tarea concreta dentro de Jira.

## Diapositiva 4 — Johan y Santiago
Johan: El proyecto se organizó en ocho sprints. El Sprint 1, de análisis y requisitos, ya se completó con cinco tareas en estado Listo en Jira. Allí se definieron el problema, los requisitos funcionales y no funcionales, el plan académico y el alcance.

Santiago: Mi actividad dentro de ese sprint fue evaluar la cobertura y viabilidad de OpenAQ. La evidencia quedó adjunta en Jira. En este momento el Sprint 2 está en desarrollo y se cierra el 6 de octubre de 2026 con historias de usuario, UML y mockups.

## Diapositiva 5 — Santiago y cierre de Johan
Santiago: A nivel técnico ya contamos con una base modular en Python que separa la consulta a OpenAQ, el cálculo AQI, el historial, las gráficas y las pruebas. La integración web se irá completando en los sprints posteriores para mantener un avance incremental.

Johan: Como retroalimentación del primer sprint, validamos que definir bien los requisitos antes de programar reduce retrabajo, y que revisar OpenAQ desde el inicio disminuye riesgos técnicos. El próximo paso es cerrar el Sprint 2 y pasar a la arquitectura del repositorio y el desarrollo del backend.
