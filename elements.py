from functions import (resource_init, relay_switch,  esc_menus, attenuator_init, 
                        relay_init, EQUIPMENT, config, scope_setup_one, 
                        scope_setup_two, handtest_menu, siggen_set, adjust, peak_position,
                        is_SRT_running, siggen_setup_one, noise_peak_position, wifi_check)
from time import sleep
import serial
import pyautogui
import math
import ctypes
import numpy as np
from fpdf import FPDF
import datetime
import os
import logging





def single_test(name):
    scope = None
    siggen = None
    sock = None
    ser = None
    base = None
    if name == 'transmitter':
        if scope is None or siggen is None or sock is None or ser is None:
            scope, siggen, sock, ser, isconnected = init_test()
        global transmitter_results
        transmitter_results = transmitterPulseParameters(scope, sock, ser, 'mk3')
    if name == 'frequency':
        if scope is None or siggen is None or sock is None or ser is None:
            scope, siggen, sock, ser, isconnected = init_test()
        if base is None:
            base = init_base_signal(scope, siggen, ser, sock)
        global frequency_results
        frequency_results = frequencyResponse(scope, siggen, sock, ser, base)
    if name == 'noise':
        if scope is None or siggen is None or sock is None or ser is None:
            scope, siggen, sock, ser, isconnected = init_test()
        if base is None:
            base = init_base_signal(siggen, ser, sock)
        if frequency_results is None:
            frequency_results = frequencyResponse(scope, siggen, sock, ser, base)
        global noise_results
        noise_results = equivalentNoise(frequency_results, siggen, sock, ser, base)
    if name == 'attenuator':
        if scope is None or siggen is None or sock is None or ser is None:
            scope, siggen, sock, ser, isconnected = init_test()
        if base is None:
            base = init_base_signal(siggen, ser, sock)
        global attenuator_results
        attenuator_results = attenuationAccuracy(ser)
    if name == 'vertical':
        if scope is None or siggen is None or sock is None or ser is None:
            scope, siggen, sock, ser, isconnected = init_test()
        if base is None:
            base = init_base_signal(siggen, ser, sock)
        
        global linearity_results
        linearity_results = verticalLinearity(siggen, ser, base)

    sock.close()
    ser.close()
    scope.close()
    siggen.close() 


# Configure logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def init_test():
    end = False
    try:
        scope, siggen = resource_init()
    except Exception as e:
        logging.error(f"Test equipment connection error: {e}")
        ctypes.windll.user32.MessageBoxW(0, "The test equipment is not found, check connections and restart", "Test Equipment Connection Error", 0x1000)
        scope = None
        siggen = None
        end = True 

    try:
        attenuator_port, is_connected = attenuator_init()
        ser = serial.Serial(attenuator_port, timeout=1)
        sleep(1)
        ser.write(b'ATT-00.50\r\n')
    except serial.SerialException as e:
        logging.error(f"Attenuator connection error: {e}")
        ctypes.windll.user32.MessageBoxW(0, "The attenuator is not found, check connections and restart", "Attenuator Connection Error", 0x1000)
        ser = None
        is_connected = None
        end = True


    try: 
        sock = relay_init(ser)
    except Exception as e:
        logging.error(f"Relay box connection error: {e}")
        ctypes.windll.user32.MessageBoxW(0, "The SwitchBox is not found, check connections, power and restart", "Relay Box Connection Error", 0x1000)
        sock = None
        end = True


    return scope, siggen, sock, ser, is_connected, end

def init_base_signal(scope, siggen, serial, sock):
    if not is_SRT_running():
        ctypes.windll.user32.MessageBoxW(0, "SRT isn't running", "SRT Error", 1)
        exit()
    
    esc_menus() # start the same location
    handtest_menu() # access hand test menu

    scope_setup_one(scope)
    siggen_setup_one(siggen)

    relay_switch('TX', 1, sock)
    relay_switch('RX', 1, sock)
    relay_switch('main', 0, sock)

    base = siggen_set(siggen)

    return base

