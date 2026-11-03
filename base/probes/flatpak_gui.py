import os, subprocess, sys, time
S = sys.argv[1]
home = os.path.join(S, 'fp-home')
cmd = ['flatpak', 'build', '--socket=x11', '--share=ipc', '--device=dri',
       '--filesystem=%s' % home, '--filesystem=%s:ro' % os.path.join(S, 'djvu'),
       '--env=XDG_CONFIG_HOME=%s/config' % home, '--env=XDG_DATA_HOME=%s/data' % home,
       '--env=XDG_CACHE_HOME=%s/cache' % home, '--env=HOME=%s' % home,
       '--env=FLATPAK_ID=io.github.twwn.mcomix', '--env=GDK_BACKEND=x11',
       os.path.join(S, 'fp-build'), 'mcomix', os.path.join(S, 'djvu', '03-RAR-Normal.rar')]
log = open(os.path.join(S, 'fp-gui.log'), 'w')
proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
time.sleep(8)
alive = proc.poll() is None
subprocess.run(['import', '-window', 'root', os.path.join(S, 'fp-shot', 'gui.png')])
out = subprocess.run(['xdotool', 'search', '--class', 'io.github.twwn.mcomix'], capture_output=True, text=True).stdout.split()
print('alive', alive, 'windows with class io.github.twwn.mcomix:', len(out), flush=True)
proc.terminate()
try:
    proc.wait(5)
except subprocess.TimeoutExpired:
    proc.kill()
