#---------------------------------------------------------------------------
# A meta-Makefile to:
# - download tools (cross-compilers)
# - ensure proper packages (Ubuntu)
#---------------------------------------------------------------------------
# Cedric Adjih - Inria 2014
#---------------------------------------------------------------------------

# All repositories variables are set in:
include Makefile.defs

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

GCCARMPKG=gcc-arm-none-eabi-4_8-2014q2-20140609-linux.tar.bz2
GCCARMDIR=${CURDIR}/local/gcc-arm-none/bin

ensure-gcc-arm: local/gcc-arm-none/bin/arm-none-eabi-gcc

local/download/${GCCARMPKG}:
	test -e local || make local
	cd local/download && wget https://launchpad.net/gcc-arm-embedded/4.8/4.8-2014-q2-update/+download/${GCCARMPKG}

local/gcc-arm-none/bin/arm-none-eabi-gcc: 
	make local/download/${GCCARMPKG}
	tar -xjvf local/download/${GCCARMPKG} -C local
	ln -s gcc-arm-none-eabi-4_8-2014q2 local/gcc-arm-none

#---------------------------------------------------------------------------
# MSP430 cross-compiler
# from: iot-lab/parts/wsn430/README.md
#---------------------------------------------------------------------------

GCCMSPPKG=msp430-z1.tar.gz
GCCMSPDIR=${CURDIR}/local/msp430/bin

ensure-gcc-msp430: local/msp430/bin/msp430-gcc

local/download/${GCCMSPPKG}:
	test -e local || make local
	cd local/download && wget http://sourceforge.net/projects/zolertia/files/Toolchain/${GCCMSPPKG}

local/msp430/bin/msp430-gcc: 
	make local/download/${GCCMSPPKG}
	tar -xzvf local/download/${GCCMSPPKG} -C local
	ln -s msp430-z1 local/msp430

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


ensure-cli-tools: ensure-pkg-python-requests iot-lab/parts/cli-tools

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

prepare-openlab: ensure-pkg-cmake ensure-pkg-g++
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
build-samples-wsn430: ensure-wsn430
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

#ensure-openwsn:

#===========================================================================
#===========================================================================
# RIOT-OS
#===========================================================================
#===========================================================================

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
	. ${CURDIR}/riot/riot.defs \
        && . ${CURDIR}/local/src/local.profile \
        && cd riot/RIOT/examples/hello-world && make

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

${BIN_SNIFFER_FOREN6_M3}:
	make ensure-openlab-prepare ensure-gcc-arm
	cd iot-lab/parts/openlab/build.m3 \
        && PATH=${GCCARMDIR}:${PATH} make foren6_sniffer

${BIN_SNIFFER_FOREN6_A8_M3}:
	make ensure-openlab-prepare ensure-gcc-arm
	cd iot-lab/parts/openlab/build.a8-m3 \
        && PATH=${GCCARMDIR}:${PATH} make foren6_sniffer

#===========================================================================
#===========================================================================
# Local installation
#===========================================================================
#===========================================================================

#---------------------------------------------------------------------------
# Local repository
#---------------------------------------------------------------------------

help:
	@echo "<read the Makefile, sorry>"

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

ensure-pkg-python-requests: /usr/share/doc/python-requests/copyright
/usr/share/doc/python-requests/copyright: ; make install-ubuntu-pkg PKGNAME='python-requests'

#-- all:

PKGLIST=cmake g++ tshark qt4-qmake libpcap0.8-dev libexpat1-dev libqt4-dev \
        python-requests

install-all-ubuntu-pkg:
	make install-ubuntu-pkg PKGNAME="${PKGLIST}"

#--------------------------------------------------

install-ubuntu-pkg:
	@printf "Doing 'sudo apt-get install ${PKGNAME}' [Ctrl-C to cancel]: " \
             && read ENTER
	sudo apt-get install ${PKGNAME}

#---------------------------------------------------------------------------

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
