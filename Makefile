#---------------------------------------------------------------------------
# A meta-Makefile to:
# - download tools (cross-compilers)
# - ensure proper packages (Ubuntu)
#---------------------------------------------------------------------------
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

default: help

# All repositories variables are set in:
include Makefile.defs
-include Makefile-local.defs

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
	make really-ensure-local-dirs
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

USE_OPENLAB_DEFS=. ${CURDIR}/local/src/local.profile

#OPENLAB_EXAMPLE=example_soft_timer_delay
OPENLAB_EXAMPLE=example_event

ensure-openlab-example-m3: \
  iot-lab/parts/openlab/build.m3/bin/${OPENLAB_EXAMPLE}.elf

iot-lab/parts/openlab/build.m3/bin/${OPENLAB_EXAMPLE}.elf:
	make build-openlab-example-m3

build-openlab-example-m3: ensure-openlab-prepare
	${USE_OPENLAB_DEFS} && cd iot-lab/parts/openlab/build.m3 \
         && make ${OPENLAB_EXAMPLE}

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

run-roxterm: local/src/local.profile ensure-pkg-roxterm
	DISPLAY=:0 roxterm -e bash --init-file local/src/local.profile #XXX default .rc

run-gnome-terminal: local/src/local.profile ensure-pkg-gnome-terminal
	DISPLAY=:0 gnome-terminal --window-with-profile=base #XXX default .rc

go-trusty:
	@#schroot -c trusty make run-roxterm
	schroot -c trusty make run-gnome-terminal

ensure-local-profile: local/src/local.profile

local/src/local.profile: Makefile
	(echo "# Automagically generated" ; \
	echo "PATH=${GCCARMDIR}:${GCCMSPDIR}:${CURDIR}/iot-lab/parts/cli-tools:${CURDIR}/local/bin:$$PATH" ;  \
	echo "export PATH" ;  \
        echo "DISPLAY=:0" ;   \
        echo "export DISPLAY" \
         ) > $@

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
	cd openwsn/openwsn-fw/firmware/openos/bsp/boards/iot-lab_M3 \
        && mv uart.c uart.c-orig \
        && sed s/115200/500000/g < uart.c-orig > uart.c

openwsn/openwsn-sw:
	make openwsn
	git clone ${GIT_OPENWSN_SW} openwsn/openwsn-sw

openwsn/coap:
	make openwsn
	git clone ${GIT_OPENWSN_COAP} openwsn/coap


ensure-all-openwsn: openwsn openwsn/openwsn-fw openwsn/openwsn-sw \
        openwsn/coap openwsn/openwsn.defs

ensure-openwsn-build-deps: ensure-all-openwsn ensure-gcc-arm \
            ensure-local-profile ensure-pkg-scons ensure-pkg-python-dev \
             ensure-pkg-python-bottle \
	    ensure-python-pip ensure-pip-PyDispatcher \
           ensure-pkg-python-serial

build-all-openwsn: build-openwsn-m3 build-openwsn-a8-m3 build-openwsn-sim

build-openwsn-sim: ensure-openwsn-build-deps
	${USE_OPENWSN_DEFS} && cd openwsn/openwsn-fw \
        && scons board=python toolchain=gcc oos_openwsn

OPENWSN_SIM_OBJ=openwsn/openwsn-fw/firmware/openos/projects/common/oos_openwsn.so
ensure-openwsn-sim: ${OPENWSN_SIM_OBJ}
${OPENWSN_SIM_OBJ}: ; make build-openwsn-sim


#firmware/openos/projects/common/oos_openwsn.so
ensure-openwsn-m3: firmware/openos/projects/common/03oos_openwsn_prog

firmware/openos/projects/common/03oos_openwsn_prog:
	make build-openwsn-m3

build-openwsn-m3: ensure-openwsn-build-deps
	${USE_OPENWSN_DEFS} && cd openwsn/openwsn-fw \
        && scons board=iot-lab_M3 toolchain=armgcc oos_openwsn

build-openwsn-sink-m3: ensure-openwsn-build-deps
	${USE_OPENWSN_DEFS} && cd openwsn/openwsn-fw-sink \
        && scons board=iot-lab_M3 toolchain=armgcc oos_openwsn

build-openwsn-a8-m3: ensure-openwsn-build-deps

run-openwsn-sim: ensure-openwsn-sim ensure-openwsn-build-deps
	cd openwsn/openwsn-sw/software/openvisualizer && sudo scons runweb --sim

run-openwsn-web: ensure-openwsn-build-deps
	cd openwsn/openwsn-sw/software/openvisualizer && sudo scons runweb


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
	cd riot/thirdparty_boards/iot-lab_M3/include \
        && mv board.h board.h-orig \
        && sed s/115200/500000/g < board.h-orig > board.h

