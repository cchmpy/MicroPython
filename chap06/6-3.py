import sys
bits, v = 0, sys.maxsize
while v:
    bits += 1
    v >>= 1
if bits > 32: print(64,bits) # 64位或更高平台,输出：64 63  
elif bits>16: print(32,bits) # 32位平台，输出32 31

