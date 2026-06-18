from espnow_e2e import EspnowE2E 
pmac = b'\xd8\x13*\xf1\xaa\x10'
e2e = EspnowE2E(pmac)
cnt,cnt_max = 0, 100
while True:
    msg = e2e.recv_decrypt()
    assert msg is not None
    cnt +=1
    print(f'recv {cnt}\r',end='')
    if cnt>=cnt_max:
        print('\n',bytes(msg).decode())  
        cnt = 0
    e2e.encrypt_send(msg)
    if not cnt: break 
e2e.deinit()