ensure-riot-cpu: riot/thirdparty_cpu

riot/thirdparty_cpu:
	make ensure-riot
	git clone ${GIT_RIOT_CPU} riot/thirdparty_cpu
	cd riot/thirdparty_cpu \
	&& git checkout -b thomaseichinger-fix_stm32f1 master \
	&& git pull --no-edit git@github.com:thomaseichinger/thirdparty_cpu.git fix_stm32f1

ensure-all-riot: ensure-riot ensure-riot-board ensure-riot-cpu

ensure-riot-build-deps: \
   ensure-all-riot ensure-gcc-arm ensure-local-profile

build-riot-helloworld: ensure-riot-build-deps 
	${USE_RIOT_DEFS} && cd riot/RIOT/examples/hello-world && make

build-riot-rpl-udp: ensure-riot-build-deps
	${USE_RIOT_DEFS} && cd riot/RIOT/examples/rpl_udp && make

ensure-riot-defaultprog: \
    riot/RIOT/examples/default/bin/iot-lab_M3/default.elf

riot/RIOT/examples/default/bin/iot-lab_M3/default.elf:
	make build-riot-defaultprog

build-riot-defaultprog: ensure-riot-build-deps
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

ensure-contiki-build-deps:  ensure-all-iot-lab ensure-openlab-prepare \
         ensure-gcc-arm ensure-local-profile

build-contiki-http-server-%: ensure-contiki-build-deps
	${USE_OPENLAB_DEFS} \
        && cd iot-lab/parts/contiki/examples/ipv6/http-server \
        && make TARGET=iotlab-$*


CONTIKI_BORDER_ROUTER_PREFIX=iot-lab/parts/contiki/examples/ipv6/rpl-border-router/border-router.iotlab

ensure-contiki-border-router-m3: ${CONTIKI_BORDER_ROUTER_PREFIX}-m3
ensure-contiki-border-router-a8-m3: ${CONTIKI_BORDER_ROUTER_PREFIX}-a8-m3

${CONTIKI_BORDER_ROUTER_PREFIX}-%: ; make build-contiki-border-router-$*

build-contiki-border-router-%: ensure-contiki-build-deps
	${USE_OPENLAB_DEFS} \
        && cd iot-lab/parts/contiki/examples/ipv6/rpl-border-router \
        && make TARGET=iotlab-$*

ensure-contiki-rpl-samples: \
    ensure-contiki-http-server-m3 ensure-contiki-border-router-m3 \
    ensure-contiki-http-server-a8-m3 ensure-contiki-border-router-a8-m3 \
    ensure-contiki-tunslip6-bin

ensure-contiki-tunslip6-bin: local/bin/tunslip6

local/bin/tunslip6:
	make really-ensure-local-dirs ensure-contiki-tunslip6-src
	gcc local/src/tunslip6.c -o $@

ensure-contiki-tunslip6-src: local/src/tunslip6.c

local/src/tunslip6.c:
	make really-ensure-local-dirs ensure-pkg-wget
	wget ${URL_TUNSLIP6} -O $@

really-ensure-local-dirs: 
	for i in local local/src local/bin local/download ; do \
             test -e $$i || mkdir $$i ; done

#build-contiki-border-router-a8-m3: ensure-all-iot-lab ensure-openlab-prepare \
#         ensure-gcc-arm
#	${USE_OPENLAB_DEFS} \
#        && cd iot-lab/parts/contiki/examples/ipv6/rpl-border-router \
#        && make TARGET=iotlab-a8-m3

#---------------------------------------------------------------------------

CONTIKI_EXAMPLE_ABC_PREFIX=iot-lab/parts/contiki/examples/rime/example-abc-fast.iotlab
#CONTIKI_EXAMPLE_ABC_PREFIX=iot-lab/parts/contiki/examples/rime/example-abc.iotlab

ensure-contiki-example-abc-m3: ${CONTIKI_EXAMPLE_ABC_PREFIX}-m3
ensure-contiki-example-abc-a8-m3: ${CONTIKI_EXAMPLE_ABC_PREFIX}-a8-m3

${CONTIKI_EXAMPLE_ABC_PREFIX}-%: ; make build-contiki-example-abc-$*

build-contiki-example-abc-%: ensure-contiki-build-deps
	${USE_OPENLAB_DEFS} \
        && cd iot-lab/parts/contiki/examples/rime \
        && make TARGET=iotlab-$* `basename ${CONTIKI_EXAMPLE_ABC_PREFIX}-$*`

#===========================================================================
#===========================================================================
# Foren6
#===========================================================================
#===========================================================================

