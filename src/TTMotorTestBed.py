# Development Program to explore using Pico to control TT Gear Motors using TB6612FNG Dual H-Bridge module.
#
# Test.  Two TT Gear Motors (a.k.a. TT Gearbox Motor) are connected to the TB6612FNG module as motor A and
#        motor B.  A two 18650 battery pack supplies the power to the module's VM pin.  The logic side of
#        the module runs at 3.3V, the same as the Pico.
#
#        The direction motors turns is controlled by push buttons, one for each motor.  Pressing the button
#        causes the direction to change in the sequence [FORWARD --> STOPPED --> BACKWARD --> STOPPED --> repeat].
#        The motor speeds are controlled by potentioments, one for each motor.  The potentiometers, theortically,
#        should have a range of [0..65535].  In reality, the potentiometers do not go below a couple 100's.  This
#        is not a problem since the motors do not turn at that speed and so, it is effectively zero.
#
#        The test setup has a third push button which is connected to the Pico RUN pin so the USB cable does not
#        have to be removed and inserted every time the BOOTSEL button on the Pico is used.
#
# Some of the print statements used for debugging were left in the code and are commented out.

from machine import ADC
from machine import Pin
from machine import PWM

import utime

# The emergency exception buffer is for use is any Exceptions are thrown.  This provides pre-allocated space
# and allows interrupt handlers to throw exceptions.
import micropython
micropython.alloc_emergency_exception_buf(128)

from TTMotor      import TTMotor
from MotorControl import MotorControl
from ButtonInfo   import ButtonInfo

#print("Running TTMotorTest2 --")

## Defining GPIO Pins used 

gpioPWA   = 4
gpioPWB   = 8

gpioAN1   = 5
gpioAN2   = 6

gpioBN1   = 9
gpioBN2   = 10

gpioStandby = 15

gpioButtonA = 17
gpioButtonB = 16

gpioPotA = 27
gpioPotB = 26

gpioLED  = 25

## Initialize Pins

#print("Initializing Button Pins")

pinButtonA = Pin(gpioButtonA, mode=Pin.IN, pull=Pin.PULL_DOWN)
pinButtonB = Pin(gpioButtonB, mode=Pin.IN, pull=Pin.PULL_DOWN)

#print("Initializing Potentiometers")
pinPotA = Pin(gpioPotA, mode=Pin.IN, pull=Pin.PULL_DOWN)
pinPotB = Pin(gpioPotB, mode=Pin.IN, pull=Pin.PULL_DOWN)

potA = ADC(pinPotA)
potB = ADC(pinPotB)

#print("Turning on onboard LED")
# This step is optional.  It does make it easier to tell that the program is
# running when both motors are stopped, which is their initial state.
pinLED = Pin(gpioLED, mode=Pin.OUT)
pinLED.on()

# There is no general way to obtain the ID used to create a Pin object
# after it has been created.  The following is a HACK, that assumes that
# when a Pin object is converted to a string "Pin(xx, yy==zz, gg=pp)"
# that the first parameter after the "(" starts in offset [4] and 
# ends with a comma.
def getPinID( pin: Pin ):
    pinString = str(pin)
    pinData   = pinString[4:-1].split(",")
    return int(pinData[0])
    # End of getPinID()

# Determine which motor based on its GPIO Pin for the PWM signal based
# on the Button or Potentiometer Pin.
def whichPWM( pin: Pin ):
    pinID = getPinID(pin)
    if ( pinID == gpioPotA or pinID == gpioButtonA ):
        return gpioPWA
    elif ( pinID == gpioPotB or pinID == gpioButtonB ):
        return gpioPWB
    else:
        return -1
    # End of whichPWM()


## Initialize Motor Data

#print("Initializing Motor Objects")
motorA = TTMotor(gpioPWA, gpioAN1, gpioAN2)
motorB = TTMotor(gpioPWB, gpioBN1, gpioBN2)

motorControl = MotorControl(gpioStandby, motorA, motorB)

## Initializing Button Data

buttons = { gpioPWA: ButtonInfo( gpioPWA ), gpioPWB: ButtonInfo(gpioPWB)}

# Push Button Pin Debouncing
#
# Watches Button values until it stablizes on the same value
# for 50ms.  It does not matter whether that value is HIGH or LOW.
#
# Returns the final, stable, Pin value.
def buttonDebounce( pin: Pin ):
    curr_value = pin.value()
    period     = 50 # stable within 50 ms

    active = 0
    while ( active < period ):
        if ( pin.value() == curr_value ):
            # Pin value did not change, increment ms counter
            active += 1
        else:
            # Pin value did change.  Use the new pin value as the
            # current value.  Reset ms counter to start new period
            # of watching.
            active = 0
            curr_value = pin.value()
    utime.sleep_ms(1)
    return curr_value
    # End of buttonDebounce()
  
