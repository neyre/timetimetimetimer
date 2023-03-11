import time
from machine import Pin, PWM
from rotary_irq_esp import RotaryIRQ
import tm1637
import math

##########################
# Constants
##########################

buzzer_enabled = True
buzzer_duration = 5
buzzer_dutycycle = 200
buzzer_frequency = 2

short_duration = 7.5 # Show seconds below this # of mins, must be < 60
screen_brightness = 4 # Range of 1-7
knob_dwell = 3 # Stay in update mode for this long after an update

##########################
# Timer Controller Class
##########################

class TimeTimer(object):

    def __init__(self, screen_clk, screen_dio, enc_clk, enc_dio):

        # Setup Encoder
        self.enc = RotaryIRQ(pin_num_clk=enc_clk, pin_num_dt=enc_dio, min_val=0, half_step=True, reverse=False)
        
        # Setup Screen
        self.scr = tm1637.TM1637(clk=Pin(screen_clk), dio=Pin(screen_dio))
        self.scr.show('    ')
        self.scr.brightness(screen_brightness)

        # Expiration Time
        self.exp = 0    # End of Timer
        self.update_exp = 0   # End of Update Mode

        # Knob Old Position
        self.knob = 0

        # Buzzing Status
        self.buzz = 0


    # Update and Display, Run Once per Loop
    def run(self):
        
        # Compute Time Remaining
        self.t = self.exp - time.time()

        # Compute Hours, Minutes, Seconds
        self.h = math.floor(self.t/60/60)
        self.m = math.floor(self.t/60)%60 # Minutes Left
        self.m_disp = round(self.t/60)%60 # Rounded to Nearest Min, for seconds-free display
        self.m_total = math.floor(self.t/60) # Total Mins (e.g. 61 instead of 1:01)
        self.s = math.ceil(self.t%60)

        self.update()
        self.display()

    # Format time and show it on the display
    # Returns 1 if it should be buzzing, 0 if not.
    def display(self):
        
        # Timer Off State
        if self.t <= -1 * buzzer_duration:
            self.scr.show('    ')

        # Timer Expired (Buzzing)
        elif self.t <= 0:
            self.scr.number(0)
            self.buzz = 1
            return

        # Short Duration, Show Seconds
        # Skip if in Update Window
        elif self.update_exp-time.time() <= 0 and self.t < short_duration*60:
            self.scr.numbers(self.m_total, self.s, colon=True)
        
        # Medium Duration, Show Just Minutes
        elif self.t < 60*60:
            self.scr.number(self.m_disp)

        # Long Duation, Show Hours and Minutes 
        else: 
            self.scr.numbers(self.h, self.m_disp, colon=True)
        
        # Turn off Buzz
        self.buzz = 0

    # See if Knob has Changed, Update if So
    def update(self):
        
        k_new = self.enc.value()
        self.enc.reset()

        # Increase Timer
        if k_new > 0:
            if self.t <= 0:
                self.s = 0
                self.m_total = 1
            else:
                self.s = knob_dwell - 1
                self.m_total += 1

        # Decrease Timer
        if k_new < 0:
            if self.t <= 0:
                pass
            elif self.s <= knob_dwell:
                self.s = knob_dwell - 1
                self.m_total -= 1
            else:
                self.s = knob_dwell

        # Update timer and set into update mode
        if k_new != 0:
            t_new = self.m_total*60 + self.s
            self.exp = time.time() + t_new
            self.update_exp = time.time() + knob_dwell

##########################
# Initialize Hardware and Objects
##########################

t1 = TimeTimer(26, 25, 35, 34)
buzzer = PWM(Pin(32))
buzzer.freq(buzzer_frequency)
buzzer.duty(0)

##########################
# Main Loop
##########################

while True:
    t1.run()

    if buzzer_enabled:
        buzz = t1.buzz + t1.buzz + t1.buzz
        if buzz > 0:
            buzzer.duty(buzzer_dutycycle)
        else:
            buzzer.duty(0)