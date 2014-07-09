#! /bin/sh
#---------------------------------------------------------------------------
# Update the debootstrap distribution: add necessary packages
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

NAME=trusty

if [ "$1" != "really-update" ] ; then
  echo "$0: Error: Command not launched with secret arg (check before running on your real system - it must also be Ubuntu trusty)"
  exit 1
fi

if [ "$2" != "" ] ; then
  NAME=$2
fi

grep -q multiverse /etc/apt/sources.list || (
  echo "Updating /etc/apt/sources.list (adding multiverse)"
(cat <<EOF
deb http://security.ubuntu.com/ubuntu ${NAME}-security main restricted
deb http://archive.ubuntu.com/ubuntu/ ${NAME}-updates main restricted

deb http://archive.ubuntu.com/ubuntu/ ${NAME} universe multiverse
deb http://security.ubuntu.com/ubuntu ${NAME}-security universe multiverse
deb http://archive.ubuntu.com/ubuntu/ ${NAME}-updates universe multiverse
EOF
 ) >> /etc/apt/sources.list
apt-get update || exit 1
)

apt-get install -y git make vim jed \
    wget cmake g++ tshark qt4-qmake libpcap0.8-dev libexpat1-dev \
    libqt4-dev python-dev scons python-bottle python-serial python-tk \
  gcc-msp430 || exit 1

if [ `arch` = x86_64 ] ; then
  # http://www.unixmen.com/enable-32-bit-support-64-bit-ubuntu-13-10-greater/
  # 32 bit binaries (for arm-gcc)
  dpkg --add-architecture i386
  apt-get update
  apt-get install -y libstdc++6:i386 # maybe gcc-arm needs less, but this works
fi

(cd /tmp ;
wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py ;
python get-pip.py )

pip install PyDispatcher
pip install 'requests<=1.2.3'

#---------------------------------------------------------------------------
