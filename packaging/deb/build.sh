#!/bin/bash
# Build augustus-free-assets_<version>_all.deb from c3data/.
set -e
cd "$(dirname "$0")/../.."
VERSION="${1:-1.0.0}"
OUT="${2:-dist}"
STAGE=$(mktemp -d)
PKG="$STAGE/augustus-free-assets"
mkdir -p "$PKG/DEBIAN" "$PKG/usr/share/augustus-free-assets/data" "$PKG/usr/games" \
    "$PKG/usr/share/applications" "$PKG/usr/share/doc/augustus-free-assets"
# game data, without any per-user files
(cd c3data && tar cf - --exclude='*.svx' --exclude='*.sav' --exclude=augustus.ini --exclude=c3.inf \
    --exclude=hotkeys.ini --exclude=layout.json --exclude='*.log' .) | tar xf - -C "$PKG/usr/share/augustus-free-assets/data"
find "$PKG/usr/share" -type d -exec chmod 755 {} +
find "$PKG/usr/share" -type f -exec chmod 644 {} +
install -m 755 packaging/deb/augustus-free "$PKG/usr/games/augustus-free"
install -m 644 packaging/deb/augustus-free.desktop "$PKG/usr/share/applications/augustus-free.desktop"
install -m 644 README.md "$PKG/usr/share/doc/augustus-free-assets/README.md"
install -m 644 LICENSE "$PKG/usr/share/doc/augustus-free-assets/copyright"
SIZE=$(du -sk "$PKG/usr" | cut -f1)
cat > "$PKG/DEBIAN/control" <<CTRL
Package: augustus-free-assets
Version: $VERSION
Section: games
Priority: optional
Architecture: all
Depends: augustus-game (>= 4.0) | augustus (>= 4.0)
Installed-Size: $SIZE
Maintainer: jeriksson621 <jeriksson621@gmail.com>
Homepage: https://github.com/jeriksson621/augustus-free-assets
Description: free generated game data for Augustus (Caesar III engine)
 Original, procedurally generated replacement data (graphics, text,
 messages, scenarios and a campaign) that lets Augustus run without the
 proprietary Caesar III files. The assets are LLM-generated placeholders
 made for gameplay testing.
 .
 Start the game with the "Augustus (free assets)" menu entry or the
 augustus-free command.
CTRL
mkdir -p "$OUT"
fakeroot dpkg-deb --build -Zxz "$PKG" "$OUT/augustus-free-assets_${VERSION}_all.deb" >/dev/null
rm -rf "$STAGE"
echo "$OUT/augustus-free-assets_${VERSION}_all.deb"
