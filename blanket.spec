Name:       blanket
Version:    0.3.1
Release:    1%{?dist}
Summary:    White audio player

License:        GPLv3+
URL:            https://github.com/rafaelmardojai/blanket
Source0:        https://github.com/rafaelmardojai/blanket/archive/0.3.1.tar.gz

Requires:       glib2
Requires:       gtk3
Requires:       libhandy1
Requires:       libappstream-glib
BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  glib2-devel
BuildRequires:  libhandy1-devel
BuildRequires:  gtk3-devel
BuildRequires:  python3-gstreamer1

%description
Improve focus and increase your productivity by listening to different sounds. Or allows you to fall asleep in a noisy environment.


%prep
%autosetup -p1 -n blanket-0.3.1


%global debug_package %{nil}

%build
%meson
%meson_build



%install
%meson_install


%check


%files
%{_datadir}/blanket/
%{_bindir}/blanket
%{_datadir}/applications/com.rafaelmardojai.Blanket.desktop
%{_datadir}/glib-2.0/schemas/com.rafaelmardojai.Blanket.gschema.xml
%{_datadir}/icons/hicolor/scalable/apps/com.rafaelmardojai.Blanket.svg
%{_datadir}/icons/hicolor/symbolic/apps/com.rafaelmardojai.Blanket-symbolic.svg
%{_datadir}/icons/hicolor/symbolic/apps/com.rafaelmardojai.Blanket-wm.svg
%{_datadir}/locale/eo/LC_MESSAGES/blanket.mo
%{_datadir}/locale/es/LC_MESSAGES/blanket.mo
%{_datadir}/locale/eu/LC_MESSAGES/blanket.mo
%{_datadir}/locale/it/LC_MESSAGES/blanket.mo
%{_datadir}/locale/nl/LC_MESSAGES/blanket.mo
%{_datadir}/locale/pt_BR/LC_MESSAGES/blanket.mo
%{_datadir}/locale/ca/LC_MESSAGES/blanket.mo
%{_datadir}/locale/fr/LC_MESSAGES/blanket.mo
%{_datadir}/locale/uk/LC_MESSAGES/blanket.mo
%{_datadir}/locale/sk/LC_MESSAGES/blanket.mo
%{_datadir}/locale/sk/LC_MESSAGES/blanket.mo
%{_datadir}/metainfo/com.rafaelmardojai.Blanket.metainfo.xml

%changelog

