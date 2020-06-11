import serial
import time

usart = serial.Serial(
        port='/dev/ttyS0',
        baudrate = 38400,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=2
)

if not usart.isOpen():
    print("uart not opened")

for x in range(20):
  # print(x)
  tel = "%d. ahoj, ako sa mas? ja sa mam doobre \n" % x
  print("%d. - len: %d" % (x, len(tel)))
  usart.write(tel.encode('utf-8'))
  time.sleep(0.04)

usart.close()