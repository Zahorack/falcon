import serial
from enum import Enum
import time, os
from datetime import datetime

# .ETC:FWD ?;..
# je nutne na zaciatku posielat ACK ?
startCmd = ['0x02', '0x45', '0x54', '0x43', '0x3a', '0x46', '0x57', '0x44', '0x20', '0x3f', '0x3b', '0x03', '0x1a']

# .ETC:VER ?;..
# asi request na konkretne data, mozno baud rate
# zeby nastaveni bad rate na 19200 ? lebo je to pred kazdym posielanim dat, ale je tam otaznik teda skorej request#
# ono to moze byt connect !!
cmd1 = ['0x02', '0x45', '0x54', '0x43', '0x3a', '0x56', '0x45', '0x52', '0x20', '0x3f', '0x3b', '0x03', '0x0e']

# ..CMN:ALL ?;..
# asi request na nejake hromadne parametre
cmd2 = ['0x06', '0x02', '0x43', '0x4d', '0x4e', '0x3a', '0x41', '0x4c', '0x4c', '0x20', '0x3f', '0x3b', '0x03', '0x1c']

# .CMN:ALM <value>;1;
# set alarm level
alarmSetHeader = ['0x02', '0x43', '0x4d', '0x4e', '0x3a', '0x41', '0x4c', '0x4d', '0x20']
alarmSetEnd = ['0x3b', '0x31', '0x3b', '0x03', '0x1d']

# set time
setTimeBegin = ['0x02', '0x52', '0x54', '0x43', '0x3a', '0x4e', '0x4f', '0x57', '0x20']
setTimeEND = ['0x3b', '0x31', '0x3b', '0x03', '0x3a']

# 32 30 32 30 30 35 32 35 31 32 31 32 30 33 3b 31 3b 03 3a]


CodeOfStartingText = 0x02
CodeOfStoppingText = 0x03
Acknowledge = 0x06

os.environ['TZ'] = 'Europe/Bratislava'
time.tzset()


def listToBytes(list):
    return bytes([int(x, 0) for x in list])


def millis():
    return int(round(time.time() * 1000))


