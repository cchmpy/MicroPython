from ahttp import Application,Response   # 导入程序11-13.py（ahttp.py）
from wifinvsmg import WifiNvsManager     # 导入程序6-9.py（wifinvsmg.py）
from machine import reset
from micropython import const
import  asyncio, myutils

HTML_DOC = const('''<!doctype html>
<html lang="zh-CN"><head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wi-Fi配网</title>
    <style>.btn {width: 80px;}</style>
</head><body>
    <div style="text-align:center;">
        <h2>ESP32 Wi-Fi配网</h2>
        <p>ssid:<input type="text" id="ssid"> </p>
        <p>key:<input type="text" id="key"> </p>
        <p><button class="btn" type="button" id="submit_btn">提交</button>&emsp;
            <button class="btn" type="button" id="restart_btn">重启硬件</button> </p>
        <p><span id="status"></span></p>
    </div>
</body><script>
        const s = document.getElementById('status');
        async function request(url, options = {}, timeout = 5000) {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => { controller.abort(); }, timeout);
            try {
                const response = await fetch(url, { ...options, signal: controller.signal });
                clearTimeout(timeoutId);
                if (response.ok) { const data = await response.text(); s.innerText = data; }
            } catch (error) {
                clearTimeout(timeoutId);
                s.innerText = '网络异常,设备离线'; 
                console.error('网络异常', error.name);
            }
        }
        async function submit_ssid() { 
            // 构造表单数据，不使用FormData()对象,服务器未实现解析multipart/form-data类型数据
            const formData = new URLSearchParams();
            formData.append("ssid", document.getElementById('ssid').value);
            formData.append('key', document.getElementById('key').value);
            // 浏览器自动设置Content-Type: application/x-www-form-urlencoded
            await request('/wifi', { method: 'POST', body: formData },8000); 
        }
        // 添加事件处理函数
        document.getElementById('restart_btn').addEventListener('click',
()=>{request('/restart',{},5000);});
        document.getElementById('submit_btn').addEventListener('click', () => {submit_ssid();});
</script></html>''')

class WiFiConfig:
    def __init__(self,ap_ssid='ESP32_AP',ap_key='12345678'):
        self._nvs = WifiNvsManager()                           # 定义Wi-Fi账号NVS管理对象
        wlan = myutils.create_ap(ap_ssid, ap_key)              # 创建热点
        # wlan = myutils.connect_wifi()                        # 测试时，可不创建热点
        app = Application()
        app.add_routes([('/', self._index_handler),            # 路径"/"的处理协程
                        ('/wifi',self._wifi_handler),          # 路径"/wifi"的处理协程
                        ('/restart',self._restart_handler)])   # 路径"/restart"的处理协程
        app.run(host=wlan.ifconfig()[0])
        
    async def _index_handler(self,request):                    # 定义路径"/"(主页)的处理协程
        return Response(headers={'Content-Type': 'text/html'}, body=HTML_DOC)
    
    async def _wifi_handler(self,request):                     # 定义路径"/wifi"的处理协程
        ssid=request.get_param('ssid')                         # 获取表单提交的ssid
        key =request.get_param('key')                          # 获取表单提交的key
        if ssid and key: 
            self._nvs.save_ssid_key(ssid,key,True)             # 保存ssid和key至NVS，并设为最近有效账号
            hint = f'设备已接收{ssid}相关数据'                 # 定义在网页显示的提示信息 
        else: hint = '设备接收数据失败'
        return Response(headers={'Content-Type': 'text/plain'}, body=hint)        
    
    async def _restart_handler(self,request):                  # 定义路径"/restart"的处理协程
        async def task():                                      # 异步任务：为服务器响应等待2秒，后重启
            await asyncio.sleep(2)
            reset()
        asyncio.create_task(task())                            # 创建异步任务，加入消息队列
        return Response(headers={'Content-Type': 'text/plain'}, body='设备已重新启动')       
if __name__ == '__main__':
    WiFiConfig()                                               # 启动服务器                                               
