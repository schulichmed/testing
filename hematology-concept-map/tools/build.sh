#!/bin/sh
# Rebuild the hematology concept map. usage: sh tools/build.sh <scratch dir> <w9.pdf> <w10.pdf> <w11.pdf> <preclerkship repo>
# The transcriptions (t_<map>_<L|R>.md) must already sit in <scratch>/ov beside the blobs that detect.py wrote.
set -e
T=$(dirname "$0"); OUT=$T/..; S=$1
python -I $T/extract.py $S/src "$2" "$3" "$4"
python -I $T/detect.py $S/src/w9.png $S/ov w9 4 5
python -I $T/detect.py $S/src/w10.png $S/ov w10 4 5
python -I $T/detect.py $S/src/w11.png $S/ov w11 6 4
python -I $T/convert.py $S/ov $S/map-data.json
python -I $T/chart_links.py $S/map-data.json $OUT/nodes.json "$5"
python -I $T/link_extras.py $OUT/nodes.json
for m in w9 w10 w11; do python -I $T/dzi.py $S/src/$m.png $OUT $m; done
