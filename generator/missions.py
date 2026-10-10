"""Builds mission1.pak (campaign) by exporting generated maps as campaign saves.

Uses a tooling build of Augustus 4.0.0 with tools/missionbuilder/mission_export.patch applied
(AUG_MISSION_MAP / AUG_MISSION_OUT hooks), run headless.
"""
import os
import shutil
import struct
import subprocess
import sys

import scenario

HEADER_ENTRIES = 100


def build(out, starts, mission_binary):
    src_dir = os.path.join(out, "campaign")
    maps = scenario.write_campaign_maps(src_dir, starts)
    saves = []
    env = dict(os.environ)
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)
    xdg = os.path.join(src_dir, "xdg")
    os.makedirs(xdg, exist_ok=True)
    env.update(SDL_VIDEODRIVER="offscreen", SDL_AUDIODRIVER="dummy", SDL_RENDER_DRIVER="software",
               XDG_DATA_HOME=xdg)
    for i, path in enumerate(maps):
        save = os.path.join(src_dir, "mission%02d.svx" % i)
        if os.path.exists(save):
            os.remove(save)
        env.update(AUG_MISSION_MAP=os.path.relpath(path, out), AUG_MISSION_OUT=os.path.relpath(save, out),
                   AUG_MISSION_ID=str(i))
        r = subprocess.run([mission_binary, "--windowed", out], env=env, stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        if r.returncode != 0 or not os.path.exists(save):
            raise RuntimeError("mission %d export failed (exit %d)" % (i, r.returncode))
        saves.append(open(save, "rb").read())
    data = bytearray(HEADER_ENTRIES * 4)
    for i, blob in enumerate(saves):
        struct.pack_into("<i", data, 4 * i, len(data))
        data += blob
    with open(os.path.join(out, "mission1.pak"), "wb") as f:
        f.write(data)
    shutil.rmtree(src_dir)
    return len(saves)


if __name__ == "__main__":
    import json
    import generate
    out, binary = sys.argv[1], sys.argv[2]
    specs, _ = generate.load_specs()
    lay = json.load(open(os.path.join(out, "layout.json")))
    name2id = {v["name"]: k for k, v in specs.items()}
    starts = {name2id[n]: s for n, s in lay.items()}
    print("missions:", build(out, starts, binary))
