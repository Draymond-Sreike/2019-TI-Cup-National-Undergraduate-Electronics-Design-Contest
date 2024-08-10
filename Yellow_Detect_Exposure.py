file_name: Yellow_Detect_Exposure
import sensor, image, time, utime
import Message,Buzzer
from pyb import LED
from pyb import Timer

K_VALUE_ADJUST_TIME = 10000 # K值调整测量时间(ms) 10000ms = 10s
K_VALUE_ADJUST_REAL_DISTANCE = 45   # K值调整测量时的实际距离(cm)
CENTER_ROI = (60, 0, 80, 240)  # 中心区域，黄色物体进入该区域就给飞控发标志位
CENTER_LINE_Y = (160, 0, 160, 240)  # 中心交叉线(纵向)
CENTER_LINE_X = (0, 120, 320, 120)  # 中心交叉线(横向)
DISTANCE_LIST_NUM = 5  # 每DISTANCE_LIST_NUM组“距离”的数据求一次平均值
ALERT_DISTANCE = 20  # 报警距离(cm)，小于该距离就黄灯闪烁报警
EXPOSURE_TIME_SCALE = 1.5   # 曝光时间调整比例，设置曝光时间=初始曝光时间*EXPOSURE_TIME_SCALE
                            # 更改此值以调整曝光。试试10.0 / 0.1 /等
AUTO_WHITEBAL_FLAG = False  # 必须关闭自动增益控制和自动白平衡
AUTO_GAIN_FLAG = False      # 否则他们将更改图像增益以撤消您放置的任何曝光设置
distance_list = []  # 用于存储计算距离平均值的距离数据
distance_average = 0  # 距离平均值
DISTANCE_RECORD_TIME = 1000 # 收集距离数据的时间为1000ms(随后将这段时间收集到的数据取平均)
first_enter_center_flag_1 = True  # 黄色物体第一次进入中心区域标志(1表示正面黄色识别)
first_data_send_flag_1 = True # 第一次发送距离数据标志(2表示背面黄色识别)
first_enter_center_flag_2 = True  # 黄色物体第一次进入中心区域标志(1表示正面黄色识别)
first_data_send_flag_2 = True # 第一次发送距离数据标志(2表示背面黄色识别)

#yellow_threshold =(24, 90, -26, 2, 28, 70)

# 用于utime计时的类
class Record_Time(object):
    start_time = 0  # 记录起始时间
    end_time = 0  # 记录结束时间
# 类的实例化
Record_time = Record_Time()

# 测距比例，KL:色块长度比例，KW:色块宽度比例
KL = 2700
KW = 1125

# K值快速测试程序，给定实际距离K_VALUE_ADJUST_REAL_DISTANCE，让摄像头保持在该距离，对准测量，K_VALUE_ADJUST_TIME(ms)后测试完毕，K_VALUE_ADJUST_REAL_DISTANCE
def yellow_distance_detect_K_adjust(yellow_threshold, real_current_distance_cm, img):
    blobs = img.find_blobs([yellow_threshold], area_threshold=275, merge=True)
    if blobs:
        # 框出色块，大概率能框到黄色异物
        max_blob = find_largest_blob(blobs)
        img.draw_rectangle(max_blob[0:4])
        img.draw_cross(max_blob[5], max_blob[6])
        img.draw_line(CENTER_LINE_Y, color=(0, 0, 255))
        img.draw_line(CENTER_LINE_X, color=(0, 0, 255))
        # 测量K值，K = 像素 * 实际距离
        KL_value = max_blob[2] * real_current_distance_cm
        KW_value = max_blob[3] * real_current_distance_cm
        print("长:", max_blob[2], "宽:", max_blob[3], "KL:", KL_value, "KW:", KW_value)

# 寻找色块列表中最大的色块，使用这个函数一定要在色块列表中有元素才行，例如必须在if blobs_list:的条件下执行
def find_largest_blob(blobs_list):
    max_blob_pixels_value = 0
    for now_blob in blobs_list:
        if now_blob[4] > max_blob_pixels_value:
            largest_blob = now_blob
            max_blob_pixels_value = now_blob[4]
    return largest_blob


# 灯闪烁中断程序
#timer4 = Timer(4, freq=10)
yellow_led_glitter_mode = 0  # 默认不占有灯的控制权，即自由模式
#def yellow_led_glitter_mode_set(t):  # 作为定时器的回调函数这个参数t是必要的！
    #if (yellow_led_glitter_mode == 0):  # 自由模式
        #pass
    #elif (yellow_led_glitter_mode == 1):  # 常亮模式，黄灯常量
        #LED(1).on()
        #LED(2).on()
        #LED(3).off()
    #else:  # 闪烁模式，黄灯闪烁
        #LED(1).toggle()
        #LED(2).toggle()
        #LED(3).off()
