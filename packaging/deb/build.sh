#!/bin/bash
# Build augustus-free-assets_<version>_all.deb from c3data/.
set -e
cd "$(dirname "$0")/../.."
VERSION="${1:-1.0.0}"
OUT="${2:-dist}"
# optional variant: VARIANT=steampunk DATA=/path/to/data build.sh VERSION
VARIANT="${VARIANT:-}"
DATA="${DATA:-c3data}"
SUFFIX="${VARIANT:+-$VARIANT}"
NAME="augustus-free-assets$SUFFIX"
CMD="augustus-free$SUFFIX"
case "$VARIANT" in
    steampunk) LABEL="Augustus: Steam Age (free assets)"; FLAVOR="
 .
 Steampunk variant: brick factories, brass domes, smoke stacks and top hats.";;
    stoneage) LABEL="Augustus: Stone Age (free assets)"; FLAVOR="
 .
 Stone Age variant: thatched huts, stone circles and palisades.";;
    *) LABEL="Augustus (free assets)"; FLAVOR="";;
esac
STAGE=$(mktemp -d)
PKG="$STAGE/$NAME"
mkdir -p "$PKG/DEBIAN" "$PKG/usr/share/$NAME/data" "$PKG/usr/games" \
    "$PKG/usr/share/applications" "$PKG/usr/share/doc/$NAME"
# game data, without any per-user files
(cd "$DATA" && tar cf - --exclude='*.svx' --exclude='*.sav' --exclude=augustus.ini --exclude=c3.inf \
    --exclude=hotkeys.ini --exclude=layout.json --exclude='*.log' .) | tar xf - -C "$PKG/usr/share/$NAME/data"
find "$PKG/usr/share" -type d -exec chmod 755 {} +
find "$PKG/usr/share" -type f -exec chmod 644 {} +
sed "s|augustus-free-assets|$NAME|g" packaging/deb/augustus-free > "$PKG/usr/games/$CMD"
chmod 755 "$PKG/usr/games/$CMD"
sed -e "s|^Name=.*|Name=$LABEL|" -e "s|^Exec=.*|Exec=$CMD|" packaging/deb/augustus-free.desktop \
    > "$PKG/usr/share/applications/$CMD.desktop"
chmod 644 "$PKG/usr/share/applications/$CMD.desktop"
install -m 644 README.md "$PKG/usr/share/doc/$NAME/README.md"
install -m 644 LICENSE "$PKG/usr/share/doc/$NAME/copyright"
SIZE=$(du -sk "$PKG/usr" | cut -f1)
cat > "$PKG/DEBIAN/control" <<CTRL
Package: $NAME
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
 Start the game with the "$LABEL" menu entry or the
 $CMD command.$FLAVOR
CTRL
mkdir -p "$OUT"
fakeroot dpkg-deb --build -Zxz "$PKG" "$OUT/${NAME}_${VERSION}_all.deb" >/dev/null
rm -rf "$STAGE"
echo "$OUT/${NAME}_${VERSION}_all.deb"
