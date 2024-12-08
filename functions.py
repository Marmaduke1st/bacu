# Title: B-Scan Automated Calibration Unit - Mk3 B-Scan - function.py
# Author: Jono Watkins
# Version: 1.5v

# All imports for application 
from time import sleep # To allow measurement time for other devices 
import pyautogui # used for move the mouse and entering keys
import configparser  # Allows external ini config file
import os # utilise config files
import pyvisa # for test equipment communication
from PIL import Image # for work mode detection
from pytesseract import pytesseract # for work mode detection
import cv2 # for peak detection
import numpy as np # for peak detection 
from bleak import BleakScanner # for BLE communication
import subprocess
import serial.tools.list_ports # for serial port communication
import serial # for serial port communication
import socket # for network communication
import asyncio # for asynchronous communication
import psutil # for process management

# Config File Setup - Contains the file location of the SRT software for the specific end users
# Get the path of the config file relative to the script
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
# Load the config file
config = configparser.ConfigParser()
# Read Config File
config.read(config_path)

def wlan_profile(ssid):
    """
    Connects to a WiFi network using the provided SSID.

    SSID is supplied as an argument to the function in main.py
    
    Args:
        ssid (str): The SSID of the WiFi network.

    Returns:
        None


    Scans the adpater names for the relevent WiFi adapter    
    Creates a new WiFi connection profile 
    Issues the commands to the OS to connnect to it


    """
    try:
        output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"])
        output = output.decode('utf-8')
        interface_names = []
        for line in output.splitlines():
            if "Name" in line:
                interface_name = line.split(":")[1].strip()
                interface_names.append(interface_name)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")

    #  Config docstring for the xml profile information
    config = """<?xml version=\"1.0\"?>
    <WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>"""+ssid+"""</name>
    <SSIDConfig>
        <SSID>
            <name>"""+ssid+"""</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>"""+ssid+"""</keyMaterial>
            </sharedKey>
           </security>
        </MSM>
    </WLANProfile>"""
    command = "netsh wlan add profile filename=\""+ssid+".xml\""
    with open(ssid+".xml", 'w') as file:
        file.write(config)
    os.system(command)

    sleep(1)

    command = f'netsh wlan connect name="{ssid}" ssid="{ssid}" interface={interface_names[0]}'
    os.system(command)

EQUIPMENT = {
    'HandTest': 1,
    'mk1' : 9,
    'mk2' : 9,
    'mk3' : 9,
    'mk4' : 11,
    }

# Establish a resource manager for connection to the test equipment
rm = pyvisa.ResourceManager()

def resource_init():
    """
    Initializes the test equipment resources with setups listed below.

    Returns:
        tuple: A tuple containing the scope and siggen resources.
    """
    resources = rm.list_resources()   
    scope = rm.open_resource(tuple(filter(lambda x: config.get('TEST', 'SCOPE') in x, resources))[0])
    siggen = rm.open_resource(tuple(filter(lambda x: config.get('TEST', 'SIGGEN') in x, resources))[0])
    return scope, siggen

RELAYS = {
    
    'CH1': {
        'command': 'AT+A1',
        'status': None
    },
    'CH2': {
        'command': 'AT+B1',
        'status': None
    },
    'CH3': {
        'command': 'AT+C1',
        'status': None
    },
    'CH4': {
        'command': 'AT+D1',
        'status': None
    },
    'CH5': {
        'command': 'AT+E1',
        'status': None
    },
    'CH6': {
        'command': 'AT+F1',
        'status': None
    },
    'CH7': {
        'command': 'AT+G1',
        'status': None
    },
    'CH8': {
        'command': 'AT+H1',
        'status': None
    },
    'CH9': {
        'command': 'AT+I1',
        'status': None
    },
    'CH10': {
        'command': 'AT+J1',
        'status': None
    },
    'CH11': {
        'command': 'AT+K1',
        'status': None
    },
    'main': {
        'command': 'AT+L1',
        'status': None
    },
    'TX': {
        'command': 'AT+M1',
        'status': None
    },
    'RX': {
        'command': 'AT+O1',
        'status': None
    }
}

