## Useful Links
- [Rotary Encoder Library](https://github.com/miketeachman/micropython-rotary)
- [LED Driver Library](https://github.com/mcauser/micropython-tm1637)
- [Instructions for loading files with ampy](https://learn.adafruit.com/micropython-basics-load-files-and-run-code/file-operations)
- [Getting started guide with esp32 and micropython](https://docs.micropython.org/en/latest/esp32/tutorial/intro.html#esp32-intro)
- [Firmware downloads](https://micropython.org/download/esp32/)
- [The MCU I bought](https://www.amazon.com/dp/B09XDMVS9N)
- [The 7-seg display I bought](https://www.amazon.com/dp/B07MCGDST2)
- [Encoder I bought](https://www.amazon.com/dp/B07F26CT6B)
- [Buzzer I bought](https://www.amazon.com/dp/B07MPYWVGD)

## Misc. Notes
- can't put everything on one side, not enough pins on 3.3V side without using the UART pins
- enabling the watchdog creates problems when trying to push new firmware the watchdog resets it. 
- Yellow, red, white are probably the best colors. Blue is hard to read with the white outlines.
- trying to put all the screen control logic in the second thread leads to noticable delay

## Known Bugs
Pin 12 (knob #2) is linked to a pin that affects boot. Should move this to another pin as if this pin is high at boot, it doesn't boot right. Avoid pins 0/2/12/15

## Opportunities for performance improvement
- Right now, we're writing to the LEDs a lot. Writing only when the value is different would probably speed things up.

## Commands

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