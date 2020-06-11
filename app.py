import time
import serial
import configparser
from falcon import logger, falcon, gnss

import RPi.GPIO as GPIO

#TODO:
# Logger time - presnost 100 ms - to bude podla casu z Falcona

sampleMeasData = "ETC:FWD 1;00115;00112;+4.8500E+02;+1.4193E+03;0000076927;00115;+4.8500E+02;+1.4570E\
+03;0000076928;00116;+4.8533E+02;+1.4770E+03;0000076929;00116;+4.8500E+02;+1.4710E+03;00\
00076930;00116;+4.8367E+02;+1.4727E+03;0000076931;"

LED1 = 21  # //app runing
LED2 = 13  # // fix, sending



def sendSampleMeasData():
    usart.write(serial.to_bytes(b'\x06'))
    usart.write(serial.to_bytes(b'\x02'))
    usart.write(sampleMeasData.encode())
    usart.write(serial.to_bytes(b'\x03'))
    usart.write(b'\n')  #check code

def millis():
    return int(round(time.time() * 1000))

configParser = configparser.RawConfigParser()
configParser.read('/falcon/config-falcon-laser.txt')

usart = serial.Serial(
        port='/dev/ttyS0',
        baudrate = 38400,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=2
)

usb = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate = 19200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=2,
        dsrdtr=True
        # rtscts = True
        # xonxoff = True
)



log = logger.Logger(usart)
falcon = falcon.Falcon(usb)
gps = gnss.Gnss(usart)


if __name__ == '__main__':

    #Configuration
    log.logDelimiter = str(configParser.get('falcon-config', 'logDelimiter').split("'")[1])
    log.configAlarm = int(configParser.get('falcon-config', 'Alarm'))
    log.configAlarm1f = int(configParser.get('falcon-config', '1fAlarm'))
    gps.configDeltaTime = int(configParser.get('falcon-config', 'utcDeltaTimeHours'))

    print("Config")
    print(log.logDelimiter)
    print(log.configAlarm)
    print(log.configAlarm1f)

    GPIO.setmode(GPIO.BCM)  # Numbers GPIOs by physical location
    GPIO.setup(LED1, GPIO.OUT)  # Set LedPin's mode is output
    GPIO.setmode(GPIO.BCM)  # Numbers GPIOs by physical location
    GPIO.setup(LED2, GPIO.OUT)  # Set LedPin's mode is output

    GPIO.output(LED1, GPIO.HIGH)

    if not usart.isOpen():
        log.usartNotOpenMessage()

    if not usb.isOpen():
        log.usbNotOpenMessage()

    # falcon.setAlarm(log.configAlarm)

    # falcon.startMeasurement()



    while True:

        if not falcon.timeWasSend:
            if gps.hasDateAndTime():
                print(gps.falconDate+gps.falconTime)
                falcon.setTime(str(gps.falconDate+gps.falconTime))

        if gps.update():
            log.updateGnss(gps.data)

        # if usart.inWaiting():
        #     print(usart.readline())

        if falcon.update():
            log.updateFalcon(falcon.data())
            if  gps.hasFix():
                GPIO.output(LED2, GPIO.HIGH)
            if not gps.hasFix():
                log.noFixMessage()
                GPIO.output(LED2, GPIO.LOW)

        log.writeTelemetry()


    usb.close()
    usart.close()
