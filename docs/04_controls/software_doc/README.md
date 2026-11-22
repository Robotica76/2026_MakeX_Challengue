# Documentación del software (capítulo LaTeX)

Genera el capítulo **Software** a partir de los comentarios Doxygen de
`software/robot/main/Robot.py`.

```bash
python3 generate_software_doc.py          # genera generated/software.tex
python3 generate_software_doc.py --pdf    # además compila main.tex (requiere pdflatex)
python3 generate_software_doc.py ruta/otro/Robot.py   # otro archivo fuente
```

Volver a ejecutarlo después de cada cambio en `Robot.py`. Se regeneran listados de código,
variables, parámetros, tabla de botones, secuencia de arranque, ciclo principal y grafo de llamadas.

Archivos editables a mano: `design_decisions.json` (decisiones de diseño),
`diagrams/autonomous_flow.tex` (flujo autónomo) y `main.tex`.

## Idioma / Language

`python3 generate_software_doc.py --lang es|en [--pdf]` (default `es`). En inglés se usan `doxygen_en.json`
(traducción de cada texto Doxygen; si falta una entrada se deja el original), `design_decisions.en.json` y
`diagrams/autonomous_flow.en.tex`. Si cambias un comentario Doxygen, actualiza su entrada en `doxygen_en.json`.
