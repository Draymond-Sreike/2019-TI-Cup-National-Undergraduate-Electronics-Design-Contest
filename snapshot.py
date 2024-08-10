import sensor, image, pyb, utime

SNAPSHOT_SURPLUS_TIME = 8  # 拍摄倒数时间
IMAGE_NUM = 10  # 待拍摄照片的数量
AUTO_WHITEBAL_FLAG = False  # 白平衡，默认关闭
AUTO_GAIN_FLAG = True  # 自动增益，环境过暗时应开启

# 时间记录类
class Time_Record:
    start_time = 0  # 程序指定处开始时间(ms)
    current_time_second = 0  # 程序当前时间(s)
    snapshot_surplus_time = SNAPSHOT_SURPLUS_TIME  # 拍照剩余准备时间(s),默认SNAPSHOT_SURPLUS_TIME秒
time_record = Time_Record()

if __name__ == "__main__":
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.set_auto_whitebal(AUTO_WHITEBAL_FLAG)  # 若想追踪颜色则关闭白平衡
    sensor.set_auto_gain(AUTO_GAIN_FLAG)  # 视野太暗可以开启自动增益
    sensor.skip_frames(10)

    time_record.start_time = utime.ticks_ms()  # 获取程序开始时间
    n = 1  # 当前拍摄照片的次序
    while True:
        img = sensor.snapshot()
        if (((utime.ticks_ms() - time_record.start_time) // 1000) == 1):  # 每秒执行一次
            # time_record.current_time_second += 1       # 程序当前时间+1s
            time_record.start_time = utime.ticks_ms()  # 更新程序起始时间，便于计时下一秒
            print("剩余拍照准备时间：",time_record.snapshot_surplus_time,"s")
            time_record.snapshot_surplus_time -= 1     # 拍照剩余时间-1s

            if (time_record.snapshot_surplus_time > 3):
                # 拍照剩余时间大于3s，亮绿灯
                pyb.LED(1).off()
                pyb.LED(2).on()
                pyb.LED(3).off()
            elif ((time_record.snapshot_surplus_time <= 3)
                  and time_record.snapshot_surplus_time >= 0):
                # 拍照剩余时间小于3s，亮黄灯
                pyb.LED(1).on()
                pyb.LED(2).on()
                pyb.LED(3).off()
            else:
                # 剩余拍照时间为负数等错误情况红灯常亮
                pyb.LED(1).on()
                pyb.LED(2).off()
                pyb.LED(3).off()

        if (time_record.snapshot_surplus_time == 0 and n <= IMAGE_NUM):
            # 剩余拍照时间为0，且当前拍摄照片数量未达预定值时执行拍照
            time_record.snapshot_surplus_time = SNAPSHOT_SURPLUS_TIME   # 更新下一次拍照的剩余时间
            # 亮红灯说明该拍照功能正在执行，变绿灯说明该功能执行完毕(这个功能执行完将会亮绿灯)
            pyb.LED(1).on()
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
                pyb.LED(1).on()
                pyb.LED(2).on()
                pyb.LED(3).on()
                while True:
                    # 程序到此死循环处说明拍摄完成，但继续刷新帧缓冲区图像
                    sensor.snapshot()