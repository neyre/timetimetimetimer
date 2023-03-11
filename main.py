import _thread
import esp32
import time
from machine import Pin, PWM, WDT
from rotary_irq_esp import RotaryIRQ
import tm1637
import math

##########################
# Constants
##########################

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
        self.notifier = False


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
        if self.t <= -1:
            pass

        # Timer Expired (Buzzing)
        elif self.t <= 0:

            # Spawn Notifier
            if self.notifier == False:
                _thread.start_new_thread(alarm, (self,))
                self.notifier = True
                print('spawn thread')

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

    # See if Knob has Changed, Update if So
    def update(self):
        
        k_new = self.enc.value()
        self.enc.reset()

        # Don't update if notifier is running
        if self.notifier:
            return

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
                self.s = knob_dwell - 1

        # Update timer and set into update mode
        if k_new != 0:
            t_new = self.m_total*60 + self.s
            if t_new < 0:
                t_new = 0
            self.exp = time.time() + t_new
            self.update_exp = time.time() + knob_dwell
            self.notifier = False

##########################
# Alarm to be run in another thread
##########################

def alarm(tt):

    # Turn on Buzzer
    buzzer.duty(buzzer_dutycycle)

    # Print Scrolling Message
    segments = tt.scr.encode_string('food is good')
    data = [0] * 8
    data[4:0] = list(segments)
    for i in range(len(segments) + 5):
        tt.scr.write(data[0+i:4+i])
        time.sleep_ms(200)

    # Turn off Buzzer
    buzzer.duty(0)
    tt.notifier = False;

##########################
# Initialize Hardware and Objects
##########################

# watchdog = WDT(timeout=1000)
esp32.wake_on_ext0(Pin(34), esp32.WAKEUP_ANY_HIGH)  # Waking from deep sleep on knob movement

t1 = TimeTimer(26, 25, 35, 34)
buzzer = PWM(Pin(32))
buzzer.freq(buzzer_frequency)
buzzer.duty(0)

##########################
# Main Loop
##########################

while True:
    t1.run()

    # watchdog.feed()
