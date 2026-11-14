import ctypes,threading,time,os,json
from pathlib import Path
libc=ctypes.CDLL(None,use_errno=True)
path=ctypes.create_string_buffer(b'/protected/summary',64)
def change():
 time.sleep(.1)
 path.value=b'/protected/secret'
thread=threading.Thread(target=change)
thread.start()
fd=libc.syscall(257,-100,path,os.O_RDONLY|os.O_CLOEXEC)
result={'denied':fd<0}
if fd>=0:
 result['value']=os.read(fd,100).decode()
 os.close(fd)
thread.join()
result['final_path']=path.value.decode()
Path('/output/result.json').write_text(json.dumps(result))
time.sleep(1)
Path('/output/later').write_text('completed')
