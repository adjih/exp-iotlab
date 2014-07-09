#! /bin/sh
#---------------------------------------------------------------------------
# Update the debootstrap distribution: add necessary packages
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

NAME=trusty

if [ "$1" != "really-update" ] ; then
  echo "Command not launched with secret arg (don't run it on your system!)"
  exit 1
fi


grep -q multiverse /etc/apt/sources.list || (
echo "
(cat <<EOF
deb http://security.ubuntu.com/ubuntu ${NAME}-security main restricted
deb http://archive.ubuntu.com/ubuntu/ ${NAME}-updates main restricted

deb http://archive.ubuntu.com/ubuntu/ ${NAME} universe multiverse
deb http://security.ubuntu.com/ubuntu ${NAME}-security universe multiverse
deb http://archive.ubuntu.com/ubuntu/ ${NAME}-updates universe multiverse
EOF
 ) >> /etc/apt/sources.list
apt-get update || exit 1

apt-get install git make vim jed \
    wget cmake g++ tshark qt4-qmake libpcap0.8-dev libexpat1-dev \
    libqt4-dev python-dev scons python-bottle python-serial \
  || exit 1

(cd /tmp ;
wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py ;
python get-pip.py )

pip install PyDispatcher
pip install 'requests<=1.2.3'

#---------------------------------------------------------------------------
