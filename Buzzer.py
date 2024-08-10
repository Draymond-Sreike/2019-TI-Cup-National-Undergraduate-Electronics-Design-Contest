import sensor, image, time
from pyb import Pin

buzzer_pin = Pin('P7', Pin.OUT_PP)#设置p_out为输出引脚
buzzer_vcc = Pin('P8', Pin.OUT_PP)#设置p_out为输出引脚
buzzer_pin.high()   # 上电默认蜂鸣器不工作
buzzer_vcc.high()   # 蜂鸣器供电脚

def Buzzer_open():
    buzzer_pin.low()

def Buzzer_close():
    buzzer_pin.high()

if __name__ == "__main__":
    while(True):

        #img = sensor.snapshot()         # Take a picture and return the image.
        #print(clock.fps())              # Note: OpenMV Cam runs about half as fast when connected
                                        # to the IDE. The FPS should increase once disconnected.
        #p_out.high()#设置p_out引脚为高
        buzzer_pin.low()#设置p_out引脚为低
