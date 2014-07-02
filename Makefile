
-include Makefile.defs

#---------------------------------------------------------------------------
# 
#---------------------------------------------------------------------------

local:
	mkdir local
	mkdir local/download

#---------------------------------------------------------------------------
# ARM compiler
# From: https://github.com/iot-lab/iot-lab/wiki/FAQ_Gcc_arm_versions
#---------------------------------------------------------------------------

ARMGCCPKG=gcc-arm-none-eabi-4_8-2014q2-20140609-linux.tar.bz2

ensure-gcc-arm: local/gcc-arm-none/bin/arm-none-eabi-gcc

local/download/${ARMGCCPKG}:
	test -e local || make local
	cd local/download && wget https://launchpad.net/gcc-arm-embedded/4.8/4.8-2014-q2-update/+download/${ARMGCCPKG}

local/gcc-arm-none/bin/arm-none-eabi-gcc: 
	make local/download/${ARMGCCPKG}
	tar -xjvf local/download/${ARMGCCPKG} -C local
	ln -s gcc-arm-none-eabi-4_8-2014q2 local/gcc-arm-none

#--------------------------------------------------------------------------
# CLI Tools Installation
# From: https://github.com/iot-lab/iot-lab/wiki/CLI-Tools-Installation
#---------------------------------------------------------------------------

python-setuptools: /usr/share/pyshared/setuptools.egg-info

/usr/share/pyshared/setuptools.egg-info:
	@printf "Doing 'sudo apt-get install python-setuptools' [Ctrl-C to cancel]: " && read 1
	sudo apt-get install python-setuptools

#---------------------------------------------------------------------------
# Configuration
# https://www.iot-lab.info/tutorials/get-compile-a-m3-firmware-code/
#---------------------------------------------------------------------------

iot-lab:

#---------------------------------------------------------------------------
#
#---------------------------------------------------------------------------
