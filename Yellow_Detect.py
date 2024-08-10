import sensor, image, time, utime
import Message
from pyb import LED
from pyb import Timer

timer4 = Timer(4, freq=10)
K_VALUE_ADJUST_TIME = 10000 # K值调整测量时间(ms) 10000ms = 10s
K_VALUE_ADJUST_REAL_DISTANCE = 50   # K值调整测量时的实际距离(cm)
CENTER_ROI = (140, 0, 40, 240)  # 中心区域，黄色物体进入该区域就给飞控发标志位
CENTER_LINE_Y = (160, 0, 160, 240)  # 中心交叉线(纵向)
CENTER_LINE_X = (0, 120, 320, 120)  # 中心交叉线(横向)
DISTANCE_LIST_NUM = 5  # 每DISTANCE_LIST_NUM组“距离”的数据求一次平均值
ALERT_DISTANCE = 20  # 报警距离(cm)，小于该距离就黄灯闪烁报警
distance_list = []  # 用于存储计算距离平均值的距离数据
distance_average = 0  # 距离平均值
DISTANCE_RECORD_TIME = 1000 # 收集距离数据的时间为1000ms(随后将这段时间收集到的数据取平均)
first_enter_center_flag = True  # 黄色物体第一次进入中心区域标志
first_data_send_flag = True # 第一次发送距离数据标志
yellow_threshold =yellow_threshold =(20, 91, -34, 18, 21, 62)

# 用于utime计时的类
class Record_Time(object):
    start_time = 0  # 记录起始时间
    end_time = 0  # 记录结束时间
# 类的实例化
Record_time = Record_Time()

# 测距比例，KL:色块长度比例，KW:色块宽度比例
KL = 1500
KW = 850

# K值快速测试程序，给定实际距离K_VALUE_ADJUST_REAL_DISTANCE，让摄像头保持在该距离，对准测量，K_VALUE_ADJUST_TIME(ms)后测试完毕，K_VALUE_ADJUST_REAL_DISTANCE
def yellow_distance_detect_K_adjust(real_current_distance_cm, img):
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
yellow_led_glitter_mode = 0  # 默认不占有灯的控制权，即自由模式

def yellow_led_glitter_mode_set(t):  # 作为定时器的回调函数这个参数t是必要的！
    if (yellow_led_glitter_mode == 0):  # 自由模式
        pass
    elif (yellow_led_glitter_mode == 1):  # 常亮模式，黄灯常量
        LED(1).on()
        LED(2).on()
        LED(3).off()
    else:  # 闪烁模式，黄灯闪烁
        LED(1).toggle()
        LED(2).toggle()
        LED(3).off()


timer4.callback(yellow_led_glitter_mode_set)  # 中断时执行()括号中的函数


# 关闭定时器。黄色检测后应关停定时器，防止其对后续其他程序对LED灯的控制造成影响
def alert_close():
    timer4.deinit()
    LED(1).off()
    LED(2).off()
    LED(3).off()


# 黄色异物检测
def yellow_Detect(img):
    global distance_average, yellow_led_glitter_mode,first_enter_center_flag,first_data_send_flag
    blobs = img.find_blobs([yellow_threshold], area_threshold=250, merge=True)
    if blobs:
        # 框出色块，大概率能框到黄色异物
        max_blob = find_largest_blob(blobs)
        img.draw_rectangle(max_blob[0:4])
        img.draw_cross(max_blob[5], max_blob[6])
        img.draw_line(CENTER_LINE_Y, color=(0, 0, 255))
        img.draw_line(CENTER_LINE_X, color=(0, 0, 255))

        if ((CENTER_ROI[0] < max_blob[5]) and (max_blob[5] < (CENTER_ROI[0] + CENTER_ROI[2]))):
            # 色块进入中心区域
            if (first_enter_center_flag == True):   # 该语句块只执行一次
                first_enter_center_flag = False
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
                distance_L = KL / max_blob[2]
                distance_W = KW / max_blob[3]
                distance = (distance_L + distance_W) / 2
                distance_list.append(distance)
                if (len(distance_list) >= DISTANCE_LIST_NUM):
                    # 当经过DISTANCE_RECORD_TIME时间后第一次执行时list中的元素个数必然是大于DISTANCE_LIST_NUM的
                    # 这可以保证DISTANCE_LIST_NUM时间内采集到的数据可以来到这个地方求出平均值
                    # 但DISTANCE_RECORD_TIME后的非第一次执行就是每DISTANCE_LIST_NUM次求一次平均值
                    # 继续求平均值是为了服务灯闪烁程序
                    distance_average = sum(distance_list) / len(distance_list)
                    distance_average = int(distance_average)
                    distance_list.clear()
                # 若之前”没有“发送过距离数据，则执行如下程序一次
                if(first_data_send_flag == True):
                    # 将DISTANCE_LIST_NUM时间内采集到的数据平均值发送
                    first_data_send_flag = False
                    for i in range(3):
                        Message.UartSendData(Message.My_Pack(0x01, distance_average, 0))  # 将进入中心区域的标志信号发给飞控
                        print("实际发送给飞控的距离数据:", distance_average, "cm")
                    print("用时：",(utime.ticks_ms()-Record_time.start_time),"ms")

            if (distance_average <= ALERT_DISTANCE):
                # 黄色异物在ALERT_DISTANCE报警距离内则闪烁
                # print("靠近黄色物体！！！距离:", distance_average, "cm")
                yellow_led_glitter_mode = 2
            else:
                # 黄色异物不在报警距离内则不闪烁，黄灯常量
                # print("黄色物体进入中心区域！", "距离:", distance_average, "cm")
                yellow_led_glitter_mode = 1
        else:
            yellow_led_glitter_mode = 0  # 定时器中断交出灯的控制权
            # 白灯表示物体出现在视野，但未进入中心区域
            LED(1).on()
            LED(2).on()
            LED(3).on()
            # print("黄色物体进入视野！但还没有进入中心区域...")
            img.draw_rectangle(CENTER_ROI, color=(255, 255, 0))
    else:
        yellow_led_glitter_mode = 0  # 定时器中断交出灯的控制权
        # 无黄色色块在视野中被识别则关灯
        LED(1).off()
        LED(2).off()
        LED(3).off()


if __name__ == '__main__':
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.skip_frames(10)
    sensor.set_auto_whitebal(False)
    sensor.set_auto_gain(False)
    clock = time.clock()
    start_time = utime.ticks_ms()
    while (True):
        clock.tick()
        img = sensor.snapshot()
        end = utime.ticks_ms()
        #yellow_Detect(img)
        if (utime.ticks_ms() - start_time <= K_VALUE_ADJUST_TIME):    # 测量
            yellow_distance_detect_K_adjust(K_VALUE_ADJUST_REAL_DISTANCE, img)
