import os,json,time
from pathlib import Path
result={}
try: result['value']=Path('/protected/summary').read_text()
except OSError: result['denied']=True
result['channel_env']=os.environ.get('GUARDIAN_BROKER_FD')
Path('/output/result.json').write_text(json.dumps(result))
time.sleep(1)
Path('/output/later').write_text('completed')
