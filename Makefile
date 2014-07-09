#---------------------------------------------------------------------------
# A meta-Makefile to:
# - download tools (cross-compilers)
# - ensure proper packages (Ubuntu)
#---------------------------------------------------------------------------
# Cedric Adjih - Inria 2014
#---------------------------------------------------------------------------

# All repositories variables are set in:
include Makefile.defs
-include Makefile-local.defs

default: help

#===========================================================================
#===========================================================================
# Tools
#===========================================================================
#===========================================================================

#---------------------------------------------------------------------------
# ARM cross-compiler
# From: https://github.com/iot-lab/iot-lab/wiki/FAQ_Gcc_arm_versions
#---------------------------------------------------------------------------

ifeq (${WITH_PKG_GCC_ARM},yes)

# gcc-arm from Ubuntu packages
ensure-gcc-arm: ensure-pkg-gcc-arm

ensure-pkg-gcc-arm: /usr/bin/arm-none-eabi-gcc
/usr/bin/arm-none-eabi-gcc:
	make install-ubuntu-pkg PKGNAME='gcc-arm-none-eabi'

else

# gcc-arm as indicated in the IoT-LAB tutorial
GCCARMPKG=gcc-arm-none-eabi-4_8-2014q2-20140609-linux.tar.bz2
GCCARMDIR=${CURDIR}/local/gcc-arm-none/bin

ensure-gcc-arm: local/gcc-arm-none/bin/arm-none-eabi-gcc

local/download/${GCCARMPKG}: ensure-pkg-wget
	test -e local || make local
	cd local/download && wget https://launchpad.net/gcc-arm-embedded/4.8/4.8-2014-q2-update/+download/${GCCARMPKG}

local/gcc-arm-none/bin/arm-none-eabi-gcc: 
	make local/download/${GCCARMPKG}
	tar -xjvf local/download/${GCCARMPKG} -C local
	ln -s gcc-arm-none-eabi-4_8-2014q2 local/gcc-arm-none

endif

#---------------------------------------------------------------------------
# MSP430 cross-compiler
# WAS: from: iot-lab/parts/wsn430/README.md 
# REPLACED BY: from gcc-msp430 (from Ubuntu 14.04)
#---------------------------------------------------------------------------

ifeq (${WITH_PKG_GCC_MSP430},yes)

# MSP430 from Ubuntu packages
ensure-gcc-msp430: ensure-pkg-gcc-msp430

ensure-pkg-gcc-msp430: /usr/bin/msp430-gcc
/usr/bin/msp430-gcc:
	make install-ubuntu-pkg PKGNAME='gcc-msp430'

else

# MSP430 from Zolertia site (as described in IoT-LAB tutorial)
GCCMSPPKG=msp430-z1.tar.gz
GCCMSPDIR=${CURDIR}/local/msp430/bin

ensure-gcc-msp430: local/msp430/bin/msp430-gcc

local/download/${GCCMSPPKG}: ensure-pkg-wget
	test -e local || make local
	cd local/download && wget http://sourceforge.net/projects/zolertia/files/Toolchain/${GCCMSPPKG}

local/msp430/bin/msp430-gcc: 
	make local/download/${GCCMSPPKG}
	tar -xzvf local/download/${GCCMSPPKG} -C local
	ln -s msp430-z1 local/msp430

endif

#--------------------------------------------------------------------------
# CLI Tools Installation
# From: https://github.com/iot-lab/iot-lab/wiki/CLI-Tools-Installation
# (not used ; we use from github instead)
#---------------------------------------------------------------------------

#python-setuptools: /usr/share/pyshared/setuptools.egg-info

#/usr/share/pyshared/setuptools.egg-info:
#	@printf "Doing 'sudo apt-get install python-setuptools' [Ctrl-C to cancel]: " && read 1
#	sudo apt-get install python-setuptools

#===========================================================================
#===========================================================================
# IoT-LAB
#===========================================================================
#===========================================================================

#---------------------------------------------------------------------------
# Configuration
# https://www.iot-lab.info/tutorials/get-compile-a-m3-firmware-code/
#
# We are not using iot-lab/Makefile to download subprojects 
# in order to allow forking
#---------------------------------------------------------------------------

ensure-iot-lab: iot-lab/Makefile

iot-lab/Makefile:
	git clone ${GIT_IOTLAB}


ensure-cli-tools: ensure-pip-requests iot-lab/parts/cli-tools

iot-lab/parts/cli-tools: # <- no deps (is intended)
	make ensure-iot-lab # ^^^^^^^
	git clone ${GIT_IOTLAB_CLITOOLS} iot-lab/parts/cli-tools

