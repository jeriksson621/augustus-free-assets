#!/bin/bash
# Build a small showcase town in "Tiber Valley" and take README screenshots.
# usage: showcase.sh DATA_DIR WORK_DIR
L="$(dirname "$0")/live.sh"; D="$1"; W="$2"
rm -rf "$W"; "$L" start "$D" "$W" >/dev/null
"$L" do "$W" "click 400 300"; sleep 1
"$L" shot "$W" menu 300 >/dev/null
"$L" do "$W" "click 400 283"; sleep 1
"$L" do "$W" "click 140 333" "click 693 512"; sleep 3
"$L" do "$W" "click 700 125" "click 770 314" "click 480 425" "drag 60 420 600 420" "drag 330 420 330 120" \
    "key 41 27" "click 770 314" "click 480 425" "drag 440 410 200 290" \
    "key 41 27" "click 670 314" "drag 225 345 290 420" "drag 330 390 390 460" "drag 130 445 230 495" \
    "key 41 27" "click 770 350" "click 480 297"
sleep 0.5
"$L" do "$W" "click 480 353" "click 560 400" "click 480 297"
sleep 0.5
"$L" do "$W" "click 480 449" "click 470 335" "key 41 27" "click 670 350" "click 480 441" "click 270 465" \
    "click 400 310" "key 41 27" "click 720 422" "click 480 441" "click 330 320" "click 250 360" "key 41 27" \
    "click 670 422" "click 480 441" "click 520 470" "key 41 27" "click 684 516" "click 684 516" "click 684 516"
"$L" shot "$W" city 14000 >/dev/null
"$L" do "$W" "click 755 190"
"$L" shot "$W" empire 1500 >/dev/null
"$L" stop "$W" >/dev/null
ls "$W"/*.png
