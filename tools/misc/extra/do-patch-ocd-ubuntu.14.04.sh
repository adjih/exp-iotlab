#! /bin/sh
	
test `lsb_release -c -s` = "trusty"  || exit 1 # need this distrib.
cd local/src || cd ../../../local/src || exit 1
apt-get install -y cdbs build-essential texlive \
     software-properties-common gdebi-core || exit 1
add-apt-repository -s "http://archive.ubuntu.com/ubuntu/ trusty main"
apt-get update
apt-get source openocd || exit 1

apt-get install openocd
OCDVER=0.7.0
cd openocd-${OCDVER} || exit 1
patch -p1 < ../../../tools/misc/extra/openocd-0.7.0-device-index.patch \
  || exit 1
#dpkg-buildpackage
make -f debian/rules binary || exit 1
cd .. 
gdebi -n openocd_${OCDVER}*.deb
