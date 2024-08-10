#******************************************** (C) 2023 MSL ******************************************#
import sensor, image, time, utime,math, struct
import json
from pyb import LED,Timer
from struct import pack, unpack
import Message,Barcode,QRandBAR,Red_Detect,Red_Detect_Exposure,Buzzer
#import Yellow_Detect
import Yellow_Detect_Exposure
#初始化镜头
#sensor.reset()
#sensor.set_pixformat(sensor.RGB565)
#sensor.set_framesize(sensor.QVGA)
#sensor.skip_frames(10)#时钟
#sensor.set_auto_whitebal(False) # 若想追踪颜色则关闭白平衡
#sensor.set_auto_gain(True)      # 环境太暗时应开启自动增益以提高视野亮度
#clock = time.clock()#初始化时钟

EXPOSURE_TIME_SCALE = 1 # 初始曝光比例
EXPOSURE_TIME_SCALE_YELLOW_1 = 1.5   # 黄色曝光比例
EXPOSURE_TIME_SCALE_RED = 1 # 红色曝光比例
work_mode_1_flag = True # 第一次进入工作模式1标志(黄色检测)
work_mode_2_flag = True
work_mode_3_flag = True # 第一次进入工作模式3标志(寻找红色)
work_mode_5_flag = True
work_mode_6_flag = True
work_mode_7_flag = True # 第一次进入工作模式7标志(红色绕杆)
work_mode_8_flag = True

AUTO_WHITEBAL_FLAG = False  # 必须关闭自动增益控制和自动白平衡
AUTO_GAIN_FLAG = False      # 否则他们将更改图像增益以撤消您放置的任何曝光设置
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)  # 等待设置生效
print("Initial Exposure Time:%d us" % sensor.get_exposure_us())  # 打印初始曝光值，用于后续比较曝光值的变化
sensor.set_auto_whitebal(AUTO_WHITEBAL_FLAG)
sensor.set_auto_gain(AUTO_GAIN_FLAG)
sensor.skip_frames(time=500)    # 需要让以上设置生效
# 记录镜头参数设置完成后的当前曝光时间，后续用于倍乘
current_exposure_time_in_microseconds = sensor.get_exposure_us()
print("Current Exposure Time:%d us" % current_exposure_time_in_microseconds)
# 设置曝光时间为int(current_exposure_time_in_microseconds * EXPOSURE_TIME_SCALE)
# 默认情况下启用自动曝光控制（AEC）。调用以下功能可禁用传感器自动曝光控制。
# 另外“exposure_us”参数在AEC被禁用后覆盖自动曝光值。
sensor.set_auto_exposure(False,
    exposure_us=int(current_exposure_time_in_microseconds * EXPOSURE_TIME_SCALE_YELLOW_1))
print("New exposure Time:%d us" % sensor.get_exposure_us())


