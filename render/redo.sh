#!/bin/zsh
set -e
cd "${0:A:h}/.."
PY="$PWD/.venv/bin/python"; B=/Applications/Blender.app/Contents/MacOS/Blender; R=out/white
( cd cad; for n in 4 5 6 7; do $PY render_meshes.py --tag step$n --step $n; done )
export EXPO=-2.5 DIST=3.75
for n in 4 5 6 7; do $B -b -P render/white.py -- out/mesh_step$n/manifest.json $R/step_0$n.png w_34 80 1600 >/dev/null 2>&1; echo step$n; done
FLAT=1 $B -b -P render/white.py -- out/mesh_section/manifest.json $R/06_section.png w_section 110 2000 >/dev/null 2>&1
FLAT=1 $B -b -P render/white.py -- out/mesh_section/manifest.json $R/07_section_three_quarter.png w_section34 110 2000 >/dev/null 2>&1
$PY render/compose.py docs/img $R/*.png
