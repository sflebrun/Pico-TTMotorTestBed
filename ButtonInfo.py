# Class for storing information for the interrupt handling

# This class contains information about the push buttons where
# one object represents a single push button.  Initially, this
# class contains more data fields and the objects are stored
# in a dictionary or keyed list.
#
# During development, it was determined that only the Change/Check Flag
# was really necessary.  The keyed listed could have stored a single
# bool value and use the GPIO Pin Number as the key.  This was not done
# because the code for the dictionary was already written and working and 
# it is possible in the future, more button state information might be needed
#
class ButtonInfo:

    pinLow  = 0
    pinHigh = 1

    def __init__(self, pinID):
        self.id = pinID
        self.check     = False

    def pinID(self):
        return self.id

    def getChange(self):
        return self.check

    def setChange(self, newValue: bool):
        self.check = newValue

    
