# Pico-TTMotorTestBed
Environment and Code for testing two DC TT Gear Motors using a TB6612FNG Dual H-Bridge module and a Pico

## Build Environment
The code for ths project was developed using Visual Studio Code.  I see no reason why Thonny cannot be used with the code.

### Visual Studio Code modifications

* Add to the settings.json file the following line:<br/>
  "python.analysis.extraPaths:" ["./."]
  * This allows the editor to import from local files.
* Recommended (**Required**) Extensions:
  * MagicPython
  * **Pico-Go**
  * Pylance
  * Python

### Pico
The MicroPython UF2 file needs to be uploaded to the Pico.  This is the real program running on the Pico and it interrupts the
python code.  The three class files, ButtonInfo.py, MotorControl.py, and TTMotor.py must be uploaded to the Pico before the main
code, TTMotorTestBed.py, can run.

On multiple occasions, when trying to run the TTMotorTestBed python code, an error would occur that it could not find TTMotor.
Running the program again resolved this problem.  I do not know if this is a Pico issue or a Visual Studio Code/Pico-Go issue.

## Parts List
The links are places where I have bought the parts.  They are intended as recommendations and so you can 
identify the parts.

* [Raspberry Pi Pico](https://www.seeedstudio.com/Raspberry-Pi-Pico-p-4832.html)
* [TB6612FNG Dual H-Bridge](https://www.amazon.com/dp/B08J3S6G2N?psc=1&ref=ppx_yo2_dt_b_product_details&pldnSite=1)
* [2 TT Gear Motors with Wheels](https://smile.amazon.com/dp/B098Q1BCX5?psc=1&ref=ppx_yo2_dt_b_product_details)
* [Breadboard -- 830 points](https://smile.amazon.com/DEYUE-Solderless-Prototype-Breadboard-Points/dp/B07NVWR495/ref=sr_1_8?crid=1AAPZPBJRNTO9&keywords=breadboard&qid=1636086519&s=electronics&sprefix=breadbo%2Celectronics%2C296&sr=1-8)
* [Dupont connector, male to male, various lengths](https://smile.amazon.com/Elegoo-EL-CP-004-Multicolored-Breadboard-arduino/dp/B01EV70C78/ref=sr_1_3?crid=1KPAZ3AVHP07W&keywords=dupont+connectors&qid=1636086746&s=electronics&sprefix=dupont+connectors%2Celectronics%2C80&sr=1-3)
* [2 Breadboard Potentiometers](https://smile.amazon.com/dp/B09G9TBY38?psc=1&ref=ppx_yo2_dt_b_product_details)
* [3 Breadboard Push Buttons](https://smile.amazon.com/dp/B07XF3YMJ4?psc=1&ref=ppx_yo2_dt_b_product_details)
* 3D Printed Motor Stand [optional] See File: **Dual TT Gear Motor Test Bed.stl**
* 4 M3x30mm screws and nuts, if 3D Printed Motor Stand is used.

**Note** These are the parts that I used.  You can substitute most of the parts with something equivalent.  If you substitute a different
microcontroller board for the Pico or another Dual H-Bridge module for the TB6612FNG, changes to the code will be necessary.  For the Dual
H-Bridge Module see the comment about the Standby Pin in the MotorControl.py file.

## 3D Printed Parts
There is only one part that needs to be 3D printed.  That is the **Dual TT Motor Test Bed.stl**.  This can be printed with PLA filament with layers
set to 0.2mm and 20% infill.  No supports are necessary.  My printer is an Ender 3 Pro and the test bed had to be rotated 45 degrees so that the
test bed would fit in the 220mm x 220mm build area.

The TT Gear Motors mount on the pair of walls and requires M3 screws with nuts.  I recommend 30mm length screws. The screws pass through two walls
that are 25mm apart measured by the outside of each wall.  A 26mm length screw might work though it may not have enough thread sticking out to hold
the nut securely.

The Cad file for the TT Gear Motor Mount is included as **TestBedForTwoMotorsV3.FCStd**.  This file is a FreeCad file.

## The Code

### The Main Python Program

The main file, that contains the infinite loop, is **TTMotorTestBed.py**.  I ran this program thought the Pico directly from Visual Studio Code.
Clicking the ***Run*** button on the lower status line causes VS Code to upload the file and run it.  The extension ***Pico-Go*** provides the Run and upload 
buttons on the GUI.  This method of running the code means that I manually started and stopped running the Python code.

If the file **TTMotorTestBed.py** is renamed to **main.py** and uploaded to the Pico, the MicroPython interrupter program will automatically read and
run it everytime the Pico is powered up.

### Interrupt Handling

There are two push buttons used to toggle the directions of the motors.  One button per motor.  The code uses interrupts to handle the button being pushed.
Multiple issues had to be handled during the development of the code.  The first was button bounce and the other was that the Pico does not handle 
interrupts immediate and schedules them to be processed.

#### Debouncing

When a push button is pressed and released, it seldoms makes and breaks the connection cleanly.  Instead, the signal received from the pin may have a 
series of rises and falls in a small window of time as the connection is made and broken.  This is  called bounce.

There are two ways to handle debouncing: hardware solutions and software solutions.  The hardware solution is the better of the two solutions and 
should be used in production level electronics.  The con of this method is that it adds more components to the breadboard in a capacitor and a couple 
of resisters per button.  The software solution usually involves examining the button over a small window of time until it stablizes.  The con of
this solution is that if you make your window too small, you get false readings.

Because this is a one-off project and built on a single breadboard, I choose to use a software solution.  An additional factor needed to be considered
with my software solution [See the function ***buttonDebounce()*** in **TTMotorTestBed.py**].  The problem is that bounce can occur on both the push 
and release of a button.  The interrupt is only intended to trigger a direction toggle on the push or rising edge of the signal.  To over come the
fact that the falling edge can bounce and therefore look like another rising edge, the debounce function ignores the state of the button pin.
Instead, it looks for the state to remain the same over a specified period of time.  Once the button has stablized, the final state of the button
is used.  If the pin value is High, the interrupt function handles the interrupt.  If the final state is low, the interrupt ignores the interrupt.

#### Delayed Interrupt Handling

Normally when writing an interrupt handler, two things are considered.  The fist is to keep the interrupt handler as short, timewise, as possible.
The second is to disable additional interrupts for the same event from occurring while the first interrupt is being handled.  On the Pico, it is
not possible to prevent multiple interrupts from occurring with the same event.  In the case of the push button with bounce, each time the signal
rises another interrupt is generated.  In other words, multiple interrupts can be generated due to button bounce in the time between the first
interrupt occurs and when it is handled.  Disabling new interrupts during the processing of the interrupt handle fails to work in this case because
the extra interrupts have already occurred.

The debounce function handles most of the cases of multiple interrupts.  The one exception is if the button is held down for a long enough period
of time and multiple interrupts are queued for processing.  In this case, the interrupt handler processes the first interrupt and the pin value is HIGH.  When 
the second interrupt is handled, the interrupt handler finds that the button value is still HIGH and treats it as a new interrupt.  This case is 
resolved in the code by requiring a second interrupt that detects the release of the button.  Only one rising interrupt will be processed until a
matching falling interrupt is detected.  So if there are multiple rising or button pressed interrupts detected, all secondary interrupts are ignored 
until the button is released and the falling interrupt is detected.

* [See Interrupt Handling Problem in Pico -- Raspberry Pi Forums](https://forums.raspberrypi.com/viewtopic.php?t=319655) for more details.


