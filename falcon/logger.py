import itertools
import copy
from falcon.falcon import FalconData, FalconMeasurementData
from falcon.gnss import GnssData

logHeader = ['DATE', 'TIME', 'MEAS', 'ERROR', 'ALARM', '1F', '2F', 'LAT', 'N', 'LON','E', 'ALT', 'M', 'SATNUM']

class Logger(object):
    def __init__(self, serial):
        self.serial = serial

        self.name = str()
        self.logDelimiter = ' '

        self.date = str()
        self.time = str()

        self.configAlarm = None
        self.configAlarm1f = None

        self.falconAlarmAlert = str();
        self.falconErrorCode = str();


        self.falcon = FalconMeasurementData(None, None, None, None)
        self.gps = GnssData()

        self.gpsList = []


    def writeOnDisk(self):
        path = '/falcon/'
        if self.name:
            with open(path+'logs/'+self.name, 'a', newline='', encoding='utf8') as file:
                file.write(self.string())
                file.write('\n')

        elif self.gps.Date and self.gps.Time:
            # self.name = self.gps.Date+"_"+str(self.gps.Time)+'.txt'
            self.name = self.gps.Date + "_" + str(self.gps.Time)
            self.name = self.name.replace('.', '').replace(':', '')
            self.name = self.name + ".txt"

            with open(path+'logs/'+self.name, 'a', newline='', encoding='utf8') as file:
                file.write(self.logDelimiter.join(map(str, logHeader)))
                file.write('\n')




    def write(self):
        # print(self.string())
        self.writeOnDisk()
        # print(self.falcon.time)

        self.serial.write(self.string().encode('utf-8'))
        self.serial.write(b'\n')

    def updateGnss(self, gnssData):
        self.gps = gnssData

        self.gpsList.append(copy.copy(gnssData))

        if len(self.gpsList) > 5:
            self.gpsList.pop(0)

    def updateFalcon(self, falconData):
        # print("updateFalcon")

        self.falconErrorCode = falconData.errorCode

        # print("new")
        counter = 0
        if len(self.gpsList) > 4:
            for data, gps in zip(falconData.data, self.gpsList):
                # print(data.meas, data.f1, data.f2, data.time)
                if int(data.meas) > int(self.configAlarm) and float(data.f1) > float(self.configAlarm1f):
                    self.falconAlarmAlert = 1
                else:
                    self.falconAlarmAlert = 0

                self.falcon = data
                self.gps = gps


                #self.gps.Lat = self.convertGps(self.gps.Lat)
                #self.gps.Lon = self.convertGps(self.gps.Lon)

                counter += 1
                self.write()


    def convertGps(self, input):
        s = str(input).strip("0")

        splits = s.split(".")

        if len(splits[0]) == 0:
            out = str(round(float(s)/ 60, 7))
        elif len(splits[0]) == 1:
            out = str(round(float(s[:1]) + float(s[1:])/60, 7))
        elif len(splits[0]) > 1:
            out = str(round(float(s[:2]) + float(s[2:]) / 60, 7))

        return out



    def list(self):
        return [self.gps.Date,
                # self.gps.Time,
                self.falcon.time,
                self.falcon.meas,
                self.falconErrorCode,
                self.falconAlarmAlert,
                self.falcon.f1,
                self.falcon.f2,

                self.gps.Lat,
                self.gps.LatDir,
                self.gps.Lon,
                self.gps.LonDir,
                self.gps.Alt,
                self.gps.AltUnit,
                self.gps.SatNum]

    def string(self):
        return self.logDelimiter.join(map(str, self.list()))

    def noFixMessage(self):
        self.serial.write("Gps has no fix, please wait..\n".encode())

    def usartNotOpenMessage(self):
        self.serial.write('Cannot open USART port..\n')
        print('Cannot open USART port..\n')

    def usbNotOpenMessage(self):
        self.serial.write('Cannot open USB port (check if sensor is connected)\n')
        print('Cannot open USB port (check if sensor is connected)\n')




