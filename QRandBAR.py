import sensor, image, time, math, struct, pyb
import json
from pyb import LED,Timer
from struct import pack, unpack
import Message,QRcode,Photography,Barcode

times1=0
times2=0

#检测到条形码拍照
def BarcodePhoto():
    global times1
    if times1 == 0:
        times1 = 1
        i = 3
        pyb.delay(100)
        Photography.Photography('BAR1.jpg',100)
        #pyb.delay(100)
        ##Photography.Photography('BAR2.jpg',100)
        #pyb.delay(100)
        #Photography.Photography('BAR3.jpg',100)
        while i>0:
            i = i - 1
            Message.UartSendData(Message.My_Pack(2,0,0))
    else:
        pass
         #print('QwQ no BarCode QwQ')
#检测到条形码则连续拍三张照片，能扫码的边界距离为13.5cm

#检测到二维码拍照
def QRcodePhoto():
    global times2
    if  times2 == 0:
       times2 = 1
       j = 3
       pyb.delay(100)
       Photography.Photography('QR1.jpg',100)
       #pyb.delay(100)
       #Photography.Photography('QR2.jpg',100)
       #pyb.delay(100)
       #Photography.Photography('QR3.jpg',100)
       while j>0:
            j = j - 1
            Message.UartSendData(Message.My_Pack(4,0,0))
    else:
        pass
         #print('QwQno QRcode QwQ')
#检测到有二维码出现，拍照三张 ,能扫码的极限距离为16cm