def transmitterPulseParameters(scope, siggen, sock, mk):
    #  Transmitter Pulse Parameters
    #  switch the TX relay off
    relay_switch('TX', 0, sock)
    #  switch the RX relay off
    relay_switch('RX', 0, sock)
    # siggen.write(f":OUTP{config.get('CHANNEL', 'SIGIN')} OFF") # set Amplitude to Zero
    #  switch the main relay on
    relay_switch('main', 1, sock)
    #  Come out of hand test menu
    esc_menus()
    #  Scope Setup
    #  loop through the commands in the SCOPE_SETUP2 list and send them to the scope
    scope_setup_two(scope)
    
    transmitter_results = {}
    for i in range(1, EQUIPMENT[mk]+1):
        transmitter_results['CH'+str(i)] = {
            'voltage': 0,
            'rise': 0,
            'duration': 0,
            'voltage_pass': '',
            'rise_pass': '',
            'duration_pass': ''
    }    
    
    # for each channel in the list above read each channel's voltage, rise time and duration, store results 
    for channel in transmitter_results:
        #  switch the relay to the channel
        relay_switch(channel, 1, sock)
        #  wait 1 second
        sleep(1)
        #  read the voltage from the scope
        transmitter_results[channel]['voltage'] = float(scope.query(":MEAS:ITEM? VMIN, CHAN4"))
        #  check the voltage is between 225 and 275
        if -264 <= transmitter_results[channel]['voltage'] <= -216:
            #  if the voltage is between 225 and 275 then add PASS to the pulse list
            transmitter_results[channel]['voltage_pass'] = "PASS"
            #  add 1 to the pulse voltage list
        else:
            #  if the voltage is not between 225 and 275 then add FAIL to the pulse list
            transmitter_results[channel]['voltage_pass'] = "FAIL"
        #  wait 1 second
        sleep(1)
        #  read the rise time from the scope
        transmitter_results[channel]['rise'] = float(scope.query(":MEAS:ITEM? FTIM, CHAN4"))*1000000000

        #  check the rise time is less than 50
        if transmitter_results[channel]['rise'] < 50:
            #  if the rise time is less than 50 then add PASS to the pulse list
            transmitter_results[channel]['rise_pass'] = "PASS"
            #  add 1 to the pulse voltage list
        else:
            #  if the voltage is not between 225 and 275 then add FAIL to the pulse list
            transmitter_results[channel]['rise_pass'] = "FAIL"
        #  wait 1 second
        sleep(1)
        #  read the duration from the scope
        transmitter_results[channel]['duration'] = float(scope.query(":MEAS:ITEM? NWID, CHAN4"))*1000000000
        #  format the duration to 2 decimal places
        sleep(1)
        if transmitter_results[channel]['duration'] < 250: # if acceptable
            transmitter_results[channel]['duration_pass'] = "PASS"
            
        else:
            transmitter_results[channel]['duration_pass'] = "FAIL"
        
        relay_switch(channel, 0, sock)
        
    # Handle 'Overall' logic after the loop
    transmitter_results['Overall'] = {
        'voltage': 'PASS' if all(result['voltage_pass'] == 'PASS' for result in transmitter_results.values() if 'voltage_pass' in result) else 'FAIL',
        'rise': 'PASS' if all(result['rise_pass'] == 'PASS' for result in transmitter_results.values() if 'rise_pass' in result) else 'FAIL',
        'duration': 'PASS' if all(result['duration_pass'] == 'PASS' for result in transmitter_results.values() if 'duration_pass' in result) else 'FAIL',
        'pass': ''
    }
    
    transmitter_results['Overall']['pass'] = 'PASS' if all(result == 'PASS' for result in list(transmitter_results['Overall'].values())[0:3]) else 'FAIL'
    

    return transmitter_results