ensure-openlab: iot-lab/parts/openlab

iot-lab/parts/openlab: 
	make ensure-iot-lab
	git clone ${GIT_IOTLAB_OPENLAB} iot-lab/parts/openlab

ensure-contiki: iot-lab/parts/contiki

iot-lab/parts/contiki: 
	make ensure-iot-lab
	git clone ${GIT_IOTLAB_CONTIKI} iot-lab/parts/contiki

ensure-wsn430: iot-lab/parts/wsn430

iot-lab/parts/wsn430: 
	make ensure-iot-lab
	git clone ${GIT_IOTLAB_WSN430} iot-lab/parts/wsn430

ensure-all-iot-lab:  ensure-iot-lab ensure-cli-tools \
   ensure-openlab ensure-contiki ensure-wsn430

#---------------------------------------------------------------------------
# openlabs/README_COMPILING
# Prepare env for M3, A8-M3, agile-fox
#---------------------------------------------------------------------------

ensure-openlab-prepare: \
  iot-lab/parts/openlab/build.m3/CMakeFiles \
  iot-lab/parts/openlab/build.a8-m3/CMakeFiles \
  iot-lab/parts/openlab/build.fox/CMakeFiles

iot-lab/parts/openlab/build.m3/CMakeFiles \
  iot-lab/parts/openlab/build.a8-m3/CMakeFiles \
  iot-lab/parts/openlab/build.fox/CMakeFiles:
	make prepare-openlab

prepare-openlab: ensure-pkg-cmake ensure-pkg-g++ ensure-openlab
	@#export PATH=${GCCARMDIR}:${PATH} && 
	for subdir in m3 a8-m3 fox ; do \
	    test -e iot-lab/parts/openlab/build.$${subdir} \
           || mkdir iot-lab/parts/openlab/build.$${subdir} ; \
        done
	cd iot-lab/parts/openlab/build.m3 && cmake .. -DPLATFORM=iotlab-m3
	cd iot-lab/parts/openlab/build.a8-m3 && cmake .. -DPLATFORM=iotlab-a8-m3
	cd iot-lab/parts/openlab/build.fox && cmake .. -DPLATFORM=agile-fox

#---------------------------------------------------------------------------

build-tutorial-m3: ensure-openlab-prepare
	export PATH=${GCCARMDIR}:${PATH} \
        && cd iot-lab/parts/openlab/build.m3 && make tutorial_m3 PATH=$$PATH

build-tutorial-a8-m3: ensure-openlab-prepare
	export PATH=${GCCARMDIR}:${PATH} \
        && cd iot-lab/parts/openlab/build.a8-m3 && make tutorial_m3 PATH=$$PATH

# see: iot-lab/parts/wsn430/README.md
build-samples-wsn430: ensure-wsn430 ensure-gcc-msp430
	export PATH=${GCCMSPDIR}:${PATH} \
        && cd iot-lab/parts/wsn430 && make -f iotlab.makefile PATH=$$PATH

#---------------------------------------------------------------------------

run-bash: local/src/local.profile
	bash --init-file local/src/local.profile #XXX default .rc

ensure-local-profile: local/src/local.profile

local/src/local.profile: Makefile
	(echo "# Automagically generated" ; \
	echo "PATH=${GCCARMDIR}:${GCCMSPDIR}:${CURDIR}/local/bin:$$PATH" ; \
	echo "export PATH") > $@

#===========================================================================
#===========================================================================
# OpenWSN
#===========================================================================
#===========================================================================
# See also: https://openwsn.atlassian.net/wiki/display/OW/Kickstart+Linux

USE_OPENWSN_DEFS=. ${CURDIR}/openwsn/openwsn.defs \
        && . ${CURDIR}/local/src/local.profile

ensure-openwsn: openwsn 

openwsn/openwsn.defs: Makefile
	(echo "# Automagically generated" ; \
	echo "true" ) > $@

openwsn:
	mkdir openwsn

openwsn/openwsn-fw:
	make openwsn
	git clone ${GIT_OPENWSN_FW} openwsn/openwsn-fw

openwsn/openwsn-sw:
	make openwsn
	git clone ${GIT_OPENWSN_SW} openwsn/openwsn-sw

openwsn/coap:
	make openwsn
	git clone ${GIT_OPENWSN_COAP} openwsn/coap


ensure-all-openwsn: openwsn openwsn/openwsn-fw openwsn/openwsn-sw \
        openwsn/coap openwsn/openwsn.defs

ensure-openwsn-deps: ensure-all-openwsn ensure-gcc-arm \
            ensure-local-profile ensure-pkg-scons ensure-pkg-python-dev \
             ensure-pkg-python-bottle \
	    ensure-python-pip ensure-pip-PyDispatcher \
           ensure-pkg-python-serial

