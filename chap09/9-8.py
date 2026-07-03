from esp32_ulp import src_to_binary, assemble_file
source = """\
data:       .long 0
entry:      move r3, data    # 将数据加载到r3中
            ld r2, r3, 0     # 将数据（[r3+0]）加载到r2中
            add r2, r2, 1    # r2增加1
            st r2, r3, 0     # 将R2的内容存储到数据（[r3+0]）中
            halt             # 暂停ULP协处理器（直到它再次被唤醒）
"""
binary = src_to_binary(source, cpu="esp32")     # 编译生成机器码（bytes对象）
assemble_file('counter.s','esp32')              # 编译生成counter.ulp机器码文件
with open('counter.ulp','rb') as f:             # 打开counter.ulp
    binary1 = f.read()

print(len(binary),len(binary1),binary==binary1) # 输出：36 36 True