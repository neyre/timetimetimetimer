A time timer with three time time timers.

# BOM & Hardware Notes
- [ESP32 MCU (1)](https://www.amazon.com/dp/B09XDMVS9N)
- [7-seg displays (3, sold in pack of 5)](https://www.amazon.com/dp/B07MCGDST2)
- [Encoder I bought (3, sold in pack of 5)](https://www.amazon.com/dp/B07F26CT6B)
- [Buzzer I bought (1, sold in pack of 5)](https://www.amazon.com/dp/B07MPYWVGD)

It's easiest to de-solder the headers from all of the boards (easy with a bit of solder wick) and solder wires to them. Some tape and zipties helps keep the many wires organized.

Wire the buzzer with its gnd & IO pins to ground, and the VCC pin to the digital output of the MCU. It buzzes when IO is pulled low, so this prevents it from buzzing until the MCU commands it.

The encoders are wired to 3.3V. The 7-seg displays are wired to 5V (an attempt to reduce the load on the voltage regulator on the ESP32 board). Everything is a common ground.

Yellow, red, white are probably the best display colors. Blue is hard to read up close with the white outlines.

This is powered off USB (from an old iPhone power brick), it'd need some optimization to be battery powered.

![pinout](https://raw.githubusercontent.com/neyre/timetimetimetimer/master/esp32_pinout.png)

# Useful Links
- [Rotary Encoder Library](https://github.com/miketeachman/micropython-rotary)
- [LED Driver Library](https://github.com/mcauser/micropython-tm1637)
- [Instructions for loading files with ampy](https://learn.adafruit.com/micropython-basics-load-files-and-run-code/file-operations)
- [Getting started guide with esp32 and micropython](https://docs.micropython.org/en/latest/esp32/tutorial/intro.html#esp32-intro)
- [Firmware downloads](https://micropython.org/download/esp32/) - this is using version esp32-20220618-v1.19.1.bin

# Misc. Notes

### Known Bugs
Pin 12 (knob #2) is linked to a pin that affects boot. Should move this to another pin as if this pin is high at boot, it doesn't boot right. Avoid pins 0/2/12/15

### Opportunities for performance improvement
- Right now, it's writing to the LEDs very frequently. Writing only when the value is different would probably speed things up.

### Misc. FW Notes
- enabling the watchdog creates problems when trying to push new firmware the watchdog resets it. 
- trying to put all the screen control logic in a second thread leads to noticable delay. just kept it all to one thread

# Command Reference

I don't use these commands often, so I'm including them here just so they're handy next time I need them. All are performed when connected to the ESP32 with USB.

##### To erase and install firmware

`esptool.py --port COM5 erase_flash`

`esptool.py --chip esp32 --port COM5 write_flash -z 0x1000 esp32-20220618-v1.19.1.bin`

##### To Run Code

`ampy -pCOM5 run main.py`

##### To Push Code

If code in a `main.py` file already running, stop it by connecting via serial and press Ctrl-A to stop code. Then run `ampy -pCOM5 rm main.py`

`ampy -pCOM5 put main.py`

Repeat for library files as required.

#### If Ampy Not Responding

First, make sure that the esp32 is booted correctly by opening the serial port with putty and making sure it's booted. See known issue about knob 2.

Then, see if the `main.py` needs to be stopped.