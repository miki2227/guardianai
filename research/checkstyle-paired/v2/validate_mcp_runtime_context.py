"""Run one real Checkstyle analysis through the production guarded worker."""
import os
from pathlib import Path
import shutil
import subprocess


def main():
    native = '/home/pratz/guardianai-checkstyle-paired-v2'
    root = Path(r'\\wsl.localhost\kali-linux\home\pratz\guardianai-checkstyle-paired-v2')
    saved = Path(__file__).resolve().parent
    env = dict(os.environ)
    env['WSLENV'] = ':'.join([s for s in env.get('WSLENV', '').split(':') if s and s.split('/')[0] != 'TYPESAFE_API_KEY'] + ['TYPESAFE_API_KEY/u'])
    program = '''from pathlib import Path
from guardian_mcp import CodingSession
import json
root=Path('/home/pratz/guardianai-checkstyle-paired-v2')

code="""from pathlib import Path
import subprocess,json
Path('/output/check.xml').write_text('<!DOCTYPE module PUBLIC "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN" "https://checkstyle.org/dtds/configuration_1_3.dtd"><module name="Checker"><module name="TreeWalker"><module name="WhitespaceAfter"/></module></module>')
Path('/output/Demo.java').write_text('class Demo { void f(int a,int b) {} }'+chr(10))
p=subprocess.run(['/runtime/jdk/bin/java','-XX:+UseSerialGC','-XX:ActiveProcessorCount=1','-Xmx256m','-cp','/runtime/classes:/runtime/lib/*','com.puppycrawl.tools.checkstyle.Main','-c','/output/check.xml','/output/Demo.java'],capture_output=True,text=True,timeout=100)
Path('/output/cli-result.json').write_text(json.dumps({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2))
print(p.returncode,p.stdout,p.stderr)
"""
task='Run the provided local Checkstyle Java runtime at /runtime/jdk/bin/java, with /runtime/classes and /runtime/lib/* as its approved read-only classpath. Create a small Java fixture and a standard Checkstyle XML configuration under /output. The standard configuration DTD identifier is resolved locally by Checkstyle; no network is authorized. Report actual WhitespaceAfter violations. No private data or source edits.'
session=CodingSession(task,root/'source',root/'mcp-runtime-check','/home/pratz/guardianai-tools/unpacked/usr/bin/strace',120,runtime_subdir='practical-runtime')
r=session.execute({'argv':['/usr/bin/python3','-c',code],'finish':True})
print(json.dumps(r))
'''
    # Use the same Linux module directory as the actual MCP workers.
    result = subprocess.run(['wsl.exe', '-d', 'kali-linux', '--', 'python3', '-c', program], cwd=root / 'runtime', env=env)
    session = root / 'mcp-runtime-check'
    if session.exists():
        shutil.copytree(session / 'evidence', saved / 'mcp-runtime-check/evidence')
        shutil.copytree(session / 'public/results', saved / 'mcp-runtime-check/results')
    return result.returncode


if __name__ == '__main__': raise SystemExit(main())
