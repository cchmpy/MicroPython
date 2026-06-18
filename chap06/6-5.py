from esp32 import Partition
import esp,gc
def partitions_info():    
    # 打印flash和内存的大小
    print(f'flash  size: {esp.flash_size()/1024:.3f}KiB')
    print(f'memory size: {(gc.mem_free()+gc.mem_alloc())/1024:.3f}KiB')
    print('-'*70)  # 打印分隔线
    # ---------------------1. 定义分区类型、子类型信息的字典---------------
    p_type = {0:'app',1:'data'}    
    app_subtype = {i:f'ota_{i-0x10}' for i in range(0x10,0x20)} | \
                  {0x00:'factory',0x20:'test'}   
    data_subtype = {0:'ota',1:'phy',2:'nvs',4:'nvs_keys',0x81:'fat',
                    0x82:'spiffs',0x83:'littlefs',6:'undefined'}
    # ---------------------2. 搜索分区并获取分区信息-----------------------
    info = []                                             # 保存分区信息的列表
    for i in range(2):
        for x in Partition.find(i): info.append(x.info()) # 搜索data和app分区并添加分区信息
    # ---------------------3. 按分区地址对列表排序---------------------------
    info.sort(key=lambda x:x[2])                          # 按偏移地址排序    
    # ---------------------4. 打印分区表信息（表头和每个分区的信息）----------
    print(f"{'Name':<17}{'Type':<5}{'SubType':<10}\
{'Offset':<9}{'Size (bytes)':<20}{'Flags':<9}")
    for x in info:
        s = data_subtype if x[0] else app_subtype
        print(f"{x[4]:<17}\
{p_type.get(x[0],x[0]):<5}{s.get(x[1],x[1]):<10}\
{hex(x[2]):<9}{hex(x[3])+' ('+str(x[3])+')':<20}\
{'encrypted' if x[5] else '':<9}")

if __name__=='__main__':
    partitions_info()
