Name:           blanket
Version:        0.7.0
Release:        1%{?dist}
Summary:        White noise audio player

License:        GPLv3+
URL:            https://github.com/rafaelmardojai/blanket
Source0:        %{url}/archive/%{version}/%{name}-%{version}.tar.gz

Requires:       glib2
Requires:       gtk4
Requires:       libhandy1
Requires:       libadwaita
Requires:       libappstream-glib
Requires:       python3-gobject
BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  glib2-devel
BuildRequires:  libhandy1-devel
BuildRequires:  gtk4-devel
BuildRequires:  python3-gstreamer1
BuildRequires:  libadwaita-devel

BuildArch:      noarch

%description
Improve focus and increase your productivity by listening to different sounds. Or allows you to fall asleep in a noisy environment.


%prep
%autosetup -p1


%build
%meson
%meson_build



%install
%meson_install

%find_lang %{name}


%files -f %{name}.lang
%license COPYING SOUNDS_LICENSING.md
%{_bindir}/blanket
%{_datadir}/blanket/
%{_datadir}/applications/com.rafaelmardojai.Blanket.desktop
%{_datadir}/glib-2.0/schemas/com.rafaelmardojai.Blanket.gschema.xml
%{_datadir}/icons/hicolor/scalable/apps/com.rafaelmardojai.Blanket.svg
%{_datadir}/icons/hicolor/symbolic/apps/com.rafaelmardojai.Blanket-symbolic.svg
%{_datadir}/metainfo/com.rafaelmardojai.Blanket.metainfo.xml

%changelog

