#! /bin/sh
#---------------------------------------------------------------------------
# copied from openlab (IoT-LAB), same copyright
#---------------------------------------------------------------------------

IMAGE=$1

if [ "$IMAGE" = "" ] ; then
  echo "$0: ERROR: Syntax: $0 <image file> [<device index>]"
  exit 1
fi

DEVICE_INDEX=$2
if [ "$DEVICE_INDEX" = "" ] ; then
  #DEVICE_INDEX_OPT="-c 'ft2232_device_index ${DEVICE_INDEX}'"
  DEVICE_INDEX=0
fi


FILE=$(readlink -f "$0")
DIR_FILE=$(dirname "${FILE}")
EXP_IOTLAB_DIR=$(dirname $(dirname ${DIR_FILE}))

OPENLAB_GIT=${EXP_IOTLAB_DIR}/iot-lab/parts/openlab

#---------------------------------------------------------------------------

# From iot-lab/parts/contiki/platform/iotlab-m3/Makefile.iotlab-m3

OOCD_TARGET=stm32f1x
#OOCD_ITF=${OPENLAB_GIT}/platform/scripts/iotlab-m3.cfg
OOCD_ITF=${DIR_FILE}/iotlab-m3.cfg
#OOCD_ITF=${DIR_FILE}/iot-lab_m3_jtag.cfg

# From iot-lab/parts/contiki/platform/openlab/Makefile.include

OOCD_PORT=123
GDB_PORT=3${OOCD_PORT}
TELNET_PORT=4${OOCD_PORT}
TCL_PORT=5${OOCD_PORT}

OOCD=openocd

${OOCD} \
    -f "${OOCD_ITF}" \
    -f "target/${OOCD_TARGET}.cfg" \
    -c "ft2232_device_index ${DEVICE_INDEX}" \
    -c "gdb_port ${GDB_PORT}" \
    -c "telnet_port ${TELNET_PORT}" \
    -c "tcl_port ${TCL_PORT}" \
    -c "init" \
    -c "targets" \
    -c "reset halt" \
    -c "reset init" \
    -c "flash write_image erase ${IMAGE}" \
    -c "verify_image ${IMAGE}" \
    -c "reset run" \
    -c "shutdown"

#    -f 'ft2232_device_desc "${DEVICE_DESC}"'

#---------------------------------------------------------------------------

#ft2232_device_desc "M3"
#ft2232_device_desc "FITECO M3"
