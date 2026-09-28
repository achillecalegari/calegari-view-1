#!/bin/zsh
# Rebuild every documentation image (white studio). About 40 minutes on an M-series Mac.
set -e
cd "${0:A:h}/.."
PY="$PWD/.venv/bin/python"
B=/Applications/Blender.app/Contents/MacOS/Blender
R=out/white; mkdir -p $R
( cd cad
  $PY render_meshes.py --tag home
  $PY render_meshes.py --tag rise --sy 25 --sx -12
  $PY render_meshes.py --tag explode --explode 30
  $PY render_meshes.py --tag section --section
  $PY render_meshes.py --tag portrait --rot -90
  for n in 1 2 3 4 5 6 7 8 9; do $PY render_meshes.py --tag step$n --step $n; done )
export EXPO=-2.5 DIST=3.75
shot() { env FLAT="${FLAT:-}" SEALGREY="${SEALGREY:-}" $B -b -P render/white.py -- out/mesh_$1/manifest.json $R/$2.png $3 ${4:-110} ${5:-2000} >/dev/null 2>&1; echo "$2"; }
shot home  01_three_quarter w_34
shot home  02_front         w_front
shot home  03_side          w_side
shot home  04_rear          w_rear
shot home  05_top           w_top
DIST=4.4 shot section 06_section w_section
DIST=4.1 shot section 07_section_three_quarter w_section34
shot rise  08_shift         w_34
shot explode 09_exploded    explode34
shot portrait 10_portrait   w_rear
views=(w_34 w_rear w_rear w_34 w_34 w_34 w_34 w_34 w_rear)
for n in 1 2 3 4 5 6 7 8 9; do
  SEALGREY=1 shot step$n step_$(printf %02d $n) ${views[$n]} 80 1600
done
$PY render/compose.py docs/img $R/*.png
