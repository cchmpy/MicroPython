from espnow_e2e import EspnowE2E
pmac = b'\x08\xf9\xe0\xd3\xb9\xb8'    # 对端设备的mac地址
msg = b'白日依山尽，黄河入海流。欲穷千里目，更上一层楼。' 

e2e = EspnowE2E(pmac)
cnt,cnt_max = 0, 100                  # 接收加密消息次数和最大次数限制
e2e.encrypt_send(msg)                 # 加密并发送消息
while True:        
    msg = e2e.recv_decrypt()          # 接收并解密消息
    assert msg is not None            # 断言接收或解密消息时是否出现错误
    cnt += 1
    print(f'recv {cnt}\r',end='')     # 单行内打印接收消息次数
    if cnt>=cnt_max: break
    e2e.encrypt_send(msg)
print('\n',bytes(msg).decode())       # 打印最后一次接收的消息    
e2e.deinit() 