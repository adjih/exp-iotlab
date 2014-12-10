This file documents some differences between two kind of M3 nodes of IoT-LAB:


* The [M3 Open Nodes](https://www.iot-lab.info/hardware/m3/)
* The M3 nodes embedded in the [A8 Open Nodes](https://www.iot-lab.info/hardware/a8/)

----

It is based on quick diff of ```openlab``` directories
(and cursory glance at schematics, and ref manuals):

```cd openlab/platform ; for i in $(cd iotlab-m3 ; ls) ; do diff -u -w iotlab-m3/$i iotlab-a8-m3/$(echo $i | sed s/m3/a8-m3/) ; done > M3-M3ofA8.diff```


Diffs going from "M3 Open Nodes" to M3 embedded in "A8 Open Nodes" include:
* No light sensor (ISL29020)
* No flash chip (N25xxx)
* No pressure sensor (LPS331AP)

Configuration changes:
* No Flash on SPI1 (no DMA1 ch2/ch3; no GPIO PA5, PA6, PA7)
* Radio on SPI2 instead of SPI1
* SPI related pins moved GPIO_B:  PB.13 as SCLK pin ,PB.14 as MISO pin, PB.15 as MOSI pin
* Gyroscope LSM303DLHC: GPIO PC9 instead of GPIO PC0 (thus uses ```NVIC_IRQ_LINE_EXTI9_5``` instead of ```NVIC_IRQ_LINE_EXTI0```)
* Accelerometer/Magnetometer LSM303DLHC (order of lines is also changed in ```accmag_setup``` if you read the diff): 
  - Mag Drdy (MAG1) on GPIO PA11 instead of PB2
  - Acc Int2 on GPIO PB2 instead of PB1
  - interrupts through the EXTI (External interrupt/event controller) are modified accordingly

----

Notes:
- comment typo: "// Set PB9 input for GYRO DRDY" in ```iotlab-a8-m3_periph.c```
  should be "PC9" instead  ?
- Is the following ```openlab```-specific ? or due to the STM chip ?
  * EXTI lines 1,2,3 and 4 have their own interrupt handlers:
    ```exti1_isr``` (in ```exti.c)``` etc.
  * EXTI lines 5 to 9 go to the same IRQ interrupt handler ```ext9_5_isr``` (```exti.c```) 
  which then demultiplexes then to proper line handlers. Same for EXTI
  lines 10 to 15 (```exti15_10_isr```).
- doc: [STM32F10.xx Reference Manual RM-008](http://www.st.com/web/en/resource/technical/document/reference_manual/CD00171190.pdf), EXTI documented in p205- (pin mapping p208).
