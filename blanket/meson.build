configure_file(
  input: 'blanket.in',
  output: 'blanket',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
)

configure_file(
  input: 'define.in',
  output: 'define.py',
  configuration: conf,
  install: true,
  install_dir: moduledir,
)

# Python sources
sources = [
  '__init__.py',
  'main.py',
  'main_player.py',
  'mpris.py',
  'preferences.py',
  'preset.py',
  'settings.py',
  'sound.py',
  'utils.py',
  'window.py',
]
install_data(sources, install_dir: moduledir)

# Install audio modules
install_subdir('audio', install_dir: moduledir)

# Install custom widgets
install_subdir('widgets', install_dir: moduledir)