build-all-openwsn: build-openwsn-m3 build-openwsn-a8-m3 build-openwsn-sim

build-openwsn-sim: ensure-openwsn-deps
	${USE_OPENWSN_DEFS} && cd openwsn/openwsn-fw \
        && scons board=python toolchain=gcc oos_openwsn

OPENWSN_SIM_OBJ=openwsn/openwsn-fw/firmware/openos/projects/common/oos_openwsn.so
ensure-openwsn-sim: ${OPENWSN_SIM_OBJ}
${OPENWSN_SIM_OBJ}: ; make build-openwsn-sim

#firmware/openos/projects/common/oos_openwsn.so

build-openwsn-m3: ensure-openwsn-deps
	${USE_OPENWSN_DEFS} && cd openwsn/openwsn-fw \
        && scons board=iot-lab_M3 toolchain=armgcc oos_openwsn

build-openwsn-a8-m3: ensure-openwsn-deps

run-openwsn-sim: ensure-openwsn-sim ensure-openwsn-deps
	cd openwsn/openwsn-sw/software/openvisualizer && sudo scons runweb --sim

#===========================================================================
#===========================================================================
# RIOT-OS
#===========================================================================
#===========================================================================

USE_RIOT_DEFS=. ${CURDIR}/riot/riot.defs \
        && . ${CURDIR}/local/src/local.profile

ensure-riot: riot riot/RIOT riot/riot.defs

riot/riot.defs: Makefile
	(echo "# Automagically generated" ; \
	echo "BOARD=iot-lab_M3" ; \
	echo "RIOTCPU=${CURDIR}/riot/thirdparty_cpu" ; \
	echo "RIOTBOARD=${CURDIR}/riot/thirdparty_boards" ; \
	echo "export BOARD RIOTCPU RIOTBOARD") > $@

riot:
	mkdir riot

riot/RIOT:
	make riot
	git clone ${GIT_RIOT} riot/RIOT

ensure-riot-board: riot/thirdparty_boards

riot/thirdparty_boards:
	make ensure-riot
	git clone ${GIT_RIOT_BOARD} riot/thirdparty_boards

ensure-riot-cpu: riot/thirdparty_cpu

riot/thirdparty_cpu:
	make ensure-riot
	git clone ${GIT_RIOT_CPU} riot/thirdparty_cpu

ensure-all-riot: ensure-riot ensure-riot-board ensure-riot-cpu

build-riot-helloworld: ensure-all-riot ensure-gcc-arm ensure-local-profile
	${USE_RIOT_DEFS} && cd riot/RIOT/examples/hello-world && make

build-riot-rpl-udp: ensure-all-riot ensure-gcc-arm ensure-local-profile
	${USE_RIOT_DEFS} && cd riot/RIOT/examples/rpl_udp && make

build-riot-default: ensure-all-riot ensure-gcc-arm ensure-local-profile
	${USE_RIOT_DEFS} && cd riot/RIOT/examples/default && make


#===========================================================================
#===========================================================================
# Contiki
#===========================================================================
#===========================================================================

USE_OPENLAB_DEFS=. ${CURDIR}/local/src/local.profile


CONTIKI_HTTP_SERVER_PREFIX=iot-lab/parts/contiki/examples/ipv6/http-server/http-server.iotlab

ensure-contiki-http-server-m3: ${CONTIKI_HTTP_SERVER_PREFIX}-m3
ensure-contiki-http-server-a8-m3: ${CONTIKI_HTTP_SERVER_PREFIX}-a8-m3

${CONTIKI_HTTP_SERVER_PREFIX}-%: ; make build-contiki-http-server-$*

build-contiki-http-server-%: ensure-all-iot-lab ensure-openlab-prepare \
         ensure-gcc-arm
	${USE_OPENLAB_DEFS} \
        && cd iot-lab/parts/contiki/examples/ipv6/http-server \
        && make TARGET=iotlab-$*


CONTIKI_BORDER_ROUTER_PREFIX=iot-lab/parts/contiki/examples/ipv6/rpl-border-router/border-router.iotlab

ensure-contiki-border-router-m3: ${CONTIKI_BORDER_ROUTER_PREFIX}-m3
ensure-contiki-border-router-a8-m3: ${CONTIKI_BORDER_ROUTER_PREFIX}-a8-m3

${CONTIKI_BORDER_ROUTER_PREFIX}-%: ; make build-contiki-border-router-$*

