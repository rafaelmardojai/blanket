pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
gnome = import('gnome')

blueprint = find_program('blueprint-compiler')
blueprints = custom_target('blueprints',
  input: files(
    'about.blp',
    'preferences.blp',
    'preset-chooser.blp',
    'preset-dialog.blp',
    'preset-row.blp',
    'sound-context-menu.blp',
    'shortcuts.blp',
    'sound-item.blp',
    'volume-row.blp',
    'window.blp',
  ),
  output: '.',
  command: [blueprint, 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

gnome.compile_resources('blanket',
  'blanket.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)