#timer4.callback(yellow_led_glitter_mode_set)  # 中断时执行()括号中的函数
# 关闭定时器。黄色检测后应关停定时器，防止其对后续其他程序对LED灯的控制造成影响
#def alert_close():
    #timer4.deinit()
    #LED(1).off()
    #LED(2).off()
    #LED(3).off()
# 背面检测黄色时需要再次开启黄色检测灯光控制，需要再打开一次该定时器
#def alert_open():
    #timer4.init(freq=10)
Record_time.start_time = 0
Record_time.end_time = 0 # 获取当前时刻，用于计算从进入中心区域开始到当前时刻所经历时间(ms)
have_enter_center_roi_flag = False

# 正面黄色异物检测（测距只测1s版）
def yellow_Detect_1(img,yellow_threshold):
    global distance_average, yellow_led_glitter_mode,first_enter_center_flag_1,first_data_send_flag_1, have_enter_center_roi_flag
    blobs = img.find_blobs([yellow_threshold], area_threshold=250, merge=False)

    if have_enter_center_roi_flag == True:
        Record_time.end_time = utime.ticks_ms() # 获取当前时刻，用于计算从进入中心区域开始到当前时刻所经历时间(ms)

    if (Record_time.end_time - Record_time.start_time) > DISTANCE_RECORD_TIME:
        # 进入中心区域并经过DISTANCE_RECORD_TIME时间之后执行该else
        # 若之前”没有“发送过距离数据，则执行如下程序一次
        if(first_data_send_flag_1 == True):
            first_data_send_flag_1 = False
            # 将DISTANCE_LIST_NUM时间内采集到的数据平均值发送
            distance_average = sum(distance_list) / len(distance_list)
            distance_average = int(distance_average)
            distance_list.clear()
            # 发送数据
            for i in range(3):
                Message.UartSendData(Message.My_Pack(0x01, distance_average, 0))  # 将进入中心区域的标志信号发给飞控
                print("实际发送给飞控的距离数据:", distance_average, "cm")
            print("用时：",(utime.ticks_ms()-Record_time.start_time),"ms")


    if blobs:
        # 框出色块，大概率能框到黄色异物
        max_blob = find_largest_blob(blobs)
        img.draw_rectangle(max_blob[0:4])
        img.draw_cross(max_blob[5], max_blob[6])
        img.draw_line(CENTER_LINE_Y, color=(0, 0, 255))
        img.draw_line(CENTER_LINE_X, color=(0, 0, 255))

        if (CENTER_ROI[0] < max_blob[5]) and (max_blob[5] < (CENTER_ROI[0] + CENTER_ROI[2])):
            # 色块进入中心区域，亮黄灯，蜂鸣器工作
            LED(1).on()
            LED(2).on()
            LED(3).off()
            Buzzer.Buzzer_open()
            if (first_enter_center_flag_1 == True):   # 该语句块只执行一次
                first_enter_center_flag_1 = False
                # 第一次进入中心区域
                have_enter_center_roi_flag = True
                for i in range(3):
                    # 进入中心区域后立刻发送三次标志信号
                    Message.UartSendData(Message.My_Pack(0x01, 0, 0))
                Record_time.start_time = utime.ticks_ms()   # 记录发送信号的起始时间

            Record_time.end_time = utime.ticks_ms() # 获取当前时刻，用于计算从进入中心区域开始到当前时刻所经历时间(ms)
            if((Record_time.end_time - Record_time.start_time) <= DISTANCE_RECORD_TIME):
                # 从进入中心区域开始，采集DISTANCE_RECORD_TIME(ms)时间的距离数据
                distance_L = KL / max_blob[2]
                distance_W = KW / max_blob[3]
                distance = (distance_L + distance_W) / 2
                distance_list.append(distance)
            else:
                # 进入中心区域并经过DISTANCE_RECORD_TIME时间之后执行该else
                # 若之前”没有“发送过距离数据，则执行如下程序一次
                if(first_data_send_flag_1 == True):
                    first_data_send_flag_1 = False
                    # 将DISTANCE_LIST_NUM时间内采集到的数据平均值发送
                    distance_average = sum(distance_list) / len(distance_list)
                    distance_average = int(distance_average)
                    distance_list.clear()
                    # 发送数据
                    for i in range(3):
                        Message.UartSendData(Message.My_Pack(0x01, distance_average, 0))  # 将进入中心区域的标志信号发给飞控
                        print("实际发送给飞控的距离数据:", distance_average, "cm")
                    print("用时：",(utime.ticks_ms()-Record_time.start_time),"ms")
        else:
            # 白灯表示物体出现在视野，但未进入中心区域，此时蜂鸣器不工作
            LED(1).on()
            LED(2).on()
            LED(3).on()
            Buzzer.Buzzer_close()
            # print("黄色物体进入视野！但还没有进入中心区域...")
            img.draw_rectangle(CENTER_ROI, color=(255, 255, 0))
    else:
        yellow_led_glitter_mode = 0  # 定时器中断交出灯的控制权
        # 无黄色色块在视野中被识别则关灯，蜂鸣器不工作
        LED(1).off()
        LED(2).off()
        LED(3).off()
        Buzzer.Buzzer_close()

