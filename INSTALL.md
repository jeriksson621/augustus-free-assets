# Installing

You need two things:

1. **Augustus** itself (the game engine), version 4.0 or newer.
2. **One data pack**, about 7 MB each. It replaces the original Caesar III files. Pick a look:
   - Classic (Roman): [augustus-free-assets.zip](https://github.com/jeriksson621/augustus-free-assets/raw/main/augustus-free-assets.zip)
   - Steampunk: [augustus-free-assets-steampunk.zip](https://github.com/jeriksson621/augustus-free-assets/raw/main/augustus-free-assets-steampunk.zip)
   - Stone Age: [augustus-free-assets-stoneage.zip](https://github.com/jeriksson621/augustus-free-assets/raw/main/augustus-free-assets-stoneage.zip)

   The steps below use the classic zip; for a variant, use its zip and its folder name
   (`augustus-data-steampunk` or `augustus-data-stoneage`).

The zip contains one folder, `augustus-data`. Extract it somewhere you can write to: the game
stores its settings and saved games in that folder.

---

## Windows

1. Download the latest Windows release of Augustus from
   <https://github.com/Keriew/augustus/releases/latest> (the `windows` zip). Extract it, for
   example to `C:\Games\Augustus`. It contains `augustus.exe`, some `.dll` files and an `assets`
   folder. Keep them together.
2. Download [augustus-free-assets.zip](https://github.com/jeriksson621/augustus-free-assets/raw/main/augustus-free-assets.zip)
   and extract it, for example to `C:\Games\augustus-data`.
3. Start the game in one of these ways:
   - Double-click `augustus.exe`. When it asks for your Caesar 3 folder, choose
     `C:\Games\augustus-data`. It remembers the choice.
   - Or copy everything from `augustus-data` into the folder that contains `augustus.exe`, then
     double-click `augustus.exe`.
   - Or from a command prompt:

     ```
     C:\Games\Augustus\augustus.exe C:\Games\augustus-data
     ```

## Linux

### Ubuntu / Debian: apt (recommended)

Add the project's apt repository once. You then get the data and updates with `apt`:

```bash
sudo curl -fsSLo /usr/share/keyrings/augustus-free-assets.gpg \
  https://jeriksson621.github.io/augustus-free-assets/augustus-free-assets.gpg
echo "deb [signed-by=/usr/share/keyrings/augustus-free-assets.gpg] https://jeriksson621.github.io/augustus-free-assets stable main" \
  | sudo tee /etc/apt/sources.list.d/augustus-free-assets.list
sudo apt update
sudo apt install augustus-free-assets            # classic
sudo apt install augustus-free-assets-steampunk  # steampunk variant
sudo apt install augustus-free-assets-stoneage   # stone age variant
```

Variants can be installed side by side; each has its own menu entry
(`augustus-free-steampunk`, `augustus-free-stoneage`) and its own saved games.

This also installs `augustus-game` from Ubuntu. Start **Augustus (free assets)** from the
application menu, or run `augustus-free` in a terminal (`augustus-free --windowed` for a
window). Saved games go to `~/.local/share/augustus-free-assets/`.

Signing key fingerprint: `A1DE 3853 3E68 123D 2180  EE6D 0953 9F18 339E 103D`

### Ubuntu / Debian: single .deb file

Download `augustus-free-assets_1.1.0_all.deb` from the
[latest release](https://github.com/jeriksson621/augustus-free-assets/releases/latest), then:

```bash
sudo apt install ./augustus-free-assets_1.1.0_all.deb
```

### Ubuntu / Debian: manual zip

```bash
sudo apt install augustus-game
```

Then download and extract the data:

```bash
mkdir -p ~/Games && cd ~/Games
wget https://github.com/jeriksson621/augustus-free-assets/raw/main/augustus-free-assets.zip
unzip augustus-free-assets.zip
augustus-game ~/Games/augustus-data
```

To start it from the application menu without typing the path, tell Augustus where the data is:

```bash
mkdir -p ~/.local/share/augustus/augustus
printf '%s' "$HOME/Games/augustus-data" > ~/.local/share/augustus/augustus/data_dir.txt
```

### Other distributions (AppImage)

1. Download the Augustus AppImage from <https://github.com/Keriew/augustus/releases/latest>
   and make it executable: `chmod +x augustus-*.AppImage`.
2. Download and extract the data zip as shown above.
3. Run it with the data folder:

   ```bash
   ./augustus-*.AppImage ~/Games/augustus-data
   ```

---

## Useful options

| Option | Effect |
|---|---|
| `--windowed` | Start in a window instead of fullscreen |
| `--display-scale 150` | Make everything bigger (percent) |

## What to play

- **Choose a scenario** in the main menu: Tiber Valley, Open Fields (sandbox, no goals),
  Northern Frontier and Desert Oasis.
- **Start a new career**: a 22-mission campaign. The first two missions are short tutorials.

## Troubleshooting

- **"Augustus requires the original files from Caesar 3"**: the folder you gave doesn't contain
  `c3.eng`. Point it at the `augustus-data` folder itself, not the folder above it.
- **Missing extra assets warning**: the Augustus `assets` folder isn't next to the program. On
  Windows keep it beside `augustus.exe`. On Debian/Ubuntu the package installs it to
  `/usr/share/augustus-game/assets`.
- **Saving fails**: the data folder must be writable. Don't put it in `Program Files` or `/usr`.
