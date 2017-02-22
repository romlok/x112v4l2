X112V4L2
========

(eks eleven to vee for ell two)

X112v4l2 is a Linux glue UI for configuring FFmpeg to stream regions of an X11 desktop session to one or more virtual webcams.

![Status](/status.png)
![Device config](/device.png)

Requirements
------------

* Python 3
* Python3 GObject
* GTK+ >=3.12
* v4l2-loopback
* ffmpeg

Installation
------------

The following should be copy & pastable for users of Debian/Ubuntu and derivatives. If you're installing this by hand on any other distribution, you're probably technical enough to be able to adapt the commands yourself:

```
sudo apt-get install git python3-xlib python3-gi v4l-utils v4l2loopback-utils ffmpeg
cd
git clone https://github.com/romlok/x112v4l2.git
./x112v4l2/x112v4l2.py
```

Legalities
----------

Unless otherwise stated, this software is licensed under the terms of the GPLv3. See GPLv3.txt.

The application icon is derived from the KDE Breeze icon set, which is licensed under the LGPLv3. See icons/COPYING-ICONS for details.
