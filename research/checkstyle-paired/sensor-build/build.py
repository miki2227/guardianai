import hashlib,json,os,pathlib,subprocess,urllib.request,tarfile
root=pathlib.Path('/home/pratz/guardianai-tools/strace-libdw-v1');root.mkdir()
(root/'debs').mkdir();u=root/'deps';u.mkdir()
packages=['libdw-dev','libdw1t64','libelf-dev','libelf1t64','libdebuginfod1t64','libzstd-dev','zlib1g-dev','liblzma-dev','libbz2-dev']
with (root/'download.log').open('w') as log:
 subprocess.run(['apt','download',*packages],cwd=root/'debs',stdout=log,stderr=subprocess.STDOUT,check=True)
for p in (root/'debs').glob('*.deb'):
 subprocess.run(['dpkg-deb','-x',str(p),str(u)],check=True)
url='https://strace.io/files/7.0/strace-7.0.tar.xz'
archive=root/'strace-7.0.tar.xz';urllib.request.urlretrieve(url,archive)
with tarfile.open(archive) as t:
 for m in t.getmembers():
  assert not m.name.startswith('/') and '..' not in pathlib.PurePosixPath(m.name).parts
 t.extractall(root,filter='data')
env=dict(os.environ);env['PKG_CONFIG_PATH']=str(u/'usr/lib/x86_64-linux-gnu/pkgconfig');env['PKG_CONFIG_SYSROOT_DIR']=str(u)
env['LDFLAGS']='-Wl,-rpath,'+str(u/'usr/lib/x86_64-linux-gnu')
with (root/'build.log').open('w') as log:
 subprocess.run(['./configure','--with-libdw','--without-libunwind','--enable-mpers=no'],cwd=root/'strace-7.0',env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 subprocess.run(['make','-j4'],cwd=root/'strace-7.0',env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
binary=root/'strace-7.0/src/strace'
version=subprocess.check_output([str(binary),'-V'],stderr=subprocess.STDOUT,text=True)
report={'source_url':url,'source_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'binary':str(binary),'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'version':version,'packages':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'debs').glob('*.deb')}}
(root/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
