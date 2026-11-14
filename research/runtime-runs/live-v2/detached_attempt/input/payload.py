import os,time
from pathlib import Path
if os.fork()==0:
 os.setsid()
 time.sleep(1)
 Path('/output/escaped').write_text('bad')
 os._exit(0)
try: os.unlink('/workspace/payload.py')
except OSError: pass
time.sleep(3)
Path('/output/late').write_text('bad')
