def isBufProtocol(obj):
    try:
        memoryview(obj) 
        return True
    except (TypeError,ValueError):
        return False
print(isBufProtocol('abcd'))        # True
print(isBufProtocol(123))           # False
print(isBufProtocol([1,2,3]))       # False
