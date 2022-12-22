pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'blanket')
revision = run_command('../build-aux/meson/revision.sh').stdout().strip()
if revision == ''
  revision=meson.project_version()
endif

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('REVISION', revision)
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'blanket.in',
  output: 'blanket',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

# Python sources
sources = [
  '__init__.py',
  'define.py',
  'main_player.py',
  'main.py',
  'window.py',
  'player.py',
  'preferences.py',
  'preset.py',
  'sound.py',
  'settings.py',
  'mpris.py'
]

install_data(sources, install_dir: moduledir)

# Install custom widgets
install_subdir('widgets', install_dir: moduledir)
