project(
  'blanket',
  version: '0.8.0',
  meson_version: '>= 0.59.0',
  default_options: [
    'warning_level=2',
  ],
)

python = import('python')
i18n = import('i18n')

base_id = 'com.rafaelmardojai.Blanket'
pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'blanket')

if get_option('profile') == 'development'
  profile = 'Devel'
  vcs_tag = run_command('git', 'rev-parse', '--short', 'HEAD').stdout().strip()
  if vcs_tag == ''
    version_suffix = '-devel'
  else
    version_suffix = '-@0@'.format(vcs_tag)
  endif
  application_id = '@0@.@1@'.format(base_id, profile)
else
  profile = ''
  version_suffix = ''
  application_id = base_id
endif

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version() + version_suffix)
conf.set('APP_ID', application_id)
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

dependency('glib-2.0')
dependency('gobject-introspection-1.0', version: '>= 1.35.0')
dependency('gstreamer-1.0', version: '>= 1.18')
dependency('gtk4', version: '>= 4.17.5')
dependency('libadwaita-1', version: '>= 1.8')
dependency('libportal', version: '>= 0.9')
dependency('pygobject-3.0', version: '>= 3.51')

subdir('data')
subdir('blanket')
subdir('po')

gnome.post_install(
  gtk_update_icon_cache: true,
  glib_compile_schemas: true,
  update_desktop_database: true,
)