class Falcon(object):
    def __init__(self, serial):
        self.serial = serial

        self.measData = list()
        self.measHeader = None
        self.dataValid = None

        self.measStartTime = 0
        self.alarmValue = 500

        self.intro()
        # self.startMeasurement()
        self.setAlarm(500)

        self.timeWasSend = False
        self.receviveTime = 0

        self.dataReceived = False

        self.last = 0


    def setTime(self, data):

        # treba z GPS
        # date = time.strftime('%Y%m%d')
        # cas = time.strftime('%H%M%S')

        self.serial.write(listToBytes(setTimeBegin))
        self.serial.write(str(data).encode())
        self.serial.write(listToBytes(setTimeEND))

        self.timeWasSend = True
        self.startMeasurement()

    def startMeasurement(self):
        if self.timeWasSend:
            self.dataReceived = False
            # print("start")

            self.start = time.time()
            self.measStartTime = millis()

            self.serial.write(serial.to_bytes(b'\x06'))
            self.serial.setDTR(0)
            time.sleep(0.01)
            self.serial.setDTR(1)
            self.serial.write(listToBytes(startCmd))
            self.serial.setDTR(0)
            time.sleep(0.01)
            self.serial.setDTR(1)

    def setAlarm(self, alarm):
        self.alarmValue = alarm
        self.serial.write(listToBytes(alarmSetHeader))
        self.serial.write(str(alarm).encode())
        self.serial.write(listToBytes(alarmSetEnd))

    def sendAck(self):
        self.serial.write(Acknowledge)

    def intro(self):
        self.serial.write(listToBytes(cmd1))
        self.serial.write(listToBytes(cmd2))

    def update(self):
        self.parse()

        # In case data arrived damaged


        if self.dataReceived:
            if millis() > (self.receviveTime + 150):
                # print("nova vzorka")
                self.startMeasurement()

        if millis() > (self.measStartTime + 1000):
            # print("safety")
            self.startMeasurement()

        if self.dataValid:
            self.dataValid = False
            return True

        return False

    def data(self):
        return FalconData(self.measData, self.measHeader.error, self.alarmValue)

    def parse(self):

        if self.serial.in_waiting:
            begin = self.serial.read()
            # wait for code starting of text
            if int.from_bytes(begin, 'little') == CodeOfStartingText:
                header = self.readHeader()

                # parse packet type
                if header.type.decode() == 'ETC':
                    # parse packet command
                    if header.cmd.decode() == 'FWD':
                        # print("receive data "+ str(time.time()  -self.start))
                        self.measData = self.readMeasurementData()
                    else:
                        print("Unknown command")

                elif header.type == "CMN":
                    print("Read settings parameters")
                else:
                    print("Unknown type")
            # else:
            #     print("Wrong packet mark")

    def readMeasurementData(self):
        measurement_size = 41
        dif = 0
        # read main measurement value - average of 5 next measurement - not interested
        main_meas_data = self.serial.read(5)
        self.serial.read()  # semicilon

        # read 5 times measurement data
        meas_data = list()
        for id in range(0, 5):
            data = self.serial.read(measurement_size)
            meas_data.append(data)
            # print(data)

        # split data by semicolon
        parsed_data = list()
        for meas in meas_data:
            parsed_data.append(str(meas.decode()).split(';'))

        # parsing data sequence = MEAS[5];1f[11];2f[11];time[10];
        # fill falcon data object
        falconMeasuredData = list()
        counter  = 0
        for meas in parsed_data:
            if counter == 0:
                dif = abs(self.last - int(meas[3]))
                print(dif)

                if dif == 0:
                    print("duplication")

                # print(self.last)

                if dif > 7:
                    print("cas")

                self.last = int(meas[3])
            counter += 1

            falconMeasuredData.append(FalconMeasurementData(meas[0], meas[1], meas[2], self.convertTime(meas[3])))
            # falconMeasuredData.append(FalconMeasurementData(meas[0], meas[1], meas[2], meas[3]))

        self.serial.read(2)  # space
        self.serial.read()  # semicolon
        code = self.serial.read()
        # print(code)
        if int.from_bytes(code, 'little') == CodeOfStoppingText:
            # print("Measurement data valid")
            self.dataValid = True
        else:
            print('ERROR Measured data not valid')
            self.dataValid = False

        if dif == 0:
            self.dataValid = False

        self.receviveTime = millis()

        self.dataReceived = True

        # self.startMeasurement()
        # trigger for next data

        return falconMeasuredData

    def readHeader(self):
        type = self.serial.read(3)
        self.serial.read()  # semicolon
        cmd = self.serial.read(3)
        self.serial.read()  # space
        error = self.serial.read()
        self.serial.read()  # semicolon

        self.measHeader = FalconProtocolHeader(type, cmd, str(int(error)))

        return self.measHeader

    def convertTime(self, input):
        time = int(input)

        ms100 = int(time % 10)
        time /= 10

        sec = int(time % 60)
        time /= 60

        min = int(time % 60)
        time /= 60

        hour = int(time % 24)

        return str(str(hour).zfill(2) + ':' + str(min).zfill(2) + ':' + str(sec).zfill(2) + '.' + str(ms100) + '00')


class FalconData(object):
    def __init__(self, meas, error, alarm):
        self.data = meas
        self.errorCode = error
        self.alarm = alarm


class FalconMeasurementData(object):
    def __init__(self, meas, f1, f2, time):
        self.meas = meas
        self.f1 = f1
        self.f2 = f2
        self.time = time


# Protocol header
class FalconProtocolHeader(object):
    def __init__(self, t, c, e):
        self.type = t
        self.cmd = c
        self.error = e