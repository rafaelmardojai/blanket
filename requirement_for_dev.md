# Development Requirements

## System dependencies
- python
- python-gobject
- gtk4
- libadwaita
- gstreamer
- gst-plugins-base
- gst-plugins-good
- meson
- ninja
- blueprint-compiler

## Python dev dependencies
- basedpyright
- pygobject-stubs
- ruff

## Build workflows

### 1) Local repo install (fast local testing)
Use this when testing directly from the repository install under _install.

```bash
meson setup builddir --prefix "$PWD/_install" --reconfigure
meson compile -C builddir
meson install -C builddir
```

Run from local install:

```bash
GSETTINGS_SCHEMA_DIR="$PWD/_install/share/glib-2.0/schemas" \
XDG_DATA_DIRS="$PWD/_install/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" \
./_install/bin/blanket
```

### 2) Install Blanket on PATH (recommended for normal CLI usage)
Use a standard prefix so blanket is available from any terminal.

System-wide install:

```bash
meson setup builddir --prefix=/usr/local --reconfigure
meson compile -C builddir
sudo meson install -C builddir
```

User-local install (no sudo):

```bash
meson setup builddir --prefix="$HOME/.local" --reconfigure
meson compile -C builddir
meson install -C builddir
```

If using the user-local install, ensure $HOME/.local/bin is on PATH.

## PR hygiene
The _install directory is tracked in this repository and can produce noisy diffs.

Before committing:

```bash
git restore _install
git status --short
```

Only stage intended source/docs changes.