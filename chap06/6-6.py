import vfs,sys
from esp32 import Partition
from micropython import const
# 定义表示文件系统格式和状态的常量
_FAT      = const(1)
_LITTLEFS = const(2)
_UNKNOWN  = const(3)
_EMPTY    = const(0)                                          # 分区内数据为空

def mount_partition(name, mount_point, fs=vfs.VfsLfs2, read_only=False): 
    def check_bootsec(p):                                     # 嵌套函数，检查块设备，返回文件格式或状态
        buf = bytearray(p.ioctl(5, 0))                        # 使用块大小定义读取缓冲
        p.readblocks(0, buf)                                  # 读取首个块数据
        fsf = _EMPTY                                          # fsf为文件系统格式或状态 
        if buf.find(b'littlefs')==8: fsf = _LITTLEFS          # 检测格式头，当前分区为Littlefs格式
        elif buf.find(b'FAT')==54:   fsf = _FAT               # 检测格式头，当前分区为fat格式
        else:                                                 # 检测块设备内是否有数据
            for b in buf:
                if b != 0xFF:
                    fsf = _UNKNOWN                            # 当前分区有数据，但无法判定格式
                    break
        return fsf                                            # 返回块设备的文件格式或状态
    
    def mount_(p):                                            # 嵌套函数，挂载并打印提示信息
        nonlocal mount_point, read_only
        vfs.mount(p, mount_point,readonly=read_only)
        print(f'"{p.info()[4]}" has been mounted to "{mount_point}"') 
    
    # --------------------查找数据分区，获得块设备----------------
    try:
        p = Partition.find(Partition.TYPE_DATA, label=name)[0] 
    except IndexError:
        print(f'Partition("{name}") not found!')
        sys.exit(0)                                            # 退出程序
    
    # --------------------挂载分区-------------------------------
    fsn = fs.__name__                                          # 将建立的目标文件系统的名称
    fsf = check_bootsec(p)                                     # 获得块设备的文件系统格式或状态
    fmt  = True                                                # 假设需要格式化 
    if (fsf == _LITTLEFS and fsn == "VfsLfs2") or (fsf == _FAT and fsn == "VfsFat"):
        fmt = False                                            # 已有文件系统且与目标格式一致，无需格式化 
    try:
        if fmt: raise OSError(19)                              # 需要格式化
        mount_(p)                                              # 挂载并打印提示
    except OSError as err:
        if err.errno == 19:                                    # ENODEV,需要格式化 
            if fsf != _EMPTY:                                  # 块设备内有数据，需要与用户交互
                ans = input('Data exists in the partition. Confirm format? Enter Y or N:')
                if ans in 'Nn':                                # 若输入N或n，不选择格式化
                    print('Stop formatting and mounting.')
                    sys.exit(0)                                # 保留数据，退出程序 
            print('Formatting partition, all data will be erased...')   # 用户确认格式化
            fs.mkfs(p)                                         # 格式化
            mount_(p)                                          # 挂载并打印提示
        else: raise                                            # 其它错误，再次抛出 
if __name__=='__main__':    
    mount_partition('user_data','/user_data')