def scope_setup_one(item):
    """
    Sets up the scope for the first test.

    Returns:
        list: A list of commands to send to the scope.
    """
    SCOPE_SETUP1 = [
        ":CHANnel1:DISPlay OFF",
        ":CHANnel2:DISPlay ON",
        ":CHANnel3:DISPlay ON",
        ":CHANnel4:DISPlay OFF",
        ":TRIGger:MODE EDGE",
        f":TRIGger:EDGe:SOURce CHANnel{config.get('CHANNEL', 'TRIGGER')}",
        ":TRIGger:EDGe:LEVel 17.2",
        f":CHAN{config.get('CHANNEL', 'TRIGGER')}:PROB 10",
        f":CHAN{config.get('CHANNEL', 'TRIGGER')}:SCAL 20",
        f":CHANnel{config.get('CHANNEL', 'TRIGGER')}:OFFset 19",
        f":CHAN{config.get('CHANNEL', 'PULSE')}:PROB 1",
        f":CHAN{config.get('CHANNEL', 'PULSE')}:SCAL 0.1",
        f":CHANnel{config.get('CHANNEL', 'PULSE')}:DISPlay ON",
        f":CHANnel{config.get('CHANNEL', 'PULSE')}:OFFset -0.2",
        ":TIMEbase:MAIN:OFFSet 0.000064",
        ":TIMEbase:MAIN:SCALe 0.00001",    
        ":RUN",
    ]
    for command in SCOPE_SETUP1:
        #  send the command to the scope
        item.write(command)
        #  wait 0.2 seconds
        sleep(0.2)

def siggen_setup_one(item):
    """
    Sets up the signal generator for the first test.

    Returns:
        list: A list of commands to send to the signal generator.
    """
    SIGGEN_SETUP1 = [
        f":OUTP{config.get('CHANNEL', 'SIGIN')}:LOAD 50",
        f":SOUR{config.get('CHANNEL', 'SIGIN')}:APPL:SIN 2250000,0.170,0,0",
        f":SOUR{config.get('CHANNEL', 'SIGIN')}:BURS ON",
        f":SOUR{config.get('CHANNEL', 'SIGIN')}:BURS:NCYC 1",
        f":SOUR{config.get('CHANNEL', 'SIGIN')}:BURS:TDEL 0.0000195",
        f":SOUR{config.get('CHANNEL', 'SIGIN')}:BURS:TRIG:SOUR EXT",
        f":SOUR{config.get('CHANNEL', 'SIGIN')}:BURS:INT:PER 0.01",
        f":OUTP{config.get('CHANNEL', 'SIGIN')} ON",
    ]
    for command in SIGGEN_SETUP1:
        #  send the command to the siggen
        item.write(command)
        #  wait 0.2 seconds
        sleep(0.2)

def scope_setup_two(item):
    """
    Sets up the scope for the second test.

    Returns:
        list: A list of commands to send to the scope.
    """
    SCOPE_SETUP2 = [
        f":CHANnel{config.get('CHANNEL', 'SWITCHOUT')}:DISPlay ON",
        f":CHANnel{config.get('CHANNEL', 'PULSE')}:DISPlay OFF",
        f":CHANnel{config.get('CHANNEL', 'TRIGGER')}:DISPlay OFF",
        ":CHANnel1:DISPlay OFF",
        f":CHAN{config.get('CHANNEL', 'SWITCHOUT')}:PROB 10",
        f":CHAN{config.get('CHANNEL', 'SWITCHOUT')}:SCAL 50",
        ":TIMEbase:MAIN:OFFSet -0.00000011",
        ":TIMEbase:MAIN:SCALe 0.00000005",
        ":TRIGger:MODE EDGE",
        f":TRIGger:EDGe:SOURce CHANnel{config.get('CHANNEL', 'SWITCHOUT')}",
        ":TRIGger:EDGe:LEVel -32",
        f":CHANnel{config.get('CHANNEL', 'SWITCHOUT')}:OFFset 90",
        ":RUN",
    ]
    for command in SCOPE_SETUP2:
        #  send the command to the scope
        item.write(command)
        #  wait 0.2 seconds
        sleep(0.2)