def frequencyResponse(scope, siggen, sock, base):
    esc_menus() # start the same location
    handtest_menu() # access hand test menu

    scope_setup_one(scope)
    siggen_setup_one(siggen)

    relay_switch('TX', 1, sock)
    relay_switch('RX', 1, sock)
    relay_switch('main', 0, sock)

    siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT {base[0]}") # set Amplitude to Zero
    siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:BURS:TDEL {base[1]}") # set delay to base
    siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:FREQ 2250000") # set Frequency
    sleep(3)

    # Frequency Response
    frequency_results = {
        'vpp': 0,
        'upper': 0,
        'lower': 0,
        'centre': 0,
        'centre_pass': '',
        'bandwidth': 0,
        'bandwidth_pass': '',
        'pass': ''

    }
    
    # ensure cursor is in the correct position
    pyautogui.click(x=133, y=607)  # Click GAIN
    pyautogui.sleep(0.25)
    adjust(27.5) # adjust to 27dB
    sleep(1)
    # Set the signal to 80/60 position and record value in variable
    freq_base = siggen_set(siggen)
    # measure and record VPP value
    sleep(1)
    frequency_results['vpp'] = float(scope.query(f":MEAS:VPP? CHAN{config.get('CHANNEL', 'PULSE')}"))*1000 # read VPP
    
    # adjust gain to 30dB
    adjust(30.5)
    sleep(2)
    # set the amplitude variable to the base value
    freq_amp = freq_base[0]
    # declare frequency step and current frequency
    freq_step = 20000
    current_freq = 2250000
    freq = current_freq + freq_step
    position = peak_position() # check the position of the peak
    # set fsh variable to the position of the peak
    fsh = position[1]
    # declare volt step variable
    volt_step = 0.001
    #  Measuring Upper Frequency
    while fsh > 80: # if the full screen is more than 80
        wifi_check() # check the wifi
        freq = freq + freq_step # increase frequency
        siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:FREQ {freq}") # send command
        current_vpp = float(scope.query(f":MEAS:ITEM? VPP,CHAN{config.get('CHANNEL', 'PULSE')}"))*1000 #  TODO: Look into and fix ASAP VPP
        sleep(0.25)
        volt = float(siggen.query(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT?")) + volt_step #  TODO: Look into and fix ASAP amplitude
        while current_vpp > frequency_results['vpp']:
            wifi_check()
            siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT {volt}") # set amplitude # send new voltage step
            sleep(0.25)
            volt = volt - volt_step # reduce amplitude
            current_vpp = float(scope.query(f":MEAS:ITEM? VPP,CHAN{config.get('CHANNEL', 'PULSE')}"))*1000 # read VPP
        volt = volt - volt_step
        while current_vpp < frequency_results['vpp']:
            wifi_check()
            siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT {volt}") # set amplitude
            sleep(0.25)
            volt = volt + volt_step
            current_vpp = float(scope.query(f":MEAS:ITEM? VPP,CHAN{config.get('CHANNEL', 'PULSE')}"))*1000 # read VPP
        fsh = peak_position()[1]
    frequency_results['upper'] = float(siggen.query(f":SOUR{config.get('CHANNEL', 'SIGIN')}:FREQ?"))/1000000 #  TODO: Look into and fix ASAP frequency
    sleep(1)
    siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT {freq_amp}") # set amplitude
    sleep(1)
    siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:FREQ 2250000") # set frequency
    freq = current_freq - freq_step
    sleep(1)
    position = peak_position()  # check the position of the peak
    fsh = position[1]
    #  Measuring Lower Frequency
    while fsh > 80:
        wifi_check() # check the wifi
        freq = freq - freq_step
        siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:FREQ {freq}") # set frequency
        current_vpp = float(scope.query(f":MEAS:ITEM? VPP,CHAN{config.get('CHANNEL', 'PULSE')}"))*1000 # read VPP
        sleep(0.25)
        volt = float(siggen.query(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT?")) - volt_step #  TODO: Look into and fix ASAP amplitude
        while current_vpp > frequency_results['vpp']:
            wifi_check()
            siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT {volt}") # set amplitude
            sleep(0.25)
            volt = volt - volt_step
            current_vpp = float(scope.query(f":MEAS:ITEM? VPP,CHAN{config.get('CHANNEL', 'PULSE')}"))*1000 # read VPP
        volt = volt + volt_step
        while current_vpp < frequency_results['vpp']:
            wifi_check()
            siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT {volt}") # set amplitude
            sleep(0.25)
            volt = volt + volt_step
            current_vpp = float(scope.query(f":MEAS:ITEM? VPP,CHAN{config.get('CHANNEL', 'PULSE')}"))*1000 # read VPP
        fsh = peak_position()[1]
    frequency_results['lower'] = float(siggen.query(f":SOUR{config.get('CHANNEL', 'SIGIN')}:FREQ?"))/1000000 #  TODO: Look into and fix ASAP frequency
    frequency_results['centre'] = float(format(math.sqrt(frequency_results['upper'] * frequency_results['lower']), '.2f')) # calculate the square root of upper * lower


    if 2.0 <= frequency_results['centre'] <= 3.5: # If acceptable then
        frequency_results['centre_pass'] = "PASS"
    else:
        frequency_results['centre_pass'] = "FAIL"

    frequency_results['bandwidth'] = float(format(frequency_results['upper'] - frequency_results['lower'], '.2f')) # calculate the bandwidth

    if 3.0 <= frequency_results['bandwidth'] <= 6.5: # If acceptable then
        frequency_results['bandwidth_pass'] = "PASS"
    else:
        frequency_results['bandwidth_pass'] = 'FAIL'
    sleep(1)

    if frequency_results['centre_pass'] == "PASS" and frequency_results['bandwidth_pass'] == "PASS":
        frequency_results['pass'] = "PASS"
    else:
        frequency_results['pass'] = "FAIL"

    return frequency_results

def equivalentNoise(frequency_results, siggen, sock, base):

    noise_results = {
        'max_noise': 0,
        'vein': 0,
        'nin': 0,
        'pass': ''
    }
    
    relay_switch('TX', 0, sock)
    relay_switch('RX', 0, sock)
    # siggen.write(f":OUTP{config.get('CHANNEL', 'SIGIN')} OFF")


    siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT 0.001") # set Amplitude to Zero
    siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:BURS:TDEL {base[1]}") # set delay to base
    siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:FREQ 2250000") # set Frequency
    sleep(3)

    pyautogui.click(x=133, y=607)  # Click GAIN
    adjust(80) # increase gain to 80dB
    results = []
    for x in range(20): # take 20 measurements of the peak position due to the high dB can cause jitter
        height = noise_peak_position()[1]
        results.append(height)
    noise_results['max_noise'] = sum(results) / len(results) # average the 20 results and save the value
    pyautogui.click(x=133, y=607)  # Click GAIN
    adjust(40.5) # back to 40dB

    relay_switch('TX', 1, sock)
    relay_switch('RX', 1, sock)
    # siggen.write(f":OUTP{config.get('CHANNEL', 'SIGIN')} ON")
    sleep(5)
    volt_step = 0.0001
    volt = 0.001
    while peak_position()[1] < noise_results['max_noise']:
        siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT {volt}") # set Amplitude
        sleep(0.2)
        volt = volt + volt_step
    
    noise_results['vein'] = float(siggen.query(f"SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT?"))*1000
    
    sleep(2)
    noise_results['nin'] = float(format(float(((noise_results['vein'])/100)/(math.sqrt(frequency_results['bandwidth']*1000000)))*1000000, '.2f')) # calculate nin

    if noise_results['nin'] < 130: # if less than 80 its a PASS
        noise_results['pass'] = 'PASS'
    else:
        noise_results['pass'] = 'FAIL'

    return noise_results

def attenuationAccuracy(siggen, serial, base):

    siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT {base[0]}") # set Amplitude to Zero
    siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:BURS:TDEL {base[1]}") # set delay to base
    siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:FREQ 2250000") # set Frequency
    sleep(3)

    atten_results =  {
        'ATT-01.50\r\n': {'gain': 31.5, 'result': 0, 'pass': ''},
        'ATT-02.50\r\n': {'gain': 32.5, 'result': 0, 'pass': ''},
        'ATT-04.50\r\n': {'gain': 34.5, 'result': 0, 'pass': ''},
        'ATT-08.50\r\n': {'gain': 38.5, 'result': 0, 'pass': ''},
        'ATT-10.50\r\n': {'gain': 40.5, 'result': 0, 'pass': ''},
        'ATT-20.50\r\n': {'gain': 50.5, 'result': 0, 'pass': ''},
        'ATT-40.50\r\n': {'gain': 70.5, 'result': 0, 'pass': ''},
    }
    # Attenuator Accuracy
    sleep(1)
    pyautogui.click(x=133, y=607)  # Click GAIN 
    adjust(30.5) # adjust to 30dB
    serial.write(b'ATT-00.50\r\n') # ensure attenuator is 0dB
    sleep(2)
    for command in atten_results:    
        serial.write(command.encode('utf-8'))
        sleep(2)
        gain = atten_results[command]['gain']
        adjust(gain)
        sleep(2)
        peak = noise_peak_position()
        while peak[1] > 80:
            adjust(gain - 0.5)
            gain -= 0.5
            sleep(2)
            peak = noise_peak_position()
        while peak[1] < 80:
            adjust(gain + 0.5)
            gain += 0.5
            sleep(2)
            peak = noise_peak_position()
        if gain > atten_results[command]['gain'] + 1.0 or gain < atten_results[command]['gain'] - 1.0:
            if atten_results[command]['gain'] == 70.5 and gain in np.arange(68.5, 73.0, 0.5):
                atten_results[command]['result'] = gain
                atten_results[command]['pass'] = 'PASS'
            else:
                atten_results[command]['result'] = gain
                atten_results[command]['pass'] = 'FAIL'
        else:
            atten_results[command]['result'] = gain
            atten_results[command]['pass'] = 'PASS'
        sleep(2)
    
    serial.write(b'ATT-00.50\r\n')
    sleep(2)

    atten_results['Overall'] = {'pass': 'PASS' if all(result['pass'] == 'PASS' for result in atten_results.values() if 'pass' in result) else 'FAIL'}

    return atten_results

def verticalLinearity(siggen, serial, base):
    handtest_menu()
    sleep(1)
    siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT {base[0]}")  # set Amplitude to base value
    siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:BURS:TDEL {base[1]}")
    sleep(1)
    serial.write(b'ATT-02.5\r\n')
    sleep(2)
    siggen_set(siggen)
    sleep(2)
    # volt = float(siggen.query(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT?"))
    # sleep(1)
    # siggen.write(f":SOUR{config.get('CHANNEL', 'SIGIN')}:VOLT {volt+0.002}")
    linearity_results = {
            0: {'fsh': 100, 'result': 0, 'command': 'ATT-00.50\r\n', 'pass': ''},
            1: {'fsh': 90, 'result': 0, 'command': 'ATT-01.50\r\n', 'pass': ''},
            2: {'fsh': 80, 'result': 0, 'command': 'ATT-02.50\r\n', 'pass': ''},
            4: {'fsh': 64, 'result': 0, 'command': 'ATT-04.50\r\n', 'pass': ''},
            6: {'fsh': 50, 'result': 0, 'command': 'ATT-06.50\r\n', 'pass': ''},
            8: {'fsh': 40, 'result': 0, 'command': 'ATT-08.50\r\n', 'pass': ''},
            12: {'fsh': 25, 'result': 0, 'command': 'ATT-12.50\r\n', 'pass': ''},
            14: {'fsh': 20, 'result': 0, 'command': 'ATT-14.50\r\n', 'pass': ''},
            20: {'fsh': 10, 'result': 0, 'command': 'ATT-20.50\r\n', 'pass': ''},
            26: {'fsh': 5, 'result': 0, 'command': 'ATT-26.50\r\n', 'pass': ''}
            }
    
    for item in linearity_results:
        serial.write(linearity_results[item]['command'].encode('utf-8'))
        sleep(5)
        wifi_check()
        for x in range(20):
            peak = peak_position()
        sleep(1)
        if peak[1] in range(linearity_results[item]['fsh'] - 2, linearity_results[item]['fsh'] + 3):
            linearity_results[item]['result'] = peak[1]
            linearity_results[item]['pass'] = 'PASS'
        else: 
            linearity_results[item]['result'] = peak[1]
            linearity_results[item]['pass'] = 'FAIL'
        sleep(2)

    linearity_results['Overall'] = {'pass': 'PASS' if all(result['pass'] == 'PASS' for result in linearity_results.values() if 'pass' in result) else 'FAIL'}
    serial.write(b'ATT-00.50\r\n') # turn off all attenuators
    sleep(2)
    serial.close() # disconnect from attenuator
    
    return linearity_results

def results_generator(userData, scope, siggen, transmitter_results, frequency_results, noise_results, attenuator_results, linearity_results):
     #  Modify the PDF class to allow Header and Footer as per my design
    class PDF(FPDF):
        def header(self):
            # self.image(resource_path('C:\\Users\\Sperry\\Documents\\ATE\\BScanATE\\dist\\BACU\\_internal\\Sperry Logo 25.jpeg'), 165, 8, 35)
            self.set_font('helvetica', 'B', 20)
            self.set_text_color(0,0,0)
            self.cell(0, 10, 'Sperry Rail International', new_x='LMARGIN', new_y='NEXT')
            self.set_font_size(16)
            self.cell(0, 10, 'B-Scan Calibration Results')
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('helvetica', '', 12)
            self.set_text_color(0,0,0)
            self.cell(0,10,f'Page {self.page_no()}/{{nb}}', align='R')

    #  Define the PDF config, Orientation, Measurement Unit and Paper Size
    pdf = PDF('P', 'mm', 'A4')

    #  Add the first PDF Page
    pdf.add_page()

    pdf.ln(10)
    # Overall Result Text and colour change dependant of result text
    pdf.set_font('helvetica', 'B', 16)
    pdf.cell(50, 10, 'Overall Result:')
    pdf.set_font('helvetica', '', 16)

    overall_cal_result = 'PASS' if transmitter_results['Overall']['pass'] == 'PASS' and frequency_results['pass'] == 'PASS' and noise_results['pass'] == 'PASS' and attenuator_results['Overall']['pass'] == 'PASS' and linearity_results['Overall']['pass'] == 'PASS' else 'FAIL'

    if overall_cal_result == 'PASS':
        pdf.set_text_color(50, 168, 82)
    else:
        pdf.set_text_color(255,0,0)

    pdf.cell(40, 10, overall_cal_result, new_x='LMARGIN', new_y='NEXT')

    #  Reset text colour to Black
    pdf.set_text_color(0,0,0)

    # Operator's Name, Serial Number
    INPUT_DATA = [(userData["Operator's Name"], f"SRT-{userData['Serial Number']}")]

    pdf.set_font('helvetica', '', 12)
    with pdf.table(first_row_as_headings=False) as table:
        for data_row in INPUT_DATA:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    # Date
    DATE_DATA = (('Date:', datetime.datetime.now().strftime('%d/%m/%Y')),) 

    pdf.set_font('helvetica', '', 12)
    with pdf.table(first_row_as_headings=False) as table:
        for data_row in DATE_DATA:
            row = table.row()
            for datum in data_row:
                row.cell(datum)

    #  Padding
    pdf.cell(0,10, '', new_x='LMARGIN', new_y='NEXT')

    scope_info = scope.query('*IDN?').split(',')
    siggen_info = siggen.query('*IDN?').split(',')


    # Equipment Used Table
    EQUIPMENT_DATA = (('Visual:', 'Make', 'Model', 'Serial Number'),
                    ("Oscilloscope:", scope_info[0], scope_info[1], scope_info[2]),
                    ('Signal Generator:', siggen_info[0], siggen_info[1], siggen_info[2]),
                    ('Attenuator', "Sperry Rail", 'SR-ATTEN', config.get('ATE', 'ID')),
                    ('Switch Box', "Sperry Rail", 'SR-SWITCH', config.get('ATE', 'ID')))

    with pdf.table(col_widths=(20, 23, 15, 20)) as table:
        for data_row in EQUIPMENT_DATA:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    #  Padding
    pdf.cell(0,20, '', new_x='LMARGIN', new_y='NEXT')

    # Visual Inspection Table
    INSPECT_DATA = (('Visual Inspection',),)

    with pdf.table() as table:
        for data_row in INSPECT_DATA:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    INSPECT_DETAIL = (('Case Integrity', userData['Case Integrity']),
                    ('RSU Connector', userData['RSU Connector']),
                    ('HandTest Connector', userData['HandTest Connector']),
                    ('Encoder Connector', userData['Encoder Connector']),
                    ('Battery Cable', userData['Battery Cable']),
                    ('Details', userData['Details']))

    with pdf.table(first_row_as_headings=False) as table:
        for data_row in INSPECT_DETAIL:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    pdf.add_page()

    #  Transmitter Pulse Parameters
    pdf.set_font('helvetica', 'BU', 14)
    pdf.cell(0,10, 'Transmitter Pulse Parameters:', new_x='LMARGIN', new_y='NEXT')

    # Transmitter Pulse Parameters Table
    ## TODO: need to be loop generated to cope with different equipment
    PULSE_DATA = (('Pulser', 'Voltage(V)', '-240V ±10%', 'Rise Time(nSec)', '< 50 nSec', 'Duration(nSec)', '< 250 nSec'),
                ('1', format(transmitter_results['CH1']['voltage'], '.2f'), transmitter_results['CH1']['voltage_pass'], format(transmitter_results['CH1']['rise'], '.2f'), transmitter_results['CH1']['rise_pass'], format(transmitter_results['CH1']['duration'], '.2f'), transmitter_results['CH1']['duration_pass']),
                ('2', format(transmitter_results['CH2']['voltage'], '.2f'), transmitter_results['CH2']['voltage_pass'], format(transmitter_results['CH2']['rise'], '.2f'), transmitter_results['CH2']['rise_pass'], format(transmitter_results['CH2']['duration'], '.2f'), transmitter_results['CH2']['duration_pass']),
                ('3', format(transmitter_results['CH3']['voltage'], '.2f'), transmitter_results['CH3']['voltage_pass'], format(transmitter_results['CH3']['rise'], '.2f'), transmitter_results['CH3']['rise_pass'], format(transmitter_results['CH3']['duration'], '.2f'), transmitter_results['CH3']['duration_pass']),
                ('4', format(transmitter_results['CH4']['voltage'], '.2f'), transmitter_results['CH4']['voltage_pass'], format(transmitter_results['CH4']['rise'], '.2f'), transmitter_results['CH4']['rise_pass'], format(transmitter_results['CH4']['duration'], '.2f'), transmitter_results['CH4']['duration_pass']),
                ('5', format(transmitter_results['CH5']['voltage'], '.2f'), transmitter_results['CH5']['voltage_pass'], format(transmitter_results['CH5']['rise'], '.2f'), transmitter_results['CH5']['rise_pass'], format(transmitter_results['CH5']['duration'], '.2f'), transmitter_results['CH5']['duration_pass']),
                ('6', format(transmitter_results['CH6']['voltage'], '.2f'), transmitter_results['CH6']['voltage_pass'], format(transmitter_results['CH6']['rise'], '.2f'), transmitter_results['CH6']['rise_pass'], format(transmitter_results['CH6']['duration'], '.2f'), transmitter_results['CH6']['duration_pass']),
                ('7', format(transmitter_results['CH7']['voltage'], '.2f'), transmitter_results['CH7']['voltage_pass'], format(transmitter_results['CH7']['rise'], '.2f'), transmitter_results['CH7']['rise_pass'], format(transmitter_results['CH7']['duration'], '.2f'), transmitter_results['CH7']['duration_pass']),
                ('8', format(transmitter_results['CH8']['voltage'], '.2f'), transmitter_results['CH8']['voltage_pass'], format(transmitter_results['CH8']['rise'], '.2f'), transmitter_results['CH8']['rise_pass'], format(transmitter_results['CH8']['duration'], '.2f'), transmitter_results['CH8']['duration_pass']),
                ('9', format(transmitter_results['CH9']['voltage'], '.2f'), transmitter_results['CH9']['voltage_pass'], format(transmitter_results['CH9']['rise'], '.2f'), transmitter_results['CH9']['rise_pass'], format(transmitter_results['CH9']['duration'], '.2f'), transmitter_results['CH9']['duration_pass']))
    
    
    pdf.set_font('helvetica', '', 12)
    with pdf.table(col_widths=(9, 10, 11, 10, 9, 12, 9)) as table:
        for data_row in PULSE_DATA:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    PULSE_DETAIL = (('All Pulser Voltages ± 10% - 240v',	transmitter_results['Overall']['voltage']),
                    ('All Pulser Rise Time Less than 50 nSec', transmitter_results['Overall']['rise']), 
                    ('All Pulser Duration Less than 250 nSec', transmitter_results['Overall']['duration']))

    with pdf.table(first_row_as_headings=False) as table:
        for data_row in PULSE_DETAIL:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    pdf.add_page()

    #  Receiver Parameters
    pdf.set_font('helvetica', 'BU', 14)
    pdf.cell(0,10, 'Receiver:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0,10, r'Amplifier Frequency Response (60% Ref Time/ 80% FSH)', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 12)
    # Amplifier Frequency Response Table
    AMP_DATA = (('Upper Frequency(- 3dB) =', frequency_results['upper'], 'Mhz'),
                ('Lower Frequency(- 3dB) =', frequency_results['lower'], 'Mhz'),
                ('80% Ref Voltage =', frequency_results['vpp'], 'mVPP'),
                ('Centre Frequency', frequency_results['centre'], 'Mhz'))

    with pdf.table(first_row_as_headings=False) as table:
        for data_row in AMP_DATA:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    CENT_ACCPT = (('Centre Frequency Accpt = 2.0Mhz | 3.5Mhz',	frequency_results['centre_pass']),)

    with pdf.table(first_row_as_headings=False) as table:
        for data_row in CENT_ACCPT:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    BANDWIDTH = (('Bandwidth (3dB) =', frequency_results['bandwidth'], 'Mhz'),)

    with pdf.table(first_row_as_headings=False) as table:
        for data_row in BANDWIDTH:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    BANDWIDTH_ACCPT = (('Bandwidth Accpt = 3.0Mhz | 6.5Mhz',	frequency_results['bandwidth_pass']),)

    with pdf.table(first_row_as_headings=False) as table:
        for data_row in BANDWIDTH_ACCPT:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))
    #  Equivalent Noise Test
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0,10, r'Equivalent Noise Test (Dual Probe OP)', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 12)
    # Receiver Parameters Table
    AMP_DATA = (('Max Gain Noise =', noise_results['max_noise'], r'%FSH'),
                ('Vein =', format(noise_results['vein'], '.2f'), 'mV'),
                ('N(in) =', noise_results['nin'], 'nV'))

    with pdf.table(first_row_as_headings=False) as table:
        for data_row in AMP_DATA:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    CENT_ACCPT = (('N(in) Accpt = < 130nV / Square Root of Bandwidth',	noise_results['pass']),)

    with pdf.table(first_row_as_headings=False) as table:
        for data_row in CENT_ACCPT:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    #  Accuracy of Calibrated Attn
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0,10, r'Accuracy of Calibrated Attn', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 12)
    pdf.cell(0,10, r'REF Sig = 60% FSW & 80% FSH FD ATTN = 30dB', new_x='LMARGIN', new_y='NEXT')

    # Attenuation Table
    ATTEN_DATA = (('Fixed Attn', 'B-Scan Gain', 'Gain - Ref', 'PASS or FAIL'),
                ('1', attenuator_results['ATT-01.50\r\n']['result'], attenuator_results['ATT-01.50\r\n']['result'] - attenuator_results['ATT-01.50\r\n']['gain'], attenuator_results['ATT-01.50\r\n']['pass']),
                ('2', attenuator_results['ATT-02.50\r\n']['result'], attenuator_results['ATT-02.50\r\n']['result'] - attenuator_results['ATT-02.50\r\n']['gain'], attenuator_results['ATT-02.50\r\n']['pass']),
                ('4', attenuator_results['ATT-04.50\r\n']['result'], attenuator_results['ATT-04.50\r\n']['result'] - attenuator_results['ATT-04.50\r\n']['gain'], attenuator_results['ATT-04.50\r\n']['pass']),
                ('8', attenuator_results['ATT-08.50\r\n']['result'], attenuator_results['ATT-08.50\r\n']['result'] - attenuator_results['ATT-08.50\r\n']['gain'], attenuator_results['ATT-08.50\r\n']['pass']),
                ('10', attenuator_results['ATT-10.50\r\n']['result'], attenuator_results['ATT-10.50\r\n']['result'] - attenuator_results['ATT-10.50\r\n']['gain'], attenuator_results['ATT-10.50\r\n']['pass']),
                ('20', attenuator_results['ATT-20.50\r\n']['result'], attenuator_results['ATT-20.50\r\n']['result'] - attenuator_results['ATT-20.50\r\n']['gain'], attenuator_results['ATT-20.50\r\n']['pass']),
                ('40', attenuator_results['ATT-40.50\r\n']['result'], attenuator_results['ATT-40.50\r\n']['result'] - attenuator_results['ATT-40.50\r\n']['gain'], attenuator_results['ATT-40.50\r\n']['pass']))

    with pdf.table() as table:
        for data_row in ATTEN_DATA:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    ATTEN_ACCPT = (('Error 0 - 20dB  ± 0.5(db)',	'PASS' if all(result['pass'] == 'PASS' for result in list(attenuator_results.values())[0:6] if 'pass' in result) else 'FAIL'),
                ('Overall Accpt', attenuator_results['Overall']['pass']),)

    with pdf.table(first_row_as_headings=False) as table:
        for data_row in ATTEN_ACCPT:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    pdf.add_page()

    #  Linearity of Vertical Display
    pdf.set_font('helvetica', 'BU', 14)
    pdf.cell(0,10, r'Linearity of Vertical Display:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('helvetica', '', 12)
    # Receiver Parameters Table

    LINEAR_RESULTS = ((r'REF %FSH', r'Actual %FSH', 'PASS or FAIL'),
                    ('100', linearity_results[0]['result'], linearity_results[0]['pass']),
                    ('90', linearity_results[1]['result'], linearity_results[1]['pass']),
                    ('80', linearity_results[2]['result'], linearity_results[2]['pass']),
                    ('64', linearity_results[4]['result'], linearity_results[4]['pass']),
                    ('50', linearity_results[6]['result'], linearity_results[6]['pass']),
                    ('40', linearity_results[8]['result'], linearity_results[8]['pass']),
                    ('25', linearity_results[12]['result'], linearity_results[12]['pass']),
                    ('20', linearity_results[14]['result'], linearity_results[14]['pass']),
                    ('10', linearity_results[20]['result'], linearity_results[20]['pass']),
                    ('5', linearity_results[26]['result'], linearity_results[26]['pass']))
                    
    with pdf.table(first_row_as_headings=False) as table:
        for data_row in LINEAR_RESULTS:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    LINEAR_ACCPT = (('Overall Accpt', linearity_results['Overall']['pass']),)

    with pdf.table(first_row_as_headings=False) as table:
        for data_row in LINEAR_ACCPT:
            row = table.row()
            for datum in data_row:
                row.cell(str(datum))

    #  Output PDF
    pdf.output(f'SRT-{userData["Serial Number"]}.pdf') 

    os.system(f'start SRT-{userData["Serial Number"]}.pdf')


# scope, siggen, sock, ser, is_connected, end = init_test() # run the test
#
# base = init_base_signal(scope, siggen, ser ,sock) # get the base signal
#
# print(verticalLinearity(siggen, ser, base))