class RAMBlockDev:                                      # 定义支持块协议的RAMBlockDev类
    def __init__(self, block_size, num_blocks):
        self.block_size = block_size                    # 块大小
        self.data = bytearray(block_size * num_blocks)  # 分配内存，作为保存数据的设备
   
    def readblocks(self, block_num, buf, offset=0):
        addr = block_num * self.block_size + offset
        for i in range(len(buf)):
            buf[i] = self.data[addr + i] 
   
    def writeblocks(self, block_num, buf, offset=0):
        # 内存设备无需擦除，直接更改
        addr = block_num * self.block_size + offset
        for i in range(len(buf)):
            self.data[addr + i] = buf[i]

    def ioctl(self, op, arg):
        if op == 4:                                     # 获取块数量
            return len(self.data) // self.block_size
        if op == 5:                                     # 获取块大小
            return self.block_size 
        if op == 6:                                     # 块擦除,因无需擦除，所以是空操作
            return 0
if __name__== '__main__':
    import vfs
    ram_bdev = RAMBlockDev(512, 50)                     # 定义基于内存的块设备
    # vfs.VfsFat.mkfs(ram_bdev)                        # 使用Fat文件系统格式化块设备
    vfs.VfsLfs2.mkfs(ram_bdev)                          # 使用Littlefs V2文件系统格式化块设备
    vfs.mount(bdev, '/ramdisk')                         # 挂载块设备到目录/ramdisk    
   
    with open('/ramdisk/1.txt', 'w+') as f:             # 文件操作
        f.write('Hello world')
        f.seek(0)
        print(f.read())
