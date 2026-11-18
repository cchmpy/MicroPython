import deflate, json
config = {"name": "c/c++", "type":"cppvsdbg", "request":"launch",
          "program": "${fileDirname}\\${fileBasenameNoExtension}.exe",
          "args": [], "stopAtEntry":0, "cwd":"${workspaceFolder}"}
# 将字典对象序列化为json字符串，并隐含调用DeflateIO流的write()方法压缩并写入流。
with open("config.gz", "wb") as f:    
    with deflate.DeflateIO(f, deflate.GZIP, 6) as d:
        json.dump(config, d)
# 先隐含调用DeflateIO流的read()方法解压为json字符串，再将其转换为字典对象
with open("config.gz", "rb") as f:
    with deflate.DeflateIO(f, deflate.GZIP, 6) as d:
        config = json.load(d)
        print(config)             # 打印字典对象
