import esp,gc
print('flash  size:', esp.flash_size()//1024, 'KiB')
print(f'memory size:', (gc.mem_free()+gc.mem_alloc())//1024, 'KiB') 