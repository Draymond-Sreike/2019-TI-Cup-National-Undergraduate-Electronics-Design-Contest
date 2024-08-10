# 此示例显示如何手动控制相机传感器的曝光，而不是让自动曝光控制运行。
# 增益和曝光控制之间有什么区别？
#
# 通过增加图像的曝光时间，您可以在相机上获得更多光线。这为您提供了最佳的信噪比。
# 您通常总是希望增加曝光时间...除非，当您增加曝光时间时，您会降低最大可能的帧速率，
# 如果图像中有任何移动，它将在更长的曝光时间内开始模糊。
# 增益控制允许您使用模拟和数字乘法器增加每像素的输出......但是，它也会放大噪声。
# 因此，最好尽可能让曝光增加，然后使用增益控制来弥补任何剩余的地画面。

# 我们可以通过在自动增益控制算法上设置增益上限来实现上述目的。
# 一旦设置完毕，算法将不得不增加曝光时间以满足任何增益需求，而不是使用增益。
# 然而，当照明变化相对于曝光恒定且增益变化时，这是以曝光时间的变化为代价的。

import sensor, image, time, utime, pyb

SNAPSHOT_SURPLUS_TIME = 5   # 拍摄倒数时间
IMAGE_NUM = 60              # 待拍摄照片的数量
AUTO_WHITEBAL_FLAG = False  # 必须关闭自动增益控制和自动白平衡
AUTO_GAIN_FLAG = False      # 否则他们将更改图像增益以撤消您放置的任何曝光设置
EXPOSURE_TIME_SCALE = 1.5  # 曝光时间调整比例，设置曝光时间=初始曝光时间*EXPOSURE_TIME_SCALE
                            # 更改此值以调整曝光。试试10.0 / 0.1 /等
n = 0  # n用于记录当前拍摄照片的次序，默认序号1起始

# 时间记录类
class Time_Record:
    start_time = 0              # 程序指定处开始时间(ms)
    current_time_second = 0     # 程序当前时间(s)
    snapshot_surplus_time = SNAPSHOT_SURPLUS_TIME  # 拍照剩余准备时间(s),默认SNAPSHOT_SURPLUS_TIME秒
time_record = Time_Record()

if __name__ == "__main__":
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.skip_frames(time=2000)  # 等待设置生效。
    print("Initial Exposure Time:%d us" % sensor.get_exposure_us())  # 打印初始曝光值，用于后续比较曝光值的变化
    # sensor.get_exposure_us()以微秒为单位返回精确的相机传感器曝光时间。
    # 然而，这可能与命令的数量不同，因为传感器代码将曝光时间以微秒转换为行/像素/时钟时间，这与微秒不完全匹配...
    # clock = time.clock()  # 创建一个时钟对象来跟踪FPS帧率，若不需要跟踪显示FPS的话也可以不用
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
        # int(current_exposure_time_in_microseconds * EXPOSURE_TIME_SCALE)
    print("New exposure Time:%d us" % sensor.get_exposure_us())
    # 如果要重新打开自动曝光，请执行以下操作：sensor.set_auto_exposure(True)
    # 请注意，相机传感器将根据需要更改曝光时间。
    # 执行：sensor.set_auto_exposure(False)，只是禁用曝光值更新，但不会更改相机传感器确定的曝光值。

    time_record.start_time = utime.ticks_ms()  # 获取程序开始时间
    while True:
        # clock.tick()  # 更新FPS帧率时钟，不实时显示FPS的话可以不用
        # print(clock.fps())
        # 注意: 当连接电脑后，OpenMV会变成一半的速度。当不连接电脑，帧率会增加。
        img = sensor.snapshot()
        if (((utime.ticks_ms() - time_record.start_time) // 1000) == 1):  # 每秒执行一次
            # time_record.current_time_second += 1       # 程序当前时间+1s，这里暂时用不上
            time_record.start_time = utime.ticks_ms()  # 更新程序起始时间，便于计时下一秒
            print("剩余拍照准备时间：",time_record.snapshot_surplus_time,"s")
            time_record.snapshot_surplus_time -= 1     # 拍照剩余时间-1s

            if (time_record.snapshot_surplus_time > 3):
                # 拍照剩余时间大于3s，亮绿灯
                pyb.LED(1).off()
                #pyb.LED(2).on()
                pyb.LED(3).off()
            elif ((time_record.snapshot_surplus_time <= 3)
                  and time_record.snapshot_surplus_time >= 0):
                # 拍照剩余时间小于3s，亮黄灯
                #pyb.LED(1).on()
                #pyb.LED(2).on()
                pyb.LED(3).off()
            else:
                # 剩余拍照时间为负数等错误情况红灯常亮
                #pyb.LED(1).on()
                pyb.LED(2).off()
                pyb.LED(3).off()

        if (time_record.snapshot_surplus_time == 0 and n <= IMAGE_NUM):
            # 剩余拍照时间为0，且当前拍摄照片数量未达预定值时执行拍照
            time_record.snapshot_surplus_time = SNAPSHOT_SURPLUS_TIME   # 更新下一次拍照的剩余时间
            # 亮红灯说明该拍照功能正在执行，变绿灯说明该功能执行完毕(这个功能执行完将会亮绿灯)
            #pyb.LED(1).on()
            pyb.LED(2).off()
            pyb.LED(3).off()
            print("正在拍照...")
            sensor.snapshot().save("image/%s.jpeg" % (n))   # 保存图片到image文件夹，并以序号来命名
            print("第%s张图拍摄完成！" % (n))
            n += 1  # 更新照片序号
            if (n > IMAGE_NUM):
                # 已拍摄照片数量大于预定值时拍摄完成
                print("所有图片拍摄完成！")
                # 亮白灯提示拍摄完成
                #pyb.LED(1).on()
                #pyb.LED(2).on()
                #pyb.LED(3).on()
                while True:
                    # 程序到此死循环处说明拍摄完成，但继续刷新帧缓冲区图像
                    sensor.snapshot()
