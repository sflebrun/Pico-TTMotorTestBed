# Class for storing information for the interrupt handling

# This class contains information about the push buttons where
# one object represents a single push button.  Initially, this
# class contains more data fields and the objects are stored
# in a dictionary or keyed list.
#
#
class ButtonInfo:

    pinLow  = 0
    pinHigh = 1

    def __init__(self, pinID):
        self.id = pinID
        self.check     = False
        self.busy      = False

    def pinID(self):
        return self.id

    def isBusy(self):
        return self.busy
    
    def setBusy(self, flag=True):
        self.busy = flag

    def getChange(self):
        return self.check

    def setChange(self, newValue: bool):
        self.check = newValue

    
