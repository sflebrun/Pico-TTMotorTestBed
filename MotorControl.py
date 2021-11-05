# Class to handle two motors on a single TB6612FNG Dual H-Bridge module
# plus the extra control pins on the module, namely the STANDBY Pin.
#



from machine import Pin

import TTMotor

# The TB6612FNG Dual H-Bridge control class.
#
# The addition of the Standby Pin makes this class specific to the
# TB6612FNG module.  Removing all references to the Standby Pin would
# make this a generic Dual H-Bridge Controller class
#
class MotorControl:
    """Class to manage two TTMotor objects connected to the same
    TB6612FN Dual MOSFET H-Bridge module."""

    # Primary Constructor for this Class
    #
    # Note: It is the responsibility of the caller to have already created
    #       TTMotor objects for each of the two motors.  Only one motor is
    #       actually required if two motors are not connected to the H-Bridge.
    #
    # @param standby  The GPIO Pin Number, not the physical pin number, of the
    #                 pin used to control the StandBy pin on the TB6612FNG module.
    #
    # @param frontMotor  The TTMotor object for the motor that is considered to be
    #                    at the front of the car.
    #
    # @param backMotor   The TTMotor object for the motor that is considered to be
    #                    at the back of the car.
    #
    # @param flag        A boolean flag that denotes if True that the motors turn CW 
    #                    (Clockwise) when moving forward and if False that the motors
    #                    turn CCW (Counter Clockwise) when moving forward. 
    #                    NOT IMPLEMENTED YET -- Might be implemented when using four
    #                    motors and two TB6612FNG Dual H-Bridge modules.
    def __init__( self, standby: int, frontMotor=None, backMotor=None):
        self.gpioSTANDBY = standby
        self.pinSTANDBY  = Pin( self.gpioSTANDBY, mode=Pin.OUT )
        self.motors      = {}

        # Offsets for the Front and Back Motors in the motors array
        self.FRONT = 1
        self.BACK  = 2

        if ( frontMotor != None ):
            self.motors[self.FRONT] = frontMotor

        if ( backMotor != None ):
            self.motors[self.BACK]  = backMotor

        self.pinSTANDBY.high()

    # There is no general way to obtain the ID used to create a Pin object
    # after it has been created.  The following is a HACK, that assumes that
    # when a Pin object is converted to a string "Pin(xx, yy==zz, gg=pp)"
    # that the first parameter after the "(" starts in offset [4] and 
    # ends with a comma.
    def getPinID( self, pin ):
        pinString = str(pin)
        pinData   = pinString[4:-1].split(",")
        return int(pinData[0])


    # Modify speed being written to the each of the wheels
    # Either use speed or {frontSpeed and backSpeed}
    # If either frontSpeed or backSpeed are set to 0 or greater, those speeds
    # are used for each motor.  If they are not set, speed is used.  If none
    # of them are set, the speed used is 0.
    #
    # NOTE: This will result in data being written to the H-Bridge module and
    #       the motors to physically change speed.
    #
    def changeSpeed( self, speed=-1, frontSpeed=-1, backSpeed=-1):
        # Determining actual speeds based on which speed parameters are set or
        # in are their default values.
        if ( speed < 0 ):
            speed = 0

        if ( frontSpeed < 0 ):
            frontSpeed = speed

        if ( backSpeed < 0 ):
            backSpeed = speed

        # Make sure speeds are not greater than maximum value: 0xFFFF == 65535
        frontSpeed = frontSpeed & 0xFFFF
        backSpeed  = backSpeed  & 0xFFFF

        # change Motor Speeds
        #
        # NOTE: If TTMotor object was None, the if statements will evaluate to False
        if ( self.FRONT in self.motors.keys() ):
            self.motors[self.FRONT].motorControl(frontSpeed)

        if ( self.BACK  in self.motors.keys() ):
            self.motors[self.BACK].motorControl(backSpeed)


    # Toggle the direction the motor should turn based on Pin Number
    def toggleDirection(self, gpioPWM: int ):
        print("Toggle Direction on PWM Motor: ", gpioPWM)

        # Loop through motors array and toggle the direction on the appropriate motor
        for motor in self.motors.values():
            if ( motor.usesPin( gpioPWM ) ):
                motor.toggleDirection()
                print("Toggle Direction: Motor ID: ", gpioPWM, ", Direction = ", motor.direction())
        

    #
    # End of MotorControl class
    #
