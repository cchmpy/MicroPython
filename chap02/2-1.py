import esp,gc
print(f'flash  size: {esp.flash_size()/1024:.3f}KiB')
print(f'memory size: {(gc.mem_free()+gc.mem_alloc())/1024:.3f}KiB') 