# Button Interrupt Handler for Rising Signal Detected
#
# After allowing the button to stablize [see buttonDebounce()], the
# value of the pin is checked.  If the pin is HIGH, the button changed
# flag is set to True.  If the stable button is LOW, the button changed
# flag is set to False.
def buttonPressedHandler(pin):
    global  buttons

    # Let the button stablize before reading its value.
    pinValue = buttonDebounce(pin)

    # Determine the Button/Pin current value and set the
    # change flag to True if the button/pin is HIGH.
    pinID    = whichPWM(pin)

    if ( pinID < 0 ):
        # Unknown Pin cased the interrupt.  Cannot process this interrupt - IGNORE IT
        return

    if ( pinValue > 0 ):
        # If Busy, we are already processing an interrupt for this pin on a single
        # button press.  Do not process another one until the button is released.
        if ( not buttons[pinID].isBusy() ):
            buttons[pinID].setChange(True)
            buttons[pinID].setBusy( flag=True )
        #valueStr = "HIGH"  # for debug print statement below
   
    # NOTE: The change flag is cleared in the main loop and the busy flag is
    #       cleared in another interrupt handler

    #print("Button Handler: Button: ", str(pin), ", Value: ", valueStr)
    return
    # End of buttonHandler()

# Button Interrupt Handler for Falling Signal Detected
def buttonReleasedHandler( pin ):
    global  buttons

    # Let the button stablize before determining if the button was actually released
    pinValue = buttonDebounce(pin)

    # Determine which pin triggered the interrupt
    pinID = whichPWM(pin)

    if ( pinID < 0 ):
        # Unknown Pin cased the interrupt.  Cannot process this interrupt - IGNORE IT
        return

    # Only deal with falling signal interrupts, these are the ones where the final
    # pin value is LOW (or zero)
    if ( pinValue < 1 ):
        # We do not care if multiple interrupts occur when the button is released
        # so we are skipping checking to see if the button is Busy.
        buttons[pinID].setBusy(flag=False)

    return
    # end of buttonReleasedHandler


# Determine if the first value is equal to the second value +/- delta
#
# It turns out that each time the potentiometers are read, their value might
# change even if the knob is not being turned.  This method compensates for
# that small variation in readings so that the motor speeds are not changed
# everytime the potentiometers are read.
def closeEnough(value1, value2, delta):
    if ( (value1 >= (value2 - delta)) and (value1 <= (value2 + delta)) ):
        return True
    else:
        return False

    
# Setting up Interrup Handlers
#print("Initializing Button Interrupt Handlers")
pinButtonA.irq(handler=buttonPressedHandler, trigger=Pin.IRQ_RISING)
pinButtonB.irq(handler=buttonPressedHandler, trigger=Pin.IRQ_RISING)

pinButtonA.irq(handler=buttonReleasedHandler, trigger=Pin.IRQ_FALLING)
pinButtonB.irq(handler=buttonReleasedHandler, trigger=Pin.IRQ_FALLING)

print("Starting Infinite Loop")

myDelta = 1000

while True:
    # The update flag will be set to True if either buttons have been pushed
    # and the toggling of direction will be done in the main code instead of
    # in the interrupt handler, thus minimizing what the interrupt handler has
    # to do.
    #
    # If this flag is True later in the loop, the Motors will be told to 
    # change speeds, will will automatically use the new current direction.
    updateFlag = False

    for buttonInfo in buttons.values():
        if ( buttonInfo.getChange() ):
            updateFlag = True
            #print("Button Pushed: Pin: ", buttonInfo.pinID())
            motorControl.toggleDirection(buttonInfo.pinID())
            buttonInfo.setChange(False) 

    frontSpeed = potA.read_u16()
    backSpeed  = potB.read_u16()

    if ( updateFlag or 
        ( not closeEnough(frontSpeed, motorA.speed(), myDelta ) ) or 
        ( not closeEnough(backSpeed, motorB.speed(), myDelta ) ) ):
        #print("Change Speed or Direction")
        motorControl.changeSpeed(frontSpeed=potA.read_u16(), backSpeed=potB.read_u16())

        # print("Motor A: PWM: ", motorA.pwm(), 
        #   " Direction:", motorA.direction(), 
        #   ", IN1: [", getPinID(motorA.signal1Pin()),
        #   ", Flag: ", motorA.signal1(), ", Value: ", motorA.signal1Pin().value(), "]",
        #   ", IN2: [", getPinID(motorA.signal2Pin()),
        #   ", Flag: ", motorA.signal2(), ", Value: ", motorA.signal2Pin().value(), "]",
        #   ", Speed: ", motorA.speed() )
        
        # print("Motor B: PWM: ", motorB.pwm(),
        #   " Direction:", motorB.direction(), 
        #   ", IN1: [", getPinID(motorB.signal1Pin()),
        #   ", Flag: ", motorB.signal1(), ", Value: ", motorB.signal1Pin().value(), "]",
        #   ", IN2: [", getPinID(motorB.signal2Pin()),
        #   ", Flag: ", motorB.signal2(), ", Value: ", motorB.signal2Pin().value(), "]",
        #   ", Speed: ", motorB.speed() )

  
    #print("Pot A: ", potA.read_u16(), "  Pot B: ", potB.read_u16())

    # Sleep for 1 second and repeat loop.  This time can be made smaller if the response
    # time between changes (buttons pushed or potentiometers turned) is too sluggish.
    utime.sleep(1)

