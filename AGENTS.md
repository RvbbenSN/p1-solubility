# AGENTS.md — Reglas de desarrollo

Versión v0 (23/10/2026). Borrador de partida basado en prácticas establecidas (TDD, SDD, arquitectura de núcleo puro, ingeniería de software científico). Se revisa al terminar la Fase 0 de la hoja de ruta (`alchemy-platform/docs/roadmap/HOJA_DE_RUTA.md`).

Estas reglas valen para cualquier agente de IA que trabaje en este repositorio (Claude Code, Cursor, Gemini u otros). Si una instrucción en la conversación contradice este archivo, pregunta antes de actuar.

## 1. Quién soy y cómo quiero trabajar

- Soy doctor en química (materiales, MOFs), no programador de formación. Estoy aprendiendo y quiero entender y controlar todo el backend.
- **Explícame antes de construir.** Para cualquier cambio no trivial, primero un plan en español llano; espera mi aprobación.
- **Un concepto nuevo por mensaje.** Si aparece una técnica, librería o patrón que no he usado, explícalo brevemente antes de usarlo.
- **Muestra la salida real de los comandos** (tests, linter, ejecuciones). Nunca digas que algo funciona sin haberlo ejecutado.
- Si no sabes algo o dudas, dilo. Prefiero una pregunta a una suposición.
- El frontend (Streamlit, HTML, CSS, JavaScript) puedes escribirlo con más autonomía. El backend en Python, no.

## 2. Flujo de trabajo obligatorio

Para cada tarea, en este orden:

1. **Explorar:** lee el código y las specs relacionadas. No escribas código todavía.
2. **Spec:** si la tarea es nueva o cambia comportamiento, crea o actualiza `specs/<modulo>.md` con objetivo, archivos que se tocan, firma de las funciones (inputs, outputs, tipos), casos límite y criterios de aceptación. Espera mi aprobación.
3. **Test primero:** escribe los tests que expresan la spec y ejecútalos para demostrar que fallan (rojo).
4. **Implementar:** el mínimo código que hace pasar los tests (verde).
5. **Refactorizar:** limpia sin cambiar el comportamiento; los tests siguen en verde.
6. **Verificar:** ejecuta la verificación completa (sección 7) y muestra la salida.
7. **Explicar:** resume qué ha cambiado, archivo por archivo, y señala cualquier decisión que debería revisar.
8. **Commit:** uno por tarea, pequeño, con mensaje descriptivo. No hagas push sin que te lo pida.

Tareas triviales (una errata, un nombre) pueden saltarse los pasos 2–3, pero nunca el 6.

## 3. Arquitectura

- **Núcleo puro** en `src/<paquete>/`: funciones de curado, featurización, split, modelado y evaluación. No leen ni escriben archivos, no imprimen, no dependen de variables globales. Mismo input → mismo output.
- **Bordes** (entrada/salida): lectura y escritura de datos, bases de datos, red, CLI. Van en módulos separados (p. ej. `io.py`) y llaman al núcleo.
- **`app/`** (interfaz): solo llama a funciones de `src/`. Sin lógica de negocio dentro de la app.
- **`notebooks/`**: solo exploración. Si algo de un notebook se reutiliza, se mueve a `src/` con su test.
- **`config/`**: parámetros (rutas, columnas, hiperparámetros, semillas) en YAML o TOML, validados con Pydantic. Nada de esto se escribe dentro de las funciones.
- **`data/raw/`** es inmutable: nunca se modifica ni se sobrescribe.

## 4. Reglas de código

- *Type hints* en todas las funciones públicas, incluidos los valores de retorno.
- Docstring en cada función pública: qué hace, argumentos, qué devuelve y qué errores lanza.
- Una función, una responsabilidad. Si una función pasa de ~40 líneas o hace dos cosas, divídela.
- Archivos pequeños y con un propósito: si un módulo pasa de ~300 líneas, propón dividirlo.
- Nombres descriptivos en inglés para el código; comentarios y documentación pueden ir en español.
- Nada de rutas, nombres de columnas ni números mágicos dentro de la lógica: vienen como argumentos o de la configuración.
- `logging` en lugar de `print`.
- Errores explícitos: nunca `except:` vacío ni `except Exception: pass`. Si algo falla, que falle con un mensaje claro.
- No añadas dependencias nuevas sin preguntarme y explicarme para qué sirven.
- Código simple antes que ingenioso. Si hay dos formas, la más legible.

## 5. Reglas de data science

- **El test se separa primero.** Ninguna decisión (escalado, selección de features, hiperparámetros) mira el conjunto de test.
- **Todo preprocesado dentro de un `Pipeline` de scikit-learn**, para que se ajuste solo con datos de entrenamiento.
- **Siempre un baseline** (media o regresión lineal) antes de cualquier modelo complejo.
- **Split adecuado a la química:** scaffold split o validación por grupos (GroupKFold) cuando haya familias de moléculas o materiales. El split aleatorio solo como comparación.
- **Semillas** (`random_state`) fijadas desde la configuración.
- **Validación de esquemas** (pandera) al cargar datos: columnas, tipos y rangos esperados.
- **Curado químico trazable:** cada molécula descartada (SMILES inválido, duplicado, sal) se registra con el motivo, y se informa de cuántas entraron y cuántas salieron.
- **Métricas con contexto:** reportar media y desviación de la validación cruzada, y comparar con el baseline y con la literatura cuando exista.

## 6. Tests

- pytest. Los tests van en `tests/` y reflejan la estructura de `src/`.
- Cada función pública del núcleo tiene al menos: un caso normal, un caso vacío y un caso inválido (p. ej. SMILES inválido, valor nulo, columna ausente).
- Los tests son rápidos y deterministas: datos pequeños de ejemplo (fixtures), sin red, sin depender de archivos grandes.
- No modifiques un test para que pase sin decírmelo y explicarme por qué el test estaba mal.

## 7. Verificación (obligatoria antes de dar algo por terminado)

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

Ejecuta los tres, completos, y muestra la salida. Si algo falla, arréglalo o explícame por qué no.

## 8. Git

- Commits pequeños, uno por tarea, con mensajes del tipo `feat: …`, `fix: …`, `test: …`, `docs: …`, `refactor: …`.
- Nunca se versionan `data/`, secretos ni archivos `.env`. Comprueba `.gitignore` antes del primer commit.
- No reescribas el historial ni hagas push sin que te lo pida.

## 9. Prohibido sin preguntar

- Borrar archivos o datos.
- Cambiar la estructura de carpetas.
- Añadir dependencias.
- Tocar `data/raw/`.
- Desactivar tests, reglas del linter o comprobaciones.
