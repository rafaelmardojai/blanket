<h1 align="center">
	<img src="brand/logo.svg" alt="Blanket" width="128" height="128"/><br>
	Blanket
</h1>

[![Please do not theme this app](https://stopthemingmy.app/badge.svg)](https://stopthemingmy.app) 
[![GitHub](https://img.shields.io/github/license/rafaelmardojai/blanket.svg)](https://github.com/rafaelmardojai/blanket/blob/master/COPYING)
[![Donate](https://img.shields.io/badge/PayPal-Donate-gray.svg?style=flat&logo=paypal&colorA=0071bb&logoColor=fff)](https://paypal.me/RafaelMardojaiCM)

<p align="center"><strong>Listen to different sounds</strong></p>

<p align="center">
  <a href="https://flathub.org/apps/details/com.rafaelmardojai.Blanket"><img width="200" alt="Download on Flathub" src="https://flathub.org/assets/badges/flathub-badge-en.png"/></a>
</p>

<p align="center">
  <img src="brand/screenshot-1.png"/>
</p>


## Description
Improve focus and increase your productivity by listening to different sounds. Or allows you to fall asleep in a noisy environment.

## Other Methods of Installation
> We are looking for volunteers to help us make native packages of Blanket for Debian, Fedora, and other major distributions. It would be great if you could help.

### AUR
For Arch Linux and its derivatives you can install the [`blanket`](https://aur.archlinux.org/packages/blanket) package from AUR.

## Build from source

Clone and run from GNOME Builder.

### Requirements

- Python 3 `python`
- PyGObject `python-gobject`
- `appstream-glib`
- GTK3 `gtk3`
- Handy `libhandy >= 0.90.0`
- GStreamer `gstreamer`
- `python-gst`
- Meson `meson`
- Ninja `ninja`

### Meson
```bash
meson builddir --prefix=/usr/local
sudo ninja -C builddir install
```
## Credits
Developed by **[Rafael Mardojai CM](https://github.com/rafaelmardojai)** and [contributors](https://github.com/rafaelmardojai/blanket/graphs/contributors).

## Donate
If you want to support development, consider donating via [PayPal](https://paypal.me/RafaelMardojaiCM).
