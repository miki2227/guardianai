import hashlib,json,os,pathlib,subprocess,shutil
root=pathlib.Path('/home/pratz/guardianai-tools/strace-libdw-v1');u=root/'deps'
shutil.copyfile(root/'build.log',root/'configure-failed.log')
env=dict(os.environ);env['PKG_CONFIG_PATH']=str(u/'usr/lib/x86_64-linux-gnu/pkgconfig');env['PKG_CONFIG_SYSROOT_DIR']=str(u)
env['CPPFLAGS']='-I'+str(u/'usr/include')
env['LDFLAGS']='-L'+str(u/'usr/lib/x86_64-linux-gnu')+' -Wl,--disable-new-dtags,-rpath,'+str(u/'usr/lib/x86_64-linux-gnu')
with (root/'build.log').open('w') as log:
 subprocess.run(['./configure','--with-libdw','--without-libunwind','--enable-mpers=no'],cwd=root/'strace-7.0',env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 subprocess.run(['make','-j4'],cwd=root/'strace-7.0',env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
binary=root/'strace-7.0/src/strace';archive=root/'strace-7.0.tar.xz'
version=subprocess.check_output([str(binary),'-V'],stderr=subprocess.STDOUT,text=True)
report={'source_url':'https://strace.io/files/7.0/strace-7.0.tar.xz','source_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'binary':str(binary),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'version':version,'packages':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'debs').glob('*.deb')}}
(root/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