build-contiki-border-router-%: ensure-all-iot-lab ensure-openlab-prepare \
         ensure-gcc-arm
	${USE_OPENLAB_DEFS} \
        && cd iot-lab/parts/contiki/examples/ipv6/rpl-border-router \
        && make TARGET=iotlab-$*

ensure-contiki-rpl-samples: \
    ensure-contiki-http-server-m3 ensure-contiki-border-router-m3 \
    ensure-contiki-http-server-a8-m3 ensure-contiki-border-router-a8-m3

#build-contiki-border-router-a8-m3: ensure-all-iot-lab ensure-openlab-prepare \
#         ensure-gcc-arm
#	${USE_OPENLAB_DEFS} \
#        && cd iot-lab/parts/contiki/examples/ipv6/rpl-border-router \
#        && make TARGET=iotlab-a8-m3

#===========================================================================
#===========================================================================
# Foren6
#===========================================================================
#===========================================================================

# https://github.com/cetic/foren6

ensure-foren6-compile: foren6/gui-qt/release/foren6 foren6

foren6:
	git clone ${GIT_FOREN6}

run-foren6: ensure-foren6-compile
	cd foren6 && make run

foren6/gui-qt/release/foren6: 
	make ensure-foren6-deps foren6
	cd foren6 && make all

ensure-foren6-deps: ensure-pkg-g++ ensure-pkg-cmake \
   ensure-pkg-tshark ensure-pkg-libpcap0.8-dev ensure-pkg-libexpat1-dev \
   ensure-pkg-qt4-qmake ensure-pkg-libqt4-dev


#--------------------------------------------------

BIN_SNIFFER_FOREN6_M3=iot-lab/parts/openlab/build.m3/bin/foren6_sniffer.elf
BIN_SNIFFER_FOREN6_A8_M3=iot-lab/parts/openlab/build.a8-m3/bin/foren6_sniffer.elf

ensure-sniffer-foren6: ${BIN_SNIFFER_FOREN6_M3} ${BIN_SNIFFER_FOREN6_A8_M3}

build-sniffer-foren6:
	make build-sniffer-foren6-m3 build-sniffer-foren6-a8-m3

${BIN_SNIFFER_FOREN6_M3}: ; make build-sniffer-foren6-m3

${BIN_SNIFFER_FOREN6_A8_M3}: ; make build-sniffer-foren6-a8-m3

build-sniffer-foren6-m3:
	make ensure-openlab-prepare ensure-gcc-arm
	cd iot-lab/parts/openlab/build.m3 \
        && PATH=${GCCARMDIR}:${PATH} make foren6_sniffer

build-sniffer-foren6-a8-m3:
	make ensure-openlab-prepare ensure-gcc-arm
	cd iot-lab/parts/openlab/build.a8-m3 \
        && PATH=${GCCARMDIR}:${PATH} make foren6_sniffer

#--------------------------------------------------

#===========================================================================
#===========================================================================
# Local installation
#===========================================================================
#===========================================================================

#---------------------------------------------------------------------------
# Local repository
#---------------------------------------------------------------------------

help:
	@echo "<read the Makefile.defs, Makefile, sorry>"

local:
	mkdir local
	mkdir local/download local/src

#---------------------------------------------------------------------------
# Ubuntu dependencies
#---------------------------------------------------------------------------
# XXX: test that the OS is ubuntu
# XXX: this can be simplified

ensure-pkg-cmake: /usr/bin/cmake
/usr/bin/cmake: ; make install-ubuntu-pkg PKGNAME='cmake'

ensure-pkg-g++: /usr/bin/g++
/usr/bin/g++: ; make install-ubuntu-pkg PKGNAME='g++'

ensure-pkg-tshark: /usr/bin/tshark
/usr/bin/tshark: ; make install-ubuntu-pkg PKGNAME='tshark'

ensure-pkg-qt4-qmake: /usr/bin/qmake-qt4
/usr/bin/qmake-qt4: ; make install-ubuntu-pkg PKGNAME='qt4-qmake'

ensure-pkg-libpcap0.8-dev: /usr/include/pcap/pcap.h
/usr/include/pcap/pcap.h: ; make install-ubuntu-pkg PKGNAME='libpcap0.8-dev'

ensure-pkg-libexpat1-dev: /usr/include/expat.h
/usr/include/expat.h: ; make install-ubuntu-pkg PKGNAME='libexpat1-dev'

ensure-pkg-libqt4-dev: /usr/include/qt4/Qt/QtGui
/usr/include/qt4/Qt/QtGui: ; make install-ubuntu-pkg PKGNAME='libqt4-dev'

# XXX NO?:
ensure-pkg-python-requests: /usr/share/doc/python-requests/copyright
/usr/share/doc/python-requests/copyright: ; make install-ubuntu-pkg PKGNAME='python-requests'

