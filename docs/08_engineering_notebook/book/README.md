# Libro de Ingeniería (Engineering Notebook) — generador del PDF

Script que arma el **libro de ingeniería** del equipo para MakeX 2026 Storm Breaker: registro del
proceso de diseño, construcción, programación y pruebas, con la evidencia que piden los jueces
(proceso y pruebas, resolución de problemas, trabajo en equipo, base para la entrevista).

```bash
python3 docs/08_engineering_notebook/book/build_engineering_notebook.py
# -> docs/08_engineering_notebook/book/output/Libro_de_Ingenieria.pdf
```

Se puede volver a ejecutar después de cualquier cambio en el repositorio: el PDF se regenera completo.

## Qué reúne

| Fuente | Capítulos |
| --- | --- |
| Tablero GitHub Project `Robotica76/projects/9`, issues, PRs y commits (vía `gh`) | Equipo y roles, gestión del proyecto, cronología con gráficas de actividad |
| Documentos `.md` del repo (`docs/`, `mechanical/`, `electrical/`, `software/`, `simulation/`, `tests/`, `tools/`, `resources/`) con sus imágenes | Reto, estrategia, arquitectura, diseño, control, simulación, problemas, pruebas, bitácora, anexos |
| Comentarios Doxygen de `Robot.py` (vía [`generate_software_doc.py`](../../04_controls/software_doc/README.md)) | Software del robot: diagramas, tabla de botones, decisiones y código |
| Marcadores `TBD` de los documentos | Anexo de pendientes antes de entregar |

## Requisitos

`python3`, `pandoc` ≥ 3, `lualatex` (paquetes `fvextra`, `listings`, `tikz`, `fontspec`), fuente DejaVu, y
`gh` autenticado. En Debian/Ubuntu:
`sudo apt install pandoc fonts-dejavu-core texlive-luatex texlive-latex-extra texlive-latex-recommended`.

## Opciones

| Opción | Efecto |
| --- | --- |
| `--offline` | No consulta GitHub; usa `data/github_snapshot.json` (la última copia, que se guarda en cada ejecución con red) |
| `--project-json FILE` | Usa el export del tablero: `gh project item-list 9 --owner Robotica76 --limit 500 --format json > tablero.json` |
| `--skip-software` | No regenera el capítulo Software |
| `--no-pdf` | Solo genera `build/libro.tex` |
| `--config`, `--output` | Otra configuración / otra ruta de salida |

## Tablero del proyecto (permisos)

Leer `https://github.com/orgs/Robotica76/projects/9` requiere un token con el permiso **`read:project`**
(`gh auth refresh -s read:project`). Sin él, el script **no falla**: avisa, usa la última copia guardada o,
si no hay, los issues del repositorio (estado Abierto/Cerrado) y lo indica en el libro. Con permiso, se
muestran los estados reales de las columnas del tablero.

## Qué editar

- [`book_config.json`](book_config.json): título, integrantes (`name`, `role`), criterios de evaluación y la
  lista de capítulos. Cada capítulo toma archivos (`path`) o patrones (`glob`, con `min_chars` para omitir
  plantillas casi vacías y `exclude` con expresiones regulares). Un documento nuevo que coincida con un
  patrón entra solo; para otros, agregarlo a la lista.
- [`templates/preamble.tex`](templates/preamble.tex): estilo del documento.
- [`filters/notebook.lua`](filters/notebook.lua): conversión de markdown (enlaces relativos, imágenes, tablas).
- Las decisiones del capítulo de Software están en `docs/04_controls/software_doc/design_decisions.json`.

## Notas

- Los documentos fuente están en inglés; la estructura, equipo, cronología y software, en español.
- Los enlaces relativos entre `.md` se muestran como texto; las imágenes `webp`/`svg` no se incluyen.
- Los datos de GitHub (nombres de commits, asignados) se publican tal cual están en el repositorio;
  revisar antes de compartir el PDF fuera del equipo.
- `build/` (intermedios) está ignorado por git; `output/` contiene el PDF generado.
