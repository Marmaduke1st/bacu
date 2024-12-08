# Title: B-Scan Automated Calibration Unit - Mk3 B-Scan - function.py
# Author: Jono Watkins
# Version: 1.0v



#   Import the required libraries
import subprocess
from time import sleep
from functions import (wlan_profile, wifi_check, scope_setup_one, siggen_setup_one, esc_menus,
                       config, reset_cal, handtest_menu, siggen_set, relay_switch)
from elements import (init_test, transmitterPulseParameters, frequencyResponse, equivalentNoise, 
                      attenuationAccuracy, verticalLinearity, results_generator)
import pyautogui
import sys

# define the main function for calling in main.py
def main(data):
    

    # Assign Test Equipment Address object to the variables for use
    scope, siggen, sock, ser, atten_connected, end = init_test()

    if end:
        sys.exit(0)
    
    # Connect to the Electronics
    # using the serial number from the ui entry
    ssid = 'SRT-' + data['Serial Number']
    wlan_profile(ssid)

    sleep(2)

    # SRT launch
    srt = subprocess.Popen(config.get('SRT', 'LOCATION'))
    sleep(5)
    wifi_check()
    pyautogui.click(x=951, y=492)
    
    sleep(2)
    #  if the attenuator is not connected then raise an error
    if atten_connected is None:
        raise ValueError  #  TODO: Test and workout good functionality  

    scope_setup_one(scope)

    siggen_setup_one(siggen)

        # Check Trigger Signal is correct 
    #  TODO: Improve this check to ensure it meet criteria, check the trigger box is actually working and not just passing the test.
    scope.write(f":MEAS:SOUR CHAN{config.get('CHANNEL', 'TRIGGER')}")
    result = int(scope.query(f":MEAS:ITEM? VPP,CHAN{config.get('CHANNEL', 'TRIGGER')}")[0])
    if result < 1:
        raise ValueError #  TODO: Test and workout good functionality
    
    #  Reset the Calibration to ensure time to calibrate message is not displayed
    reset_cal()

    # Head Menu Setup
    handtest_menu() # selects handtest menu

    relay_switch('TX', 1, sock)
    relay_switch('RX', 1, sock)


    #set 60,80 position based on standard value
    base = siggen_set(siggen)
    sleep(1)

    transmitter_results = transmitterPulseParameters(scope, siggen, sock, 'mk3')

    frequency_results = frequencyResponse(scope, siggen, sock, base)

    noise_results = equivalentNoise(frequency_results, siggen, sock, base)

    attenuation_results = attenuationAccuracy(siggen, ser, base)

    linearity_results = verticalLinearity(siggen, ser, base)

    esc_menus()
    
    reset_cal()

    sock.close()
    ser.close()

    results_generator(data, scope, siggen, transmitter_results, frequency_results, noise_results, attenuation_results, linearity_results)

    

    srt.terminate()