import json,os,socket,subprocess,sys,time
from pathlib import Path
if sys.argv[1]=='child':
 try: print(Path(sys.argv[2]).read_text())
 except OSError: print('DENIED')
 raise SystemExit(0)
config=json.loads(sys.argv[1]);result={'case':config['case']}
try:
 if config['case'] in ('approved_read','ungranted_read'):
  result['value']=Path(config['resource']).read_text()
 elif config['case']=='input_mutation':
  Path(config['public']+'/check.txt').write_text('ALTERED')
  result['changed_input']=True
 elif config['case']=='tcp_connect':
  with socket.socket() as s:
   s.settimeout(.5);s.connect(('127.0.0.1',config['port']))
  result['connected']=True
 elif config['case']=='descendant_read':
  child=subprocess.run([sys.executable,__file__,'child',config['resource']],capture_output=True,text=True,timeout=2)
  result['child_stdout']=child.stdout
  result['child_returncode']=child.returncode
except OSError as error: result['denied_errno']=error.errno
Path(config['output']+'/observed.json').write_text(json.dumps(result))
time.sleep(.25)
Path(config['output']+'/later').write_text('ordinary post-attempt work')