def esc_menus():
    """
    Presses the 'Esc' key multiple times to ensure the main menu is present.

    Returns:
        None
    """
    pyautogui.click(x=443, y=908)  # Click 'Esc'
    pyautogui.sleep(0.25)
    pyautogui.click(x=443, y=908)  # Click 'Esc'
    pyautogui.sleep(0.25)
    pyautogui.click(x=443, y=908)  # Click 'Esc'
    pyautogui.sleep(0.25)
    pyautogui.click(x=443, y=908)  # Click 'Esc'
    pyautogui.sleep(0.25)
    pyautogui.click(x=443, y=908)  # Click 'Esc'
    pyautogui.sleep(0.25)
    pyautogui.click(x=443, y=908)  # Click 'Esc'
    pyautogui.sleep(0.25)

def reset_cal():
    """
    Resets the calibration settings, adapting for the potential fullscreen or windowed textbox.

    Returns:
        None
    """
    wifi_check()
    pyautogui.click(x=1125, y=605)  # Click 'Ok'
    pyautogui.click(x=1125, y=605)  # Click 'Ok'
    pyautogui.sleep(0.25)
    pyautogui.click(x=141, y=905)  # Click 'A'
    pyautogui.sleep(0.25)
    pyautogui.click(x=1302, y=908)  # H+
    pyautogui.sleep(0.25)
    pyautogui.click(x=1014, y=909)  # E+
    pyautogui.sleep(0.25)
    pyautogui.click(x=623, y=911)  # A+
    pyautogui.sleep(0.25)
    pyautogui.click(x=915, y=906)  # D+
    pyautogui.sleep(0.25)
    pyautogui.click(x=435, y=1025)  # Execute
    pyautogui.sleep(0.25)
    pyautogui.click(x=49, y=906)  # Settings
    pyautogui.sleep(0.25)
    wifi_check()
    pyautogui.click(x=171, y=609)  # Reset Cal
    pyautogui.sleep(0.25)
    pyautogui.click(x=435, y=1025)  # Execute
    pyautogui.sleep(0.25)
    wifi_check()
    pyautogui.click(x=1016, y=405)  # Dropdown
    pyautogui.sleep(0.25)
    pyautogui.click(x=935, y=792)  # 12 months
    pyautogui.sleep(0.25)
    pyautogui.click(x=844, y=485)  # Ok
    pyautogui.sleep(1)
    pyautogui.click(x=443, y=908)  # Click 'Esc'
    pyautogui.sleep(0.25)
    pyautogui.click(x=443, y=908)  # Click 'Esc'
    pyautogui.sleep(0.25)
    pyautogui.click(x=220, y=52)  # Dropdown
    pyautogui.sleep(0.25)
    pyautogui.click(x=250, y=440)  # 12 months
    pyautogui.sleep(0.25)
    pyautogui.click(x=96, y=132)  # Ok
    pyautogui.sleep(1)
    pyautogui.click(x=443, y=908)  # Click 'Esc'
    pyautogui.sleep(0.25)
    pyautogui.click(x=443, y=908)  # Click 'Esc'
    pyautogui.sleep(0.25)

def wifi_check():
    """
    Checks if the WiFi connection is established.

    Returns:
        None
    """
    check = pyautogui.pixel(0, 470)
    while check[0] == 255:
        sleep(1)
        check = pyautogui.pixel(0,470)

def handtest_menu():
    """
    Accesses the hand test menu.

    Using OCR to read the PARAM SET value, to ensure the correct value is set.

    Returns:
        None
    """
    pyautogui.click(x=141, y=905)  # Click 'A'
    pyautogui.sleep(1)
    pyautogui.click(x=1236, y=249)  # Click 'HAND TEST ?'
    pyautogui.sleep(3)
    param_read = screenshoot('PARAM.png', (90, 538, 200, 30))  # Get PARAM SET Image?
    param_set = [int(s) for s in param_read.split() if s.isdigit()]  # Extract Number
    calc = param_set[0] - 3   # start @ 3
    if calc > 0:
        for x in range(calc):  # if more than 3, reduce
            pyautogui.click(x=626, y=1025)
            pyautogui.sleep(1)
    elif calc < 0:
        for x in range(abs(calc)):  # if less than 3, increase
            pyautogui.click(x=629, y=905)
            pyautogui.sleep(1)
    else:
        pass
    pyautogui.click(x=133, y=607)  # Click GAIN
    pyautogui.sleep(0.25)
    adjust(30.5)
    sleep(0.25)
    pyautogui.click(x=611, y=670)  # Click CRYSTAL
    pyautogui.click(x=629, y=905)  # Click A+ to ensure on Double
    pyautogui.click(x=133, y=670)  # Click ALARM THR
    adjust(0)
    pyautogui.click(x=111, y=639)  # Click Zero
    adjust(0)
    sleep(4)

