#!/usr/bin/env python3
"""Build a signed, flat-file apt repository for GitHub Pages.

usage: build-repo.py SITE_DIR DEB... [--key FINGERPRINT]
Layout: pool/main/a/augustus-free-assets/*.deb, dists/stable/{Release,InRelease,Release.gpg},
dists/stable/main/binary-{all,amd64,arm64,i386,armhf}/Packages(.gz), augustus-free-assets.gpg
"""
import argparse
import gzip
import hashlib
import os
import shutil
import subprocess
import time

SUITE = "stable"
ARCHES = ["all", "amd64", "arm64", "i386", "armhf"]


def hashes(path):
    data = open(path, "rb").read()
    return (len(data), hashlib.md5(data).hexdigest(), hashlib.sha1(data).hexdigest(),
            hashlib.sha256(data).hexdigest())


def control_fields(deb):
    out = subprocess.run(["dpkg-deb", "-f", deb], check=True, capture_output=True, text=True).stdout
    return out.rstrip("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site")
    ap.add_argument("debs", nargs="+")
    ap.add_argument("--key", required=True)
    a = ap.parse_args()
    pool = os.path.join(a.site, "pool", "main", "a", "augustus-free-assets")
    os.makedirs(pool, exist_ok=True)
    for deb in a.debs:
        shutil.copy2(deb, pool)
    entries = []
    for name in sorted(os.listdir(pool)):
        if not name.endswith(".deb"):
            continue
        path = os.path.join(pool, name)
        size, md5, sha1, sha256 = hashes(path)
        rel = os.path.relpath(path, a.site)
        entries.append("%s\nFilename: %s\nSize: %d\nMD5sum: %s\nSHA1: %s\nSHA256: %s\n" % (
            control_fields(path), rel, size, md5, sha1, sha256))
    packages = "\n".join(entries)
    dist = os.path.join(a.site, "dists", SUITE)
    files = []
    for arch in ARCHES:
        d = os.path.join(dist, "main", "binary-" + arch)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "Packages"), "w") as f:
            f.write(packages)
        with open(os.path.join(d, "Packages.gz"), "wb") as f:
            f.write(gzip.compress(packages.encode(), mtime=0))
        for fn in ("Packages", "Packages.gz"):
            files.append(os.path.join("main", "binary-" + arch, fn))
    lines = ["Origin: augustus-free-assets", "Label: augustus-free-assets", "Suite: " + SUITE,
             "Codename: " + SUITE, "Architectures: " + " ".join(ARCHES), "Components: main",
             "Description: Free generated game data for Augustus",
             "Date: " + time.strftime("%a, %d %b %Y %H:%M:%S UTC", time.gmtime())]
    for field, idx in (("MD5Sum", 1), ("SHA1", 2), ("SHA256", 3)):
        lines.append(field + ":")
        for rel in files:
            h = hashes(os.path.join(dist, rel))
            lines.append(" %s %d %s" % (h[idx], h[0], rel))
    release = os.path.join(dist, "Release")
    with open(release, "w") as f:
        f.write("\n".join(lines) + "\n")
    for p in ("InRelease", "Release.gpg"):
        if os.path.exists(os.path.join(dist, p)):
            os.remove(os.path.join(dist, p))
    subprocess.run(["gpg", "--batch", "--yes", "-u", a.key, "--clearsign", "-o", os.path.join(dist, "InRelease"),
                    release], check=True)
    subprocess.run(["gpg", "--batch", "--yes", "-u", a.key, "-abs", "-o", os.path.join(dist, "Release.gpg"),
                    release], check=True)
    subprocess.run(["gpg", "--batch", "--yes", "--export", "-o", os.path.join(a.site, "augustus-free-assets.gpg"),
                    a.key], check=True)
    subprocess.run(["gpg", "--batch", "--yes", "--armor", "--export", "-o",
                    os.path.join(a.site, "augustus-free-assets.asc"), a.key], check=True)
    open(os.path.join(a.site, ".nojekyll"), "w").close()


if __name__ == "__main__":
    main()
