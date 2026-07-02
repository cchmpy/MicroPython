from micropython import const
_IRQ_CENTRAL_CONNECT       = const(1)
_IRQ_CENTRAL_DISCONNECT    = const(2)
_IRQ_GATTS_WRITE           = const(3)
_IRQ_GATTS_READ_REQUEST    = const(4)
_IRQ_SCAN_RESULT           = const(5)
_IRQ_SCAN_DONE             = const(6)
_IRQ_PERIPHERAL_CONNECT    = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT  = const(9)
_IRQ_GATTC_SERVICE_DONE    = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE   = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT     = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE       = const(14)
_IRQ_GATTC_READ_RESULT   = const(15)
_IRQ_GATTC_READ_DONE     = const(16)
_IRQ_GATTC_WRITE_DONE    = const(17)
_IRQ_GATTC_NOTIFY        = const(18)
_IRQ_GATTC_INDICATE      = const(19)
_IRQ_GATTS_INDICATE_DONE = const(20)
_IRQ_MTU_EXCHANGED       = const(21)
...                      # 省略以_IRQ_L2CAP开头的面向信道连接的事件（22-26）
_IRQ_CONNECTION_UPDATE   = const(27)
_IRQ_ENCRYPTION_UPDATE   = const(28)
_IRQ_GET_SECRET          = const(29)
_IRQ_SET_SECRET          = const(30)
_IRQ_PASSKEY_ACTION      = const(31)

def ble_irq(event, data):        
    # 外围设备(通常是服务器)上触发的消息（连接、断开、更新连接）
    if event == _IRQ_CENTRAL_CONNECT:          # 远端的一个中央设备连接到本地外围设备
        conn_handle, addr_type, addr = data
    elif event == _IRQ_CENTRAL_DISCONNECT:     # 远端的一个中央设备已与本地外围设备断开连接 
        conn_handle, addr_type, addr = data
    elif event == _IRQ_CONNECTION_UPDATE:      # 远端设备更新了连接参数 
        conn_handle, conn_interval, conn_latency, supervision_timeout, status = data
    
    # 中央设备(通常是客户端)上触发的消息（连接、断开）
    elif event == _IRQ_PERIPHERAL_CONNECT:     # 远端的一个外围设备连接到本地中央设备
        conn_handle, addr_type, addr = data
    elif event == _IRQ_PERIPHERAL_DISCONNECT:  # 远端的一个外围设备已与本地中央设备断开连接
        conn_handle, addr_type, addr = data  
    
    # 观察者（通常是中央设备、客户端）设备上触发消息(扫描)-
    elif event == _IRQ_SCAN_RESULT:            # 扫描到一个广播包或扫描响应包，每获得一个结果触发一次
        addr_type, addr, adv_type, rssi, adv_data = data
    elif event == _IRQ_SCAN_DONE:              # 扫描持续时间已用完或手动停止
        pass
    
    # GATT服务器上触发的消息
    elif event == _IRQ_GATTS_WRITE:
        conn_handle, attr_handle = data        # 客户端已写入一个特性或描述符的值
    elif event == _IRQ_GATTS_READ_REQUEST:
        # 本地服务器调用gatts_notify()，gatts_indicate()将触发读取请求,conn_handle=65535
        # 远端客户端调用gattc_read()将触发读取请求,conn_handle=0
        # 返回一个非零整数来拒绝读取，或者返回零(或None)来接受读取。
        conn_handle, attr_handle = data
        # return None
    elif event == _IRQ_GATTS_INDICATE_DONE:
        # 客户端已确认了一个指示。如果确认成功，status将为零，否则为特定于实现的值
        conn_handle, value_handle, status = data
    
    # GATT客户端上触发的消息
    elif event == _IRQ_GATTC_SERVICE_RESULT:
        # 调用gattc_discover_services()搜索服务，每发现一个服务触发一次该事件
        conn_handle, start_handle, end_handle, uuid = data
    elif event == _IRQ_GATTC_SERVICE_DONE:
        # 调用gattc_discover_services()搜索服务完成后触发该事件
        # 搜索成功时status为零，否则为特定于实现的值
        conn_handle, status = data
    elif event == _IRQ_GATTC_CHARACTERISTIC_RESULT:
        # 调用gattc_discover_characteristics()搜索特性，每发现一个特性触发一次该事件
        conn_handle, end_handle, value_handle, properties, uuid = data
    elif event == _IRQ_GATTC_CHARACTERISTIC_DONE:
        # 调用gattc_discover_characteristics()搜索特性完成后触发该事件
        # 搜索成功时status为零，否则为特定于实现的值
        conn_handle, status = data
    elif event == _IRQ_GATTC_DESCRIPTOR_RESULT:
        # 调用gattc_discover_descriptors()搜索描述符，每发现一个描述符触发一次该事件
        conn_handle, dsc_handle, uuid = data
    elif event == _IRQ_GATTC_DESCRIPTOR_DONE:
        # 调用gattc_discover_descriptors()搜索描述符完成后触发该事件
        # 搜索成功时status为零，否则为特定于实现的值
        conn_handle, status = data
    elif event == _IRQ_GATTC_READ_RESULT:
        # 调用gattc_read()从服务器读取到一个结果
        conn_handle, value_handle, char_data = data
    elif event == _IRQ_GATTC_READ_DONE:
        # 调用gattc_read()读取完成后触发该事件
        # 读取成功时status为零，否则为特定于实现的值
        conn_handle, value_handle, status = data
    elif event == _IRQ_GATTC_WRITE_DONE:
        # 调用gattc_write()向服务器写入完成后触发该事件
        # 写入成功时status为零，否则为特定于实现的值
        conn_handle, value_handle, status = data
    elif event == _IRQ_GATTC_NOTIFY:           # 服务器发来一个通知
        conn_handle, value_handle, notify_data = data
    elif event == _IRQ_GATTC_INDICATE:         # 服务器发来一个指示
        conn_handle, value_handle, notify_data = data
    
    # GATT服务器和客户端上触发的消息
    elif event == _IRQ_MTU_EXCHANGED:          # 由本地或远端设备发起的ATT MTU 交换完成后触发该事件
        conn_handle, mtu = data
    
    # 配对和绑定，发起和响应设备上触发的消息 
    elif event == _IRQ_ENCRYPTION_UPDATE:      # 加密状态已更改(可能是配对或绑定的结果)
        conn_handle, encrypted, authenticated, bonded, key_size = data
    elif event == _IRQ_GET_SECRET: 
        # 系统加载密钥或配对请求时，将触发该密钥请求事件
        # 该事件中需要根据sec_type,index,key返回一个已存储的秘密（每次返回一个）
        # 如果key为None，则返回该sec_type的第一个索引值，否则返回此sec_type和key对应的值
        sec_type, index, key = data
        return value                           # value是一个已存储的密钥值
    elif event == _IRQ_SET_SECRET:
        # 密钥分配时会触发该消息，每分配一个密钥触发一次
        # 在此需要将sec_type和key，以及它们对应的密钥值value一起保存到存储器中
        # 返回True表示密钥分配成功，返回False表示失败
        sec_type, key, value = data
        return True
    elif event == _IRQ_PASSKEY_ACTION:
        # 在配对过程中（认证时）响应密钥(passkey)请求。此处需要调用函数gap_passkey()
        # Action将是一个与io配置兼容的动作。如果action是"数值比较"，passkey将是该数值，其它情况为0 
        conn_handle, action, passkey = data
    ...                                        # L2CAP面向连接信道触发消息（ESP32不支持，省略）
