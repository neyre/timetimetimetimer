import _thread
import esp32
import time
from machine import Pin, PWM, WDT, freq
from rotary_irq_esp import RotaryIRQ
import tm1637
import math

##########################
# Constants
##########################

buzzer_duration = 6
short_duration = 5.5 # Show seconds below this # of mins, must be < 60
screen_brightness = 2 # Range of 1-7, 2 for white, 4 for other colors
knob_dwell = 3 # Stay in update mode for this long after an update

##########################
# Timer Controller Class
##########################

class TimeTimer(object):
    def __init__(self, screen_clk, screen_dio, enc_clk, enc_dio, brt, beep_pattern):

        # Setup Encoder
        self.enc = RotaryIRQ(pin_num_clk=enc_clk, pin_num_dt=enc_dio, min_val=0, half_step=True, reverse=False)
        
        # Setup Screen
        self.scr = tm1637.TM1637(clk=Pin(screen_clk), dio=Pin(screen_dio))
        self.scr.show('    ')
        self.scr.brightness(brt)

        # Expiration Time
        self.exp = 0    # End of Timer
        self.update_exp = 0   # End of Update Mode
        self.alarm_start = 0   # Alarm Start Time

        #  0 = Off
        # -1 = Screen Alarming
        #  1 = Running Counter
        self.status = 0

        self.beep_pattern = beep_pattern


    # Update and Display, Run Once per Loop
    def run(self):
        self.compute_time()

        # Time's Up - Transition to Alarming State
        if self.status == 1 and self.t <= 0:
            self.status = -1
            self.alarm_start = time.time()
            buz.on(self.beep_pattern)

        # State - Timer Running
        elif self.status == 1:
            self.display_time()

        # State - Timer Off
        elif self.status == 0:
            self.scr.show('    ')

        # State - Screen Alarming
        elif self.status == -1:
            self.display_alarm()

        self.handle_knob()

    # Compute time remaining
    def compute_time(self):
        # Compute Time Remaining
        self.t = self.exp - time.time()

        # Compute Hours, Minutes, Seconds
        self.h = math.floor(self.t/60/60)
        self.m = math.floor(self.t/60)%60 # Minutes Left
        self.m_disp = round(self.t/60)%60 # Rounded to Nearest Min, for seconds-free display
        self.m_total = math.floor(self.t/60) # Total Mins (e.g. 61 instead of 1:01)
        self.s = math.ceil(self.t%60)

        # Deal with special case of t=60 min
        if self.m_disp == 0 and self.h == 0 and self.t > 3000:
            self.h = 1

    # Format time and show it on the display
    def display_time(self):

        # Mode 1 - Short Duration, Show Seconds
        # Skip if in Update Window
        if self.update_exp-time.time() <= 0 and self.t < short_duration*60:
            self.scr.numbers(self.m_total, self.s)
        
        # Mode 2 - Medium Duration, Show Just Minutes
        elif self.h == 0:
            self.scr.number(self.m_disp)

        # Mode 3 - Long Duation, Show Hours and Minutes 
        else: 
            self.scr.numbers(self.h, self.m_disp)

    # Display Alarm Text (Food is Good)
    def display_alarm(self):
        elapsed = time.time() - self.alarm_start

        # Show Each Word for 2 Seconds
        if elapsed < 2:
            self.scr.write([113, 0b01011100, 0b01011100, 94])
        elif elapsed < 4:
            self.scr.show(' is ')
        elif elapsed < 6:
            self.scr.write([61, 0b01011100, 0b01011100, 94])
        else:
            self.status = 0

    # See if Knob has Changed, Update if So
    def handle_knob(self):
        
        # See which direction knob has moved
        k_new = self.enc.value()
        self.enc.reset()

        # Knob Turned Clockwise
        if k_new > 0:
            # Add minutes to timer
            if self.t <= 0:
                self.m_total = 0
            self.m_total += 1
            self.s = knob_dwell - 1

            # Turn off buzzer if alarming
            if self.status <1:
                self.status = 1
                buz.off()

        # Knob Turned Counterclockwise
        if k_new < 0:
            # Turn off if alarming
            if self.status < 1:
                self.status = 0
                buz.off()
                return

            # Pull minutes off timer
            if self.s <= knob_dwell:
                self.m_total -= 1
            self.s = knob_dwell - 1

        # Update timer and set into update mode
        if k_new != 0:
            t_new = self.m_total*60 + self.s
            if t_new <= 0:
                t_new = 0

            self.exp = time.time() + t_new
            self.update_exp = time.time() + knob_dwell


class BuzzerMinder(object):
    def __init__(self, pin_num):
        self.buzzer = Pin(pin_num, Pin.OUT)
        self.buzzer_end = 0
        self.pattern = 1

        # 0 = Buzzer Off
        # 1 = Buzzer On
        self.status = 0

    def run(self):

        # If Buzzer Expired, Transition to Off State
        if self.buzzer_end - time.time() <= 0:
            self.off()
            return

        # If Buzzer On
        if self.status == 1:

            # Beeping Pattern 1 - 70ms every 500ms
            if self.pattern == 1:
                period = time.ticks_ms() % 500
                if period <= 70:
                    self.buzzer.on();
                    return

            # Beeping Pattern 2 - 2x 50ms every 1000ms
            elif self.pattern == 2:
                period = time.ticks_ms() % 1000
                if ((period <= 50) or 
                    (period > 200 and period <= 250)):
                    self.buzzer.on();
                    return

            # Beeping Pattern 3 - 3x 50ms every 1000ms
            else:
                period = time.ticks_ms() % 1000
                if ((period <= 50) or 
                    (period > 150 and period <= 200) or
                    (period > 300 and period <= 350)):
                    self.buzzer.on();
                    return

        self.buzzer.off();

    def off(self):
        self.status = 0
        self.buzzer_end = 0
        self.buzzer.off();

    def on(self, beep_pattern):
        self.buzzer_end = time.time() + buzzer_duration
        self.status = 1
        self.pattern = beep_pattern


##########################
# Initialize Hardware and Objects
##########################

freq(80000000) # Underclock to 80MHz to save power, keep things cooler, why not
# watchdog = WDT(timeout=1000) # Skip it, causes trouble when loading new firmware
# esp32.wake_on_ext0(Pin(34), esp32.WAKEUP_ANY_HIGH)  # Waking from deep sleep on knob movement

t1 = TimeTimer(25, 33, 35, 34, screen_brightness, 1)
t2 = TimeTimer(26, 27, 14, 12, screen_brightness, 2)
t3 = TimeTimer(21, 19, 18, 5, screen_brightness, 3)
buz = BuzzerMinder(32)

# Display Power-On Message
t1.scr.show(' 1  ')
t2.scr.show('  2 ')
t3.scr.show('   3')
time.sleep(1)
t1.scr.write([61, 0b01011100, 0b01011100, 94])
t2.scr.write([61, 0b01011100, 0b01011100, 94])
t3.scr.write([61, 0b01011100, 0b01011100, 94])
time.sleep(1)

##########################
# Main Loop
##########################

while True:
    t1.run()
    t2.run()
    t3.run()
    buz.run()
