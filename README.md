# simple-PID
simple PID RPI
Made for rassbberry pi kiln controller ssimple PID
download zip unzip to main pi home directory 

install
in terminal copy paste 

$    cd simple-PID-main
$    python3 -m venv venv
$    source venv/bin/activate
$    pip install -r requirements.txt

that will install it now to run it in terminal type or copy  paste one line at a time below

$    cd simple-PID-main
$    source venv/bin/activate
$    python kiln_controller.py

then open web browser open program with

http://127.0.0.1:5000/

that easy

to get it on your phone put in ip adresss of youur PI example below

Running on http://192.168.0.166:5000


Works with Maxx31855 chip only

Max31855 chip settingss 

css 8
clk 11
do 9

relay pin for heat pin 20

you can change these eit main file
TURN ON SPI SETTINGS ON YOR RPI SETTTINGS IN RASPBERRY PI ONFIGURATTIONS NDER INTERFACES

IF it gets a board error try manual install file in download install drivers one at a time see files fror manual install!!!!!

made by MeltTech 2024