# 黄色异物检测（测距持续版）
#def yellow_Detect_1(img,yellow_threshold):
    #global distance_average, yellow_led_glitter_mode,first_enter_center_flag,first_data_send_flag
    #blobs = img.find_blobs([yellow_threshold], area_threshold=250, merge=False)
    #if blobs:
        ## 框出色块，大概率能框到黄色异物
        #max_blob = find_largest_blob(blobs)
        #img.draw_rectangle(max_blob[0:4])
        #img.draw_cross(max_blob[5], max_blob[6])
        #img.draw_line(CENTER_LINE_Y, color=(0, 0, 255))
        #img.draw_line(CENTER_LINE_X, color=(0, 0, 255))

        #if ((CENTER_ROI[0] < max_blob[5]) and (max_blob[5] < (CENTER_ROI[0] + CENTER_ROI[2]))):
            ## 色块进入中心区域，亮黄灯，蜂鸣器工作
            #LED(1).on()
            #LED(2).on()
            #LED(3).off()
            #Buzzer.Buzzer_open()
            #if (first_enter_center_flag == True):   # 该语句块只执行一次
                #first_enter_center_flag = False
                ## 第一次进入中心区域
                #for i in range(3):
                    ## 进入中心区域后立刻发送三次标志信号
                    #Message.UartSendData(Message.My_Pack(0x01, 0, 0))
                #Record_time.start_time = utime.ticks_ms()   # 记录发送信号的起始时间

            #Record_time.end_time = utime.ticks_ms() # 获取当前时刻，用于计算从进入中心区域开始到当前时刻所经历时间(ms)
            #if((Record_time.end_time - Record_time.start_time) <= DISTANCE_RECORD_TIME):
                ## 从进入中心区域开始，采集DISTANCE_RECORD_TIME(ms)时间的距离数据
                #distance_L = KL / max_blob[2]
                #distance_W = KW / max_blob[3]
                #distance = (distance_L + distance_W) / 2
                #distance_list.append(distance)
            #else:
                ## 进入中心区域并经过DISTANCE_RECORD_TIME时间之后执行该else
                #distance_L = KL / max_blob[2]
                #distance_W = KW / max_blob[3]
                #distance = (distance_L + distance_W) / 2
                #distance_list.append(distance)
                #if (len(distance_list) >= DISTANCE_LIST_NUM):
                    ## 当经过DISTANCE_RECORD_TIME时间后第一次执行时list中的元素个数必然是大于DISTANCE_LIST_NUM的
                    ## 这可以保证DISTANCE_LIST_NUM时间内采集到的数据可以来到这个地方求出平均值
                    ## 但DISTANCE_RECORD_TIME后的非第一次执行就是每DISTANCE_LIST_NUM次求一次平均值
                    ## 继续求平均值是为了服务灯闪烁程序
                    #distance_average = sum(distance_list) / len(distance_list)
                    #distance_average = int(distance_average)
                    #distance_list.clear()
                ## 若之前”没有“发送过距离数据，则执行如下程序一次
                #if(first_data_send_flag == True):
                    ## 将DISTANCE_LIST_NUM时间内采集到的数据平均值发送
                    #first_data_send_flag = False
                    #for i in range(3):
                        #Message.UartSendData(Message.My_Pack(0x01, distance_average, 0))  # 将进入中心区域的标志信号发给飞控
                        #print("实际发送给飞控的距离数据:", distance_average, "cm")
                    #print("用时：",(utime.ticks_ms()-Record_time.start_time),"ms")

            #if (distance_average <= ALERT_DISTANCE):
                ## 黄色异物在ALERT_DISTANCE报警距离内则闪烁
                ## print("靠近黄色物体！！！距离:", distance_average, "cm")
                #yellow_led_glitter_mode = 2
            #else:
                ## 黄色异物不在报警距离内则不闪烁，黄灯常量
                ## print("黄色物体进入中心区域！", "距离:", distance_average, "cm")
                #yellow_led_glitter_mode = 1
        #else:
            #yellow_led_glitter_mode = 0  # 定时器中断交出灯的控制权
            ## 白灯表示物体出现在视野，但未进入中心区域，此时蜂鸣器不工作
            #LED(1).on()
            #LED(2).on()
            #LED(3).on()
            #Buzzer.Buzzer_close()
            ## print("黄色物体进入视野！但还没有进入中心区域...")
            #img.draw_rectangle(CENTER_ROI, color=(255, 255, 0))
    #else:
        #yellow_led_glitter_mode = 0  # 定时器中断交出灯的控制权
        ## 无黄色色块在视野中被识别则关灯，蜂鸣器不工作
        #LED(1).off()
        #LED(2).off()
        #LED(3).off()
        #Buzzer.Buzzer_close()

