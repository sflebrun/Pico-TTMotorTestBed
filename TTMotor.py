# Defines the class that represents one motor part of TB6612FNG Dual H-Bridge.
#
# Note: This class is actually independent of what type of DC Motor is attached to 
#       the Dual H-Bridge Module.  My test setup is for a pair of TT Gear Motors,
#       hence the name.
#
# Three pins control each motor -- PMW, IN1, and IN2.  
#
# Motors are labeled A and B on the H-Bridge module.  This class only deals with
# a single motor so the A and B labels are ignored.  See the MotorControl class 
# for dealing with both motors and the Standby Pin.

from machine import Pin, PWM

# This class represents the part of the Dual H-Bridge module.
class TTMotor:
    """A Class that contains the state of a DC Motor, primarily for TT Gearbox Motors"""

    # Constants that denote motor direction.
    # Should be constants but Python const() does not appear to work in MicroPython
    # Please do no change these variables.
    STOPPED   = 0
    FORWARD   = 1
    BACKWARD  = 2

    # Default Constructor
    #    Current Direction is none or STOPPED
    #    Next Direction is FORWARD (by setting previous Direction to BACKWARD)
    #
    # @param  gpioPWM   The GPIO Pin Number, not the physical pin number, of the
    #                   pin used to set the motor speed with a pulse width modulation
    # @param  gpioIN1   The GPIO Pin Number used to determine direction of motor in
    #                   conjunction with gpioIN2
    # @param  gpioIN2   The GPIO Pin Number used to determine direction of motor in
    #                    conjunction with gpioIN1
    #
    def __init__(self, gpioPWM: int, gpioIN1: int, gpioIN2: int ):
        self.gpioPWM = gpioPWM
        self.gpioIN1 = gpioIN1
        self.gpioIN2 = gpioIN2
        self.motorSpeed  = 0
        self.IN1Value = False
        self.IN2Value = False

        if ( gpioPWM < 0 ):
            # Invalid value
            raise ValueError("TTMotor Constructor: Invalid GPIO PWM Pin number: " + str(gpioPWM))
        else:
            #Initialize the PWM pin
            self.pinPWM = Pin(gpioPWM, mode=Pin.OUT)

            self.pwmPin = PWM(self.pinPWM)
            self.pwmPin.freq(10000)  # 10kHz
            self.pwmPin.duty_u16(0)  # off

            # Initialize the two signal input pins
            self.in1    = Pin(gpioIN1, mode=Pin.OUT)
            self.in2    = Pin(gpioIN2, mode=Pin.OUT)

            self.in1.low()
            self.in2.low()

        self.currentDirection  = self.STOPPED
        self.previousDirection = self.BACKWARD

 
    # Determine if Pin ID is one of the GPIO Pins associated with this motor
    def usesPin( self, pinID: int ):
        if ( pinID == self.gpioPWM or pinID == self.gpioIN1 or pinID == self.gpioIN2 ):
            return True
        else:
            return False
        


    # Return the configured GPIO Pin object
    def pwm(self):
        return self.gpioPWM

    # Returns the GPIO Pin object for IN1
    def signal1Pin(self):
        return self.in1

    # Returns the GPIO Pin object for IN2
    def signal2Pin(self):
        return self.in2

    # Returns what the IN1 Pin should be set to: True == HIGH, False == LOW
    def signal1(self):
        return self.IN1Value

    # Returns what the IN2 Pin should be set to: True == HIGH, False == LOW
    def signal2(self):
        return self.IN2Value

    # Returns the Current Direction
    def direction(self):
        return self.currentDirection

    # Returns what the current speed is set to
    def speed(self):
        return self.motorSpeed
     
    # Returns the Next Direction
    #
    # The the toggle sequence is FORWARD --> STOPPED --> BACKWARD --> STOPPED --> repeat
    # So the next direction refers to the next N0N-Stopped direction.
    def nextDirection(self):
        if ( self.previousDirection == self.BACKWARD ):
            return self.FORWARD
        else:
            # all other values for Previous Direction leads to 
            return self.BACKWARD

    # Change direction based on the last none-stopped direction
    # Toggle Cycle:  FORWARD --> STOPPED --> BACKWARD --> STOPPED --> repeat
    def toggleDirection(self):
        if ( self.currentDirection == self.STOPPED ):
            # If currect direction is STOPPED, use the previous (non-STOPPED) direction
            # to determine the new current direction.
            if ( self.previousDirection == self.BACKWARD ):
                self.currentDirection = self.FORWARD
            else:
                self.currentDirection = self.BACKWARD
        else:
            # If current direction is FORWARD or BACKWARD, new current direction is STOPPED
            # and new previous direction is set to the old current direction
            self.previousDirection = self.currentDirection
            self.currentDirection  = self.STOPPED

    # Set actual Motor Speed and Direction
    #
    # This function actually writes to the Dual H-Bridge module, hence causing the motors to 
    # turn or to stop.
    def  motorControl( self, speed ):
        signal1 = False
        signal2 = False

        # Set Motor Speed to the passed value which may not match the zero speed of STOPPED
        # but it does match the Potentiometer that determines the moving speeds.
        self.motorSpeed = speed

        #print("Current Direction = ", self.currentDirection)
        if ( self.currentDirection == self.FORWARD ):
            signal2 = True
        elif ( self.currentDirection == self.BACKWARD ):
            signal1 = True
        else:
            speed = 0

        # Set Direction: STOPPED, FORWARD, or BACKWARD
        self.IN1Value = signal1
        if ( signal1 ):
            self.in1.on()
        else:
            self.in1.off()

        self.IN2Value = signal2
        if ( signal2 ):
            self.in2.on()
        else:
            self.in2.off()

        ## Set Speed
        self.pwmPin.duty_u16(speed)

        # End of MotorControl()


        
        