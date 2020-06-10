
import serial
import pynmea2
import re
from datetime import timezone, timedelta, datetime, time, date

def convertGps(input):
	s = str(input).strip("0")
	splits = s.split(".")
	if len(splits[0]) == 0:
		out = str(round(float(s)/ 60, 7))
	elif len(splits[0]) == 1:
		out = str(round(float(s[:1]) + float(s[1:])/60, 7))
	elif len(splits[0]) > 1:
		out = str(round(float(s[:2]) + float(s[2:]) / 60, 7))
	return out


class Gnss(object):
    def __init__(self, usart):
        self.serial = usart

        self.data = GnssData()
        self.configDeltaTime = None

        self.falconDate = None
        self.falconTime = None

    def hasFix(self):
        if self.data.QualityFix and int(self.data.QualityFix) >= 1:
            return True
        else:
            return False


    def update(self):
        return self.parse()


    def parse(self):
        if self.serial.inWaiting() > 20:
            data = self.serial.readline()
            # print(data)
            # print(data.isalnum())
            if data[1] == 71:
                # print("decode")
                input = data.decode()

                # rychlostna optimalizacia
                # if input.find("GGA", beg=0, end=len(string)/2) > 0:
                if input.find("GGA", 0, 10) > 0:
                    msg = pynmea2.parse(input)

                    self.data.QualityFix = msg.gps_qual

                    if msg.gps_qual and int(msg.gps_qual) >= 1:
                        # print(msg.timestamp)
                        # self.data.Time = msg.timestamp.strftime('%H:%M:%S.%f')[:-3]

                        # convert to config time zone
                        hour = int(msg.timestamp.strftime('%H')) + self.configDeltaTime
                        if hour >= 24:
                            hour -= 24
                        elif hour < 0:
                            hour = 24 + hour

                        self.data.Time = str(hour).zfill(2) + msg.timestamp.strftime(':%M:%S.%f')[:-3]
                        self.falconTime = str(hour).zfill(2) +  msg.timestamp.strftime('%M%S')

                        self.data.Lat = convertGps(str(msg.lat))
                        self.data.LatDir = msg.lat_dir
                        self.data.Lon = convertGps(str(msg.lon))
                        self.data.LonDir = msg.lon_dir
                        self.data.Alt = msg.altitude
                        self.data.AltUnit = msg.altitude_units
                        self.data.SatNum = msg.num_sats

                        return True
                    else:
                        print("No fix")
                        return False

                elif input.find('RMC') > 0:
                    #read date only once
                    if not self.data.Date and self.hasFix():
                        line = input.split(",")
                        date = line[9]
                        if len(date) >= 5:
                            self.data.Date = date[0] + date[1] + '.' + date[2] + date[3] + '.' + date[4] + date[5]
                            self.falconDate = str("20")+ date[4] + date[5] + date[2] + date[3] + date[0] + date[1]

        return False


    def hasDateAndTime(self):
        # print("has date")
        if self.data.Date and self.data.Time:
            return True

        return False

class GnssData(object):
    def __init__(self):

        self.Time = str()

        self.Date = str()

        self.Lat = str()
        self.LatDir = str()
        self.Lon = str()
        self.LonDir = str()
        self.Alt = str()
        self.AltUnit = str()
        self.SatNum = str()

        self.QualityFix = str()