def siggen_set(siggen):
    """
    Sets up reference 60/80 signal.

    Used several times during the software to set the signal to a 60/80 reference.

    Args:
        siggen (pyvisa.resources.Resource): The signal generator resource.

    Returns:
        None
    """
    peak = peak_position()
    x = peak[2]
    y = peak[3]
    volt = float(siggen.query(":SOUR1:VOLT?"))
    delay = float(siggen.query(":SOUR1:BURS:TDEL?"))
    while not 903 < x < 907 or not 80 < y < 84:
        while not 80 < y < 84:
            if y <= 70:
                volt -= 0.001
                siggen.write(f":SOUR1:VOLT {volt}")
                y = peak_position()[3] 
            if y >= 94:
                volt += 0.001
                if float(siggen.query(":SOUR1:VOLT?")) < 0.199:
                    siggen.write(f":SOUR1:VOLT {volt}")
                else:
                    break
                y = peak_position()[3]
            if y in range(70, 81):
                volt -= 0.0001
                siggen.write(f":SOUR1:VOLT {volt}")
                y = peak_position()[3]
            if y in range(84, 95):
                volt += 0.0001
                if float(siggen.query(":SOUR1:VOLT?")) < 0.199:
                    siggen.write(f":SOUR1:VOLT {volt}")
                y = peak_position()[3]
            sleep(1)
        while not 903 < x < 907:
            if x >= 917:
                delay -= 0.00000002
                siggen.write(f":SOUR1:BURS:TDEL {delay}")
                x = peak_position()[2]
            if x <= 893:
                delay += 0.00000002
                siggen.write(f":SOUR1:BURS:TDEL {delay}")
                x = peak_position()[2]
            if x in range(893, 907):
                delay += 0.00000001
                siggen.write(f":SOUR1:BURS:TDEL {delay}")
                x = peak_position()[2]
            if x in range(907, 917):
                delay -= 0.00000001
                siggen.write(f":SOUR1:BURS:TDEL {delay}")
                x = peak_position()[2]
            sleep(1)
        peak = peak_position()
        x = peak[2]
        y = peak[3]
    base_amp = float(siggen.query(":SOUR1:VOLT?"))
    base_delay = float(siggen.query(":SOUR1:BURS:TDEL?"))
    return [base_amp, base_delay]

def peak_position():
    wifi_check()
    # Take Screenshot of Screen
    pyautogui.screenshot('screenshot.png', region=(140, 38, 1510, 406))

    # Read the image
    image = cv2.imread("screenshot.png")

    # Convert the image from BGR to RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Define the specific color you want to find (in RGB format)
    target_color = (117, 134, 189)

    # Find the coordinates of the first instance of the target color
    coordinates = np.where(np.all(image == target_color, axis=-1))

    if coordinates[0].size > 0:
        # Get the x and y coordinates
        x = coordinates[1][0]
        y = coordinates[0][0]

        # Get the dimensions of the image
        height, width, _ = image.shape

        # Convert coordinates to percentage
        x_percentage = round(float((x / width) * 100))
        y_percentage = round(float((1-(y / height)) * 100))

        # Print the converted coordinates
        return x_percentage, y_percentage, x, y

    else:
        print("Target color not found in the image.")
        return None
    
