import time
from machine import Pin
from rotary_irq_esp import RotaryIRQ
import tm1637

buzzer = Pin(32, Pin.OUT)
buzzer.off()

encoder = RotaryIRQ(pin_num_clk=35, pin_num_dt=34, min_val=0, half_step=True, reverse=False)

screen = tm1637.TM1637(clk=Pin(26), dio=Pin(25))
screen.temperature(24);




while True:

    time.sleep(0.001)  # Delay for 1 second.
    screen.number(encoder.value())

    if encoder.value() < 0:
        buzzer.on()
    else:
        buzzer.off()