#212-214+216+219-220+222+226-227+231-232+234-237+239+241-242+244-246+248+253-254+257-258+260+262-265+267+271-273+278+280+282+285+288-289

# https://github.com/cetic/foren6

ensure-foren6-gui: foren6/gui-qt/release/foren6 foren6

foren6:
	git clone ${GIT_FOREN6}

run-foren6: ensure-foren6-gui
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

BIN_SNIFFER_ZEP_M3=iot-lab/parts/openlab/build.m3/bin/zep_sniffer.elf
BIN_SNIFFER_ZEP_A8_M3=iot-lab/parts/openlab/build.a8-m3/bin/zep_sniffer.elf

ensure-sniffer-zep: ${BIN_SNIFFER_ZEP_M3} ${BIN_SNIFFER_ZEP_A8_M3}

build-sniffer-zep:
	make build-sniffer-zep-m3 build-sniffer-zep-a8-m3

${BIN_SNIFFER_ZEP_M3}: ; make build-sniffer-zep-m3

${BIN_SNIFFER_ZEP_A8_M3}: ; make build-sniffer-zep-a8-m3

build-sniffer-zep-m3:
	make ensure-openlab-prepare ensure-gcc-arm
	cd iot-lab/parts/openlab/build.m3 \
        && PATH=${GCCARMDIR}:${PATH} make zep_sniffer

build-sniffer-zep-a8-m3:
	make ensure-openlab-prepare ensure-gcc-arm
	cd iot-lab/parts/openlab/build.a8-m3 \
        && PATH=${GCCARMDIR}:${PATH} make zep_sniffer


#===========================================================================
#===========================================================================
# Direct flashing
#===========================================================================
#===========================================================================

#---------------------------------------------------------------------------
# You need to have a real node connected through USB to do this:

FLASHCMD=${USE_OPENWSN_DEFS} && cd openwsn/openwsn-fw/firmware/openos/bsp/boards/iot-lab_M3/tools && ./flash.sh

direct-flash-openwsn-m3: ensure-openwsn-m3
	${FLASHCMD} ../../../../../../firmware/openos/projects/common/03oos_openwsn_prog

IOTLAB_EX1=iot-lab/parts/openlab/build.m3/bin/example_soft_timer_delay.elf

direct-flash-openlab-example-m3: ensure-openlab-example-m3
	${FLASHCMD} ${CURDIR}/iot-lab/parts/openlab/build.m3/bin/${OPENLAB_EXAMPLE}.elf
	make direct-miniterm-m3

direct-flash-sniffer-foren6-m3: ensure-sniffer-foren6
	${FLASHCMD} ${CURDIR}/${BIN_SNIFFER_FOREN6_M3}
	make direct-miniterm-m3

direct-flash-sniffer-zep-m3: ensure-sniffer-zep
	make build-sniffer-zep-m3
	${FLASHCMD} ${CURDIR}/${BIN_SNIFFER_ZEP_M3}
	${CURDIR}/iot-lab/parts/openlab/appli/iotlab_tests/zep_sniffer/serial2loopback.py


#direct-flash-openwsn-m3: ensure-openwsn-m3
#	${USE_OPENWSN_DEFS} && cd openwsn/openwsn-fw/firmware/openos/bsp/boards/iot-lab_M3/tools && ./flash.sh ../../../../../../firmware/openos/projects/common/03oos_openwsn_prog

direct-flash-contiki-http-server-m3: ensure-contiki-http-server-m3
	 ${FLASHCMD} ${CURDIR}/${CONTIKI_HTTP_SERVER_PREFIX}-m3
	make direct-miniterm-m3

direct-flash-contiki-border-router-m3: ensure-contiki-border-router-m3
	 ${FLASHCMD} ${CURDIR}/${CONTIKI_BORDER_ROUTER_PREFIX}-m3
	make direct-miniterm-m3

direct-flash-contiki-example-abc-m3: ensure-contiki-example-abc-m3
	 ${FLASHCMD} ${CURDIR}/${CONTIKI_EXAMPLE_ABC_PREFIX}-m3
	make direct-miniterm-m3

rebuild-contiki:
	cd iot-lab/parts/contiki/examples/ipv6/http-server \
	&& make clean -C

#direct-flash-contiki-example-abc-fast-m3: ensure-contiki-example-abc-fast-m3
#	 ${FLASHCMD} ${CURDIR}/${CONTIKI_EXAMPLE_ABC_FAST_PREFIX}-m3
#	make direct-miniterm-m3

#---------------------------------------------------------------------------
# New commands with python (and patched OCD)

CMDLASTM3=python ${CURDIR}/tools/misc/UsbHelper.py last-m3