ensure-pkg-scons: /usr/bin/scons
/usr/bin/scons: ; make install-ubuntu-pkg PKGNAME='scons'

ensure-pkg-python-dev: /usr/bin/python-config
/usr/bin/python-config: ; make install-ubuntu-pkg PKGNAME='python-dev'

ensure-pkg-wget: /usr/bin/wget
/usr/bin/wget: ; make install-ubuntu-pkg PKGNAME='wget'

ensure-pkg-python-bottle: /usr/share/doc/python-bottle/copyright
/usr/share/doc/python-bottle/copyright:
	make install-ubuntu-pkg PKGNAME='python-bottle'

ensure-pkg-python-serial: /usr/share/doc/python-serial/copyright
/usr/share/doc/python-serial/copyright:
	make install-ubuntu-pkg PKGNAME='python-serial'

ensure-pip-PyDispatcher: /usr/local/lib/python2.7/dist-packages/pydispatch/__init__.py
/usr/local/lib/python2.7/dist-packages/pydispatch/__init__.py:
	make install-pip-pkg PKGNAME='PyDispatcher'

ensure-pip-requests: /usr/local/lib/python2.7/dist-packages/requests/__init__.py
/usr/local/lib/python2.7/dist-packages/requests/__init__.py:
	make install-pip-pkg PKGNAME='requests<=1.2.3'

# Problem with python-pip, see:
# https://bugs.launchpad.net/ubuntu/+source/python-pip/+bug/1306991
#
#ensure-pkg-python-pip: /usr/bin/pip
#/usr/bin/pip: ; make install-ubuntu-pkg PKGNAME='python-pip'

ensure-python-pip: /usr/local/bin/pip

ifeq (${WITH_UBUNTU_APTGET_INSTALL},yes)

/usr/local/bin/pip:
	make ensure-pkg-wget
	test -e local || make local
	cd local/download && wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
	@printf "Doing 'sudo python get-pip.py' [Ctrl-C to cancel]: " \
             && read ENTER
	cd local/download && sudo python get-pip.py

#--------------------------------------------------

install-ubuntu-pkg:
	@printf "Doing 'sudo apt-get install ${PKGNAME}' [Ctrl-C to cancel]: " \
             && read ENTER
	sudo apt-get install ${PKGNAME}

install-pip-pkg:
	@printf "Doing 'sudo pip install ${PKGNAME}' [Ctrl-C to cancel]: " \
             && read ENTER
	sudo pip install "${PKGNAME}"

#---------------------------------------------------------------------------

else

/usr/local/bin/pip:
	echo "Please install /usr/local/bin/pip or change Makefile"

install-ubuntu-pkg:
	echo "Please install ubuntu package ${PKGNAME} or change Makefile"

install-pip-pkg:
	echo "Please install python pip package ${PKGNAME} or change Makefile"

endif

#===========================================================================
#===========================================================================
# Convenience
#===========================================================================
#===========================================================================

download-nearly-all: local local/download/${GCCARMPKG}\
         local/download/${GCCMSPPKG} \
        ensure-all-iot-lab ensure-all-openwsn ensure-all-riot foren6

pack-nearly-all:
	tar -czvf external-download.tar.gz \
             local/download/${GCCARMPKG} local/download/${GCCMSPPKG} \
             iot-lab openwsn riot foren6

#-- most pkgs:

PKGLIST=cmake g++ tshark qt4-qmake libpcap0.8-dev libexpat1-dev libqt4-dev \
        python-dev scons python-bottle python-serial python-tk

install-all-ubuntu-pkg:
	make install-ubuntu-pkg PKGNAME="${PKGLIST}"

PIPPKGLIST=PyDispatcher

install-all-pip-pkg: /usr/bin/pip
	make install-ubuntu-pkg PKGNAME="${PIPPKGLIST}"

install-all-pkg: install-all-ubuntu-pkg install-all-pip-pkg

#===========================================================================
#===========================================================================
# Running
#===========================================================================
#===========================================================================

ensure-auth-info: ${HOME}/.iotlabrc

${HOME}/.iotlabrc:
	@if [ "$${IOTLAB_USER}" = "" ] ; then \
   echo "use: make ensure-auth-info IOTLAB_USER=<IoT-LAB username>"; \
   echo "or use: ./iotlab/parts/cli-tools/auth-cli -u <IoT-LAB username>"; \
           exit 1 ; \
        fi
	${CURDIR}/iot-lab/parts/cli-tools/auth-cli -u ${IOTLAB_USER}

#---------------------------------------------------------------------------