start = utime.ticks_ms()
#主循环
while(True):
    #clock.tick()#时钟初始化
    end = utime.ticks_ms()
    img = sensor.snapshot()
    # 接收串口数据
    Message.UartReadBuffer()
    if (Message.Ctr.WorkMode==1):#if(end - start < 5000):识别顺光黄色条形码
        #print("顺光识别黄色模式！")
        if(work_mode_1_flag == True):
            work_mode_1_flag = False
            # 调整曝光值
            sensor.set_auto_exposure(False,
                exposure_us=int(current_exposure_time_in_microseconds * EXPOSURE_TIME_SCALE_YELLOW_1))
        #Yellow_Detect.yellow_Detect(img)
        Yellow_Detect_Exposure.yellow_Detect_1(img,(40, 99, -18, 22, 42, 78))
         #LED(1).on()
         #LED(2).off()
         #LED(3).off()
    elif (Message.Ctr.WorkMode==2):#elif(end - start < 15000): 条形码拍照
        #print("黄色条形码拍照模式！")
        if(work_mode_2_flag == True):
            work_mode_2_flag = False
            # 该函数关闭了控制黄灯闪烁的定时器，并且该函数执行时其内部把所有灯都关了以防止对后续标志灯的影响
            #Yellow_Detect_Exposure.alert_close()
            # 再关一次灯确保上一个模式的灯不会对此模式的标志灯光造成影响
            LED(1).off()
            LED(2).off()
            LED(3).off()
            Buzzer.Buzzer_open()    # 拍照模式下打开蜂鸣器

        QRandBAR.BarcodePhoto()
         #LED(1).off()
         #LED(2).on()
         #LED(3).off()
    elif (Message.Ctr.WorkMode==3): # 寻找红色杆子elif(end - start < 20000):
        #print("寻找红色杆子模式！")
        if(work_mode_3_flag == True):
            work_mode_3_flag = False
            sensor.set_auto_exposure(False,
                exposure_us=int(current_exposure_time_in_microseconds * EXPOSURE_TIME_SCALE_RED))
            # 把上一个模式的灯关了，防止影响二维码拍照的标志灯光
            LED(1).off()
            LED(2).off()
            LED(3).off()
            Buzzer.Buzzer_close()   # 关闭蜂鸣器

        Red_Detect.red_Detect_1(img)#该函数单独测试也要加曝光设置，但还没加？？？
         #LED(1).off()
         #LED(2).off()
         #LED(3).on()
    elif(Message.Ctr.WorkMode==5): # 二维码拍照elif(end - start < 25000):
        #print("二维码拍照模式！")
        if(work_mode_5_flag == True):
            work_mode_5_flag = False
            # 把上一个模式的灯关了，防止影响二维码拍照的标志灯光
            LED(1).off()
            LED(2).off()
            LED(3).off()

        QRandBAR.QRcodePhoto()
         #LED(1).on()
         #LED(2).on()
         #LED(3).on()
    elif(Message.Ctr.WorkMode==6):# 红色绕杆elif(end - start < 35000):
        #print("红色绕杆模式！")
        if(work_mode_6_flag == True):
            work_mode_6_flag = False
            # 把上一个模式的灯关了，防止影响二维码拍照的标志灯光
            LED(1).off()
            LED(2).off()
            LED(3).off()

        Red_Detect_Exposure.red_Detect(img)
    #elif(Message.Ctr.WorkMode==7):  # 背光识别黄色elif(end - start < 40000):
        ##print("背光识别黄色模式！")
        #if(work_mode_7_flag == True):
            #work_mode_7_flag = False
            ## 调整曝光值
            #sensor.set_auto_exposure(False,
                #exposure_us=int(current_exposure_time_in_microseconds * EXPOSURE_TIME_SCALE_YELLOW_1))
            ## 把上一个模式的灯关了，防止影响黄色识别的标志灯光
            #LED(1).off()
            #LED(2).off()
            #LED(3).off()

        #Yellow_Detect_Exposure.yellow_Detect_2(img,(25, 80, -28, 12, 24, 67))
    #elif (Message.Ctr.WorkMode==8):#elif(end - start < 45000):
        #if(work_mode_8_flag == True):
            #work_mode_8_flag = False
            ## 设置曝光值为红色适应曝光值
            #sensor.set_auto_exposure(False,
                #exposure_us=int(current_exposure_time_in_microseconds * EXPOSXURE_TIME_SCALE_RED))
            ## 再关一次灯确保上一个模式的灯不会对此模式的标志灯光造成影响
            #LED(1).off()
            #LED(2).off()
            #LED(3).off()
            #Buzzer.Buzzer_close()   # 关闭黄色识别的蜂鸣器

        #Red_Detect.red_Detect_2(img)#该函数单独测试也要加曝光设置，但还没加？？？

    else:
            LED(1).off()
            LED(2).on()
            LED(3).off()
            Buzzer.Buzzer_close()
#******************************************** (C) 2023 MSL ******************************************#