# 背面黄色异物检测（测距只测1s版）
def yellow_Detect_2(img,yellow_threshold):
    global distance_average, yellow_led_glitter_mode,first_enter_center_flag_2,first_data_send_flag_2
    blobs = img.find_blobs([yellow_threshold], area_threshold=250, merge=False)
    if blobs:
        # 框出色块，大概率能框到黄色异物
        max_blob = find_largest_blob(blobs)
        img.draw_rectangle(max_blob[0:4])
        img.draw_cross(max_blob[5], max_blob[6])
        img.draw_line(CENTER_LINE_Y, color=(0, 0, 255))
        img.draw_line(CENTER_LINE_X, color=(0, 0, 255))

        if (CENTER_ROI[0] < max_blob[5]) and (max_blob[5] < (CENTER_ROI[0] + CENTER_ROI[2])):
            # 色块进入中心区域，亮黄灯，蜂鸣器工作
            LED(1).on()
            LED(2).on()
            LED(3).off()
            Buzzer.Buzzer_open()
            if (first_enter_center_flag_2 == True):   # 该语句块只执行一次
                first_enter_center_flag_2 = False
                # 第一次进入中心区域
                for i in range(3):
                    # 进入中心区域后立刻发送三次标志信号
                    Message.UartSendData(Message.My_Pack(0x01, 0, 0))
                Record_time.start_time = utime.ticks_ms()   # 记录发送信号的起始时间

            Record_time.end_time = utime.ticks_ms() # 获取当前时刻，用于计算从进入中心区域开始到当前时刻所经历时间(ms)
            if((Record_time.end_time - Record_time.start_time) <= DISTANCE_RECORD_TIME):
                # 从进入中心区域开始，采集DISTANCE_RECORD_TIME(ms)时间的距离数据
                distance_L = KL / max_blob[2]
                distance_W = KW / max_blob[3]
                distance = (distance_L + distance_W) / 2
                distance_list.append(distance)
            else:
                # 进入中心区域并经过DISTANCE_RECORD_TIME时间之后执行该else
                # 若之前”没有“发送过距离数据，则执行如下程序一次
                if(first_data_send_flag_2 == True):
                    first_data_send_flag_2 = False
                    # 将DISTANCE_LIST_NUM时间内采集到的数据平均值发送
                    distance_average = sum(distance_list) / len(distance_list)
                    distance_average = int(distance_average)
                    distance_list.clear()
                    # 发送数据
                    for i in range(3):
                        Message.UartSendData(Message.My_Pack(0x01, distance_average, 0))  # 将进入中心区域的标志信号发给飞控
                        print("实际发送给飞控的距离数据:", distance_average, "cm")
                    print("用时：",(utime.ticks_ms()-Record_time.start_time),"ms")
        else:
            # 白灯表示物体出现在视野，但未进入中心区域，此时蜂鸣器不工作
            LED(1).on()
            LED(2).on()
            LED(3).on()
            Buzzer.Buzzer_close()
            # print("黄色物体进入视野！但还没有进入中心区域...")
            img.draw_rectangle(CENTER_ROI, color=(255, 255, 0))
    else:
        # 无黄色色块在视野中被识别则关灯，蜂鸣器不工作
        LED(1).off()
        LED(2).off()
        LED(3).off()
        Buzzer.Buzzer_close()


if __name__ == '__main__':
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
    #sensor.set_auto_exposure(False,
        #exposure_us=int(current_exposure_time_in_microseconds * EXPOSURE_TIME_SCALE))  # 设10100就会变为10067
    print("New exposure Time:%d us" % sensor.get_exposure_us())
    # clock = time.clock()  # 不用打印帧率的话可以不用

    start_time = utime.ticks_ms()
    while True:
        # clock.tick()
        img = sensor.snapshot()
        end = utime.ticks_ms()
        #yellow_Detect_1(img,(24, 90, -26, 2, 28, 70)) # 顺光曝光值：9864us
        #yellow_Detect_2(img,(57, 99, -8, 9, 15, 36)) # 逆光曝光值：9864us
         #if (utime.ticks_ms() - start_time <= K_VALUE_ADJUST_TIME):    # 测量距离参数K
        yellow_distance_detect_K_adjust((30, 90, -8, 22, 18, 71),K_VALUE_ADJUST_REAL_DISTANCE, img)
