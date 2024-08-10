# file_name:Red_Detect_Exposure
import sensor, image, time
import Message
from pyb import LED

IMG_CENTER_X=160
CENTER_ROI=(140,0,40,240)
CENTER_LINE_Y = (160,0,160,240)
CENTER_LINE_X = (0,120,320,120)
first_enter_center_flag = True  # 默认红色第一次进入中心区域后马上给飞控发送标志信号
red_threshold =(10, 80, 22, 92, -7, 72) # 晚上：(6, 80, 20, 82, -26, 58)

# 该文件执行main时才相关的的参数：
EXPOSURE_TIME_SCALE = 1.0   # 曝光时间调整比例，设置曝光时间=初始曝光时间*EXPOSURE_TIME_SCALE
                            # 更改此值以调整曝光。试试10.0 / 0.1 /等
EXPOSURE_TIME = 6576    # (us)
AUTO_WHITEBAL_FLAG = False  # 必须关闭自动增益控制和自动白平衡
AUTO_GAIN_FLAG = False      # 否则他们将更改图像增益以撤消您放置的任何曝光设置

# 寻找色块列表中最大的色块，使用这个函数一定要在色块列表中有元素才行，例如必须在if blobs_list:的条件下执行
def find_largest_blob(blobs_list):
    max_blob_pixels_value=0
    for now_blob in blobs_list:
        if now_blob[4] > max_blob_pixels_value:
            largest_blob=now_blob
            max_blob_pixels_value = now_blob[4]
    return largest_blob

def red_Detect(img):
    global first_enter_center_flag
    blobs = img.find_blobs([red_threshold],area_threshold=400,merge=False)
    if blobs:
        # 框出色块，大概率能框到红色物体
        max_blob=find_largest_blob(blobs)
        img.draw_rectangle(max_blob[0:4])
        img.draw_cross(max_blob[5], max_blob[6])
        img.draw_line(CENTER_LINE_Y,color=(0,0,255))
        img.draw_line(CENTER_LINE_X,color=(0,0,255))

        # 计算红色物体中心点与图像中心点的距离
        center_distance_err = max_blob[5] - IMG_CENTER_X

        if(CENTER_ROI[0]<max_blob[5] and max_blob[5]<(CENTER_ROI[0]+CENTER_ROI[2])):
            Message.UartSendData(Message.My_Pack(0x03,0,center_distance_err))
            print("红色物体进入中心区域！距离中心点:",center_distance_err)

            # 红灯表示物体进入中心区域
            LED(1).on()
            LED(2).off()
            LED(3).off()

            #if (first_enter_center_flag == True):   # 该语句块只执行一次
                #first_enter_center_flag = False
                ## 第一次进入中心区域
                ##for i in range(3):
                    ### 进入中心区域后立刻发送三次标志信号
                    ##Message.UartSendData(Message.My_Pack(0x03,0,0))
            ## 2023年5月1日晚21：30，暂时在检测到红色时只发上面的三次即可

        else:
            Message.UartSendData(Message.My_Pack(0x03,0,center_distance_err))
            print("红色物体进入视野！但还没有进入中心区域...距离中心点:",center_distance_err)
            # 白灯表示物体进入视野，但未进入中心区域
            LED(1).on()
            LED(2).on()
            LED(3).on()
            img.draw_rectangle(CENTER_ROI,color=(255,0,0))
    else:
        # 视野中没有红色色块则关灯
        LED(1).off()
        LED(2).off()
        LED(3).off()

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
    sensor.set_auto_exposure(False,
        exposure_us=int(current_exposure_time_in_microseconds * EXPOSURE_TIME_SCALE))
    print("New exposure Time:%d us" % sensor.get_exposure_us())
    # clock = time.clock()  # 不用打印帧率的话可以不用

    while True:
        # clock.tick()      # 不用打印帧率的话可以不用
        img = sensor.snapshot()
        red_Detect(img)
