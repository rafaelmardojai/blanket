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