def noise_peak_position():
    wifi_check()
    # Take Screenshot of Screen
    pyautogui.screenshot('noise_screenshot.png', region=(590, 38, 1210, 406))

    # Read the image
    image = cv2.imread("noise_screenshot.png")

    # Convert the image from BGR to RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Define the specific color you want to find (in RGB format)
    target_color = (117, 134, 189)

    # Find the coordinates of the first instance of the target color
    coordinates = np.where(np.all(image == target_color, axis=-1))

    if coordinates[0].size > 0:
        # Get the x and y coordinates
        x = coordinates[1][0]
        y = coordinates[0][0]

        # Get the dimensions of the image
        height, width, _ = image.shape

        # Convert coordinates to percentage
        x_percentage = round(float((x / width) * 100))
        y_percentage = round(float((1-(y / height)) * 100))

        # Print the converted coordinates
        return x_percentage, y_percentage, x, y

    else:
        print("Target color not found in the image.")
        return None

def adjust(amount):
    amount = str(amount)
    pyautogui.doubleClick(x=629, y=905)  # Double-Click A+ to bring up dialog window
    sleep(0.25)
    pyautogui.click(x=890, y=689)  # Click input box
    pyautogui.press('backspace')  # Clear the input box
    pyautogui.press('backspace')
    pyautogui.press('backspace')
    pyautogui.press('backspace')
    pyautogui.press('backspace')
    pyautogui.write(amount)  # input '30' dB
    pyautogui.click(x=1000, y=977)  # Click Enter
    return float(amount)

def screenshoot(name, region):
    wifi_check()
    pyautogui.screenshot(name, region=region)  # Take screenshot of MAC Number
    path_to_tesseract = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    img = Image.open(name)
    pytesseract.tesseract_cmd = path_to_tesseract
    text = pytesseract.image_to_string(img)
    return text[:-1]

def relay_switch(relay, command, conn):
    if RELAYS[relay]['status'] != 1:
        if command == 1:
            conn.send(RELAYS[relay]['command'].encode('utf-8'))
            sleep(0.5)
            conn.recv(1024).decode('utf-8').strip()
            RELAYS[relay]['status'] = 1
            sleep(0.5)

        else:
            pass
    else:
        if command == 0:
            conn.send(RELAYS[relay]['command'].encode('utf-8'))
            sleep(0.5)
            conn.recv(1024).decode('utf-8').strip()
            RELAYS[relay]['status'] = 0
            sleep(0.5)
        else:
            pass
 
def attenuator_init():    
    atten_connected = None
    # Serial port connection to the attenuator
    # get the list of available ports
    ports = serial.tools.list_ports.comports()
    # loop through the list of ports and find the port that is the attenuator name starts with USB Serial
    port = [str(port.device) for port in ports if "STMicro" in port.description]
    # loop through the list of ports and find the port that is the attenuator name starts with USB Serial
    port = port[0]
    try:
        # open the port
        ser = serial.Serial(port, 9600, timeout=1)
        sleep(1)
        ser.write(b'ATT-00.0\r\n')
        sleep(1)
        # read the response from the attenuator
        response = ser.read_all().decode('utf-8') 
        # check the response to see if the attenuator is connected
        if 'ATT OK' in response:
            atten_connected = True
            ser.close()
            return port, atten_connected
    except serial.SerialException as e:
        print(f"SerialException: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

async def scan(name):
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name == name:
            return device.address

def relay_init(serial):
    #  bluetooth connection to the switch
    # get bluetooth address for the supplied name
    device_address = asyncio.run(scan('BT04-A'))
    # create a socket
    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    # set the socket to reuse the address
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # connect to the device
    sock.connect((device_address, 1))

    #  Relay Status Setup 
    #  loop through the relays and switch them off   
    for relay in RELAYS:
        #  if the relay command is not m ie for the bluetooth not serial connection
        #  send the command to the relay board
        sock.send(RELAYS[relay]['command'].encode('utf-8'))
        sleep(0.5)
        #  read the response from the relay board
        response = sock.recv(1024).decode('utf-8').strip()
        #  check the response to see if the relay is off
        if response[0:4] == 'Clos':
            #  if the relay is off then set the status to 0
            RELAYS[relay]['status'] = 0
        else:
            #  if the relay is on then set the status to 1
            RELAYS[relay]['status'] = 1
        sleep(0.5)
        #  switch the relay off using the relay_switch function
        relay_switch(relay, 0, sock)
    return sock

def is_SRT_running():
    for p in psutil.process_iter(['name']):
        if p.info['name'] == "SRT.exe":
            return True
    return False

def signal_detect():
