FROM ubuntu
MAINTAINER soragoto@soragoto.io

RUN \
apt clean &&\
rm -rf /var/lib/apt/lists/* &&\
sed -i "s/archive.ubuntu.com/mirrors.aliyun.com/g" /etc/apt/sources.list &&\
sed -i "s/security.ubuntu.com/mirrors.aliyun.com/g" /etc/apt/sources.list &&\
export DEBIAN_FRONTEND=noninteractive &&\
apt update -y &&  apt upgrade -y &&\
echo 'upgrade success' &&\
apt -y -q -f install python3 python3-pip libeccodes-dev libffi-dev libgdal-dev &&\
apt clean &&\
echo '[global]\n\
index-url = https://mirrors.aliyun.com/pypi/simple/\n\
[install]\n\
trusted-host=mirrors.aliyun.com'\
> /etc/pip.conf &&\
pip3 install --upgrade pip &&\
pip3 install numpy &&\
pip3 install pyproj &&\
pip3 install eccodes-python &&\
pip3 install pygrib &&\
pip3 install flask &&\
pip3 install geos &&\
pip3 install netCDF4 &&\
pip3 install pygdal==3.0.4.6 &&\
pip3 install rasterio &&\
rm -rf /root/.cache/pip

CMD /bin/bash