direct-miniterm-m3:
	miniterm.py `${CMDLASTM3}` 500000

lsusb:
	python tools/misc/UsbHelper.py



# You don't need this. If you need this, you can type directly the cmds:
CMDJTAG=python ${CURDIR}/tools/misc/usbCmd.py 

do-patch-openocd:
	cd ./tools/misc/extra && sudo ./do-patch-ocd-on-ubuntu-14.04.sh

I=${CURDIR}/iot-lab/parts/contiki/examples/ipv6

dbg-start-servers:
	${CMDJTAG} --auto-port --roxterm --device-index 0 server
	${CMDJTAG} --auto-port --roxterm --device-index 1 server

dbg-clean:
	cd iot-lab/parts/contiki/examples/ipv6 \
          && (cd rpl-border-router && rm -rf *.a *.iotlab-m3 obj_iotlab-m3 ) \
          && (cd http-server && rm -rf *.a *.iotlab-m3 obj_iotlab-m3 )

dbg-compile:
	cd iot-lab/parts/contiki/examples/ipv6 \
          && (cd rpl-border-router && make TARGET=iotlab-m3) \
          && (cd http-server && make TARGET=iotlab-m3)

DBGCLIENT=${CMDJTAG} --auto-port --client --device-index

DBG_FW_BR=${I}/rpl-border-router/border-router.iotlab-m3
DBG_FW_R=${I}/http-server/http-server.iotlab-m3

#DBG_FW_BR=tools/PreCompiled/border-router.iotlab-m3
#DBG_FW_R=tools/PreCompiled/http-server.iotlab-m3

dbg-reflash:
	${DBGCLIENT} 0 flash ${DBG_FW_BR}
	${DBGCLIENT} 1 flash ${DBG_FW_R}

dbg-reset:
	${DBGCLIENT} 0 send reset
	${DBGCLIENT} 1 send reset

dbg-halt:
	${DBGCLIENT} 0 send "reset halt"
	${DBGCLIENT} 1 send "reset halt"

dbg-tty:
	${DBGCLIENT} 1 tty

dbg-tunslip:
	@#roxterm -e bash -c
	sudo local/bin/tunslip6 -B 500000 -s `${DBGCLIENT} 0 print-tty` aaaa::1/64


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

# Don't use this version of python requests:
#ensure-pkg-python-requests: /usr/share/doc/python-requests/copyright
#/usr/share/doc/python-requests/copyright: ; make install-ubuntu-pkg PKGNAME='python-requests'

ensure-pkg-scons: /usr/bin/scons
/usr/bin/scons: ; make install-ubuntu-pkg PKGNAME='scons'

ensure-pkg-python-dev: /usr/bin/python-config
/usr/bin/python-config: ; make install-ubuntu-pkg PKGNAME='python-dev'

ensure-pkg-wget: /usr/bin/wget
/usr/bin/wget: ; make install-ubuntu-pkg PKGNAME='wget'

ensure-pkg-python-bottle: /usr/share/doc/python-bottle/copyright
/usr/share/doc/python-bottle/copyright:
	make install-ubuntu-pkg PKGNAME='python-bottle'

ensure-pkg-roxterm: /usr/bin/roxterm
/usr/bin/roxterm: ; make install-ubuntu-pkg PKGNAME='roxterm'

ensure-pkg-socat: /usr/bin/socat
/usr/bin/socat: ; make install-ubuntu-pkg PKGNAME='socat'

ensure-pkg-python-serial: /usr/share/doc/python-serial/copyright
/usr/share/doc/python-serial/copyright:
	make install-ubuntu-pkg PKGNAME='python-serial'

ensure-pkg-gnome-terminal: /usr/bin/gnome-terminal
/usr/bin/gnome-terminal: ; make install-ubuntu-pkg PKGNAME='gnome-terminal'

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
	sudo apt-get install -y ${PKGNAME}

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

rpl-exp-deps: \
   ensure-contiki-rpl-samples ensure-sniffer-foren6 ensure-foren6-gui \
   ensure-all-iot-lab \
   ensure-pkg-roxterm ensure-pkg-socat \
   ensure-openlab-example-m3

#ensure-pkg-wireshark ensure-pkg-paramiko

run-rpl-experiment: rpl-exp-deps
	cd tools && python ExpRpl.py --site grenoble --nb 10

#---------------------------------------------------------------------------

riot-rpl-exp-deps: \
   ensure-all-iot-lab

#---------------------------------------------------------------------------

build-radio-test: ensure-openlab-prepare
	${USE_OPENLAB_DEFS} && cd iot-lab/parts/openlab/build.m3 \
         && make radio_test

#---------------------------------------------------------------------------