FROM ubuntu:20.04
MAINTAINER Nils Hoffmann <nils.hoffmann@cebitec.uni-bielefeld.de>
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-setuptools \
    dpkg-dev \
    build-essential \
    python3-dev \
    libpython3-dev \
    freeglut3-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libgstreamer-plugins-base1.0-dev \
    libgtk-3-dev \
    libjpeg-dev \
    libnotify-dev \
    libpng-dev \
    libsdl2-dev \
    libsm-dev \
    libtiff-dev \
    libwebkit2gtk-4.0-dev \
    libxtst-dev \
 && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install \
    numpy \
    ply \
    configparser \
    lxml \
    pyteomics \
    pandas \
    wxPython
VOLUME /tmp
COPY . /lx
WORKDIR /lx
ENTRYPOINT ["python3", "/lx/lxrun.py"]
CMD ["--help"]
