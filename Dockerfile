FROM ubuntu:20.04
MAINTAINER Nils Hoffmann <nils.hoffmann@isas.de>
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-setuptools \
 && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install \
    numpy \
    ply \
    configparser \
    lxml \
    pyteomics \
    pandas
VOLUME /tmp
COPY . /lx
WORKDIR /lx
ENTRYPOINT ["python3", "/lx/lxrun.py"]
CMD ["--help"]
