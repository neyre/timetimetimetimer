import time
from machine import Pin, PWM
from rotary_irq_esp import RotaryIRQ
import tm1637
import math

# Constants
buzzer_duration = 5
buzzer_dutycycle = 200
buzzer_frequency = 2
short_duration = 7.5 # Show Seconds Below this

# Configure Buzzer
buzzer = PWM(Pin(32))
buzzer.freq(buzzer_frequency)
buzzer.duty(0)

# Configure Encoder
enc1 = RotaryIRQ(pin_num_clk=35, pin_num_dt=34, min_val=0, half_step=True, reverse=False)

# Configure Screen
screen = tm1637.TM1637(clk=Pin(26), dio=Pin(25))
screen.show('    ')
screen.brightness(4)

# Variables for Expiration Times
t1_exp = time.time() + 200
buz_exp = 0

# Knob Position Storage Variables
k1 = enc1.value()





def disp_timer(scr, exp):
    t1 = exp - time.time()
    if t1 <= -1 * buzzer_duration: # Disabled
        scr.show('    ')
    elif t1 <= 0: # Expired
        scr.number(0)
        return 1
    elif t1 < short_duration*60: # Short Duration, Show Seconds
        scr.numbers(math.floor(t1/60), math.ceil(t1%60), colon=True)
    elif t1 < 60*60: # Medium Duration
        scr.number(round(t1/60))
    else: # Long Duation (hrs)
        scr.numbers(math.floor(t1/60/60), math.floor(t1/60)%60, colon=True)
    return 0




while True:

    # Update Timer
    k1_new = enc1.value()
    if k1_new != k1:

        # If below zero, set to zero
        if t1_exp - time.time() <= 0:
            t1_exp = time.time()
        
        # Update with change in encoder value
        t1_exp += 60 * (k1_new - k1)
        k1 = k1_new

        # Don't let go below zero
        if t1_exp - time.time() <= 0: 
            t1_exp = time.time()
        
    # Display Timer
    buz1 = disp_timer(screen, t1_exp)

    if buz1 > 0:
        buzzer.duty(buzzer_dutycycle)
    else:
        buzzer.duty(0)