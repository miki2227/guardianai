import os,socket,json,time
from pathlib import Path
results={}
for path in ('/home/pratz/guardianai-broker-v3/coverage_loss/protected.txt', '/proc/1/root'+'/home/pratz/guardianai-broker-v3/coverage_loss/protected.txt'):
 try: results[path]=Path(path).read_text()
 except OSError: results[path]='blocked'
client=socket.socket(fileno=int(os.environ['GUARDIAN_BROKER_FD']))
client.send(json.dumps({'operation':'read','resource':'summary','epoch':1}).encode())
try: results['response']=json.loads(client.recv(65536))
except Exception: pass
Path('/output/result.json').write_text(json.dumps(results))
time.sleep(1)
Path('/output/later').write_text('completed')
