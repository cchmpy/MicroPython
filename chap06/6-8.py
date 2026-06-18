import vfs,sys,gc
from machine import SDCard
from micropython import const
_FAT      = const(1)
_FAT32    = const(2)
_UNKNOWN  = const(3)
_EMPTY    = const(0)
def check_bootsec(sd):                                    # 检查存储卡，返回文件格式或状态
    buf = bytearray(sd.ioctl(5, 0))                       # 使用块大小定义读取缓冲
    sd.readblocks(0, buf)                                 # 读取首个块数据
    fsf = _EMPTY                                          # fsf为文件系统格式或状态 
    if buf.find(b'FAT')==54:     fsf = _FAT               # 检测格式头，当前分区为fat格式
    elif buf.find(b'FAT32')==82: fsf = _FAT32             # 检测格式头，当前分区为fat32格式
    else:                                                 # 检测块设备内是否有数据
        for b in buf:
            if b != 0xFF:
                fsf = _UNKNOWN                            # 当前分区有数据，但无法判定格式
                break
    return fsf                                            # 返回块设备的文件格式或状态
def mount_sd(sd, mount_point='/sd',read_only=False):      # 挂载存储卡
    try:
        vfs.mount(sd,'/sd',readonly=read_only)            # 挂载
    except OSError as err:
        if err.errno == 19:                                             # ENODEV,需要格式化
            fsf = check_bootsec(sd)
            if fsf == _UNKNOWN:                                         # 块设备内有数据，需要与用户交互
                ans = input('Data exists in the SD/microSD. Confirm format? Enter Y or N:')
                if ans in 'Nn':                                         # 若输入N或n，不选择格式化
                    print('Stop formatting and mounting.')
                    sys.exit(0)                                         # 保留数据，退出程序 
            print('Formatting partition, all data will be erased...')   # 用户确认格式化
            vfs.VfsFat.mkfs(sd)                                         # 格式化
            vfs.mount(sd,'/sd',readonly=read_only) 
        else: raise                                                     # 其它错误，再次抛出
    finally:
        gc.collect()                        # 垃圾回收

if __name__ == '__main__':
    sd = SDCard(slot=3)                     # 使用默认引脚sck=14, mosi=15, miso=2,cs=13
    mount_sd(sd)
