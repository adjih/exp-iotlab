#! /bin/sh
#---------------------------------------------------------------------------
# Create a schroot environment
# - following steps from https://wiki.ubuntu.com/DebootstrapChroot
# - man schroot.conf
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

SYSTEM=System-Ubuntu-14.04
DESC=Ubuntu-14.04
DIST=trusty

if [ "${HOME}" = "/root" ]; then
  printf "HOME does not point to user home directory (${HOME})" 
  exit 1
fi

THISUSER=`basename ${HOME}` # XXX hack


echo "*** Installing ${DESC} in ${HOME}/${SYSTEM} for user '${THISUSER}'"
printf "*** press any key to continue or [Ctrl-C] to abort: "
read whatever

apt-get install schroot debootstrap || exit 1 # script must be run as root

test -e ${HOME}/${SYSTEM} || mkdir ${HOME}/${SYSTEM}
CONF=${HOME}/${SYSTEM}/schroot.conf-part



grep -q ${SYSTEM} /etc/schroot/schroot.conf || {
  (cat <<EOF
#
# Automatically added by "$0" on `date`
#
[${DESC}]
description=${DESC}
type=directory
directory=${HOME}/${SYSTEM}
users=${THISUSER}
groups=sbuild
root-groups=${THISUSER}
aliases=${DIST}
EOF
)> ${CONF}

  ##if [ `arch` = x86_64 ] ; then
  ##  echo "personality=linux32" >> ${CONF}
  ##  #apt-get install linux32 # XXX: TODO
  ##fi

  # XXX: should try using Source chroot

  echo "--- Modifying /etc/schroot/schroot.conf, adding:"
  cat ${CONF}
  echo "-------------"
  cat ${CONF} >> /etc/schroot/schroot.conf
}

SYSTEM_ARCHIVE=${HOME}/${SYSTEM}-installed.tar.bz2 # XXX
SYSTEM_ARCHIVE=NOT-DEFINED # XXX
test -e ${SYSTEM_ARCHIVE} || SYSTEM_ARCHIVE=${HOME}/${SYSTEM}-bare.tar.gz

if [ -e ${SYSTEM_ARCHIVE} ] ; then
  echo "** Using archived system"
  #rm -rf "${HOME}/System-Ubuntu-14.04" # XXX
  tar -C ${HOME} -xpjf ${SYSTEM_ARCHIVE}
  #tar -C ${HOME} -xpjf ${HOME}/${SYSTEM}-installed.tar.bz2
else
  exit 1
  debootstrap ${DIST} ${HOME}/${SYSTEM} ftp://ftp.ubuntu.com/ubuntu
  schroot -c trusty ./update-schroot-dist.sh really-update
fi

echo  "*** you can now run: schroot -c ${DIST}"

#---------------------------------------------------------------------------
