## Global dependencies
python
python-gobject 
gtk4 
libadwaita 
gstreamer
gst-plugins-base
gst-plugins-good
meson ninja
blueprint-compiler

## Venv-dependencies
basedpyright
pygobject-stubs
ruff

## Run if the code changes:
```
meson setup builddir --prefix "$PWD/_install" --reconfigure
meson compile -C builddir
meson install -C builddir
```

## Compile and run app
`./_install/bin/blanket`

Command to run on my laptop:
```
GSETTINGS_SCHEMA_DIR="$PWD/_install/share/glib-2.0/schemas" XDG_DATA_DIRS="$PWD/_install/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}" ./_install/bin/blanket
```