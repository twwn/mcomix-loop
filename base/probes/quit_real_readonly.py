"""A real MComix, in a home, bus and display of its own, told to quit while
its config directory cannot be written to.  Run under xvfb-run from the
checkout:  quit_full.py <scratch dir>"""
import json, os, shutil, signal, subprocess, sys, tempfile, time

REPO = os.getcwd()
root = tempfile.mkdtemp(prefix='quitfull.', dir=sys.argv[1])
home = os.path.join(root, 'home')
env = dict(os.environ, HOME=home, XDG_CONFIG_HOME=os.path.join(home, 'config'),
           XDG_DATA_HOME=os.path.join(home, 'data'),
           XDG_CACHE_HOME=os.path.join(home, 'cache'),
           TMPDIR=os.path.join(root, 'tmp'), PYTHONPATH=REPO, LANGUAGE='en',
           GDK_BACKEND='x11', NO_AT_BRIDGE='1')
env.pop('WAYLAND_DISPLAY', None)
env.pop('FLATPAK_ID', None)
for folder in ('config/mcomix', 'data', 'cache'):
    os.makedirs(os.path.join(home, folder))
os.makedirs(env['TMPDIR'])
conf = os.path.join(home, 'config', 'mcomix', 'preferences.conf')
with open(conf, 'w') as out:
    json.dump({'config format version': 9}, out)
book = os.path.join(root, 'one.zip')
shutil.copy2(os.path.join(REPO, 'test/files/archives/01-ZIP-Normal.zip'), book)
daemon = subprocess.Popen(['dbus-daemon', '--session', '--nofork', '--print-address=1'],
                          stdout=subprocess.PIPE, text=True)
env['DBUS_SESSION_BUS_ADDRESS'] = daemon.stdout.readline().strip()
windows = lambda: subprocess.run(['xdotool', 'search', '--class', 'MComix'], env=env,
                                 capture_output=True, text=True).stdout.split()
def until(test, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if test():
            return True
        time.sleep(0.05)
    return False
config_dir = os.path.join(home, 'config', 'mcomix')
first = None
try:
    first = subprocess.Popen([sys.executable, '-m', 'mcomix', book], env=env, cwd=REPO,
                             stderr=subprocess.PIPE, text=True)
    assert until(windows), 'no window'
    time.sleep(2.0)
    print('window up:', len(windows()) > 0, flush=True)
    os.chmod(config_dir, 0o555)          # what a full disk or a read-only home does
    first.send_signal(signal.SIGTERM)    # run.py: idle_add(window.terminate_program)
    try:
        first.wait(timeout=10)
        print('process exited, code', first.returncode, flush=True)
    except subprocess.TimeoutExpired:
        print('process STILL ALIVE 10 s after quit; windows on screen:', len(windows()), flush=True)
    os.chmod(config_dir, 0o755)
    leftovers = os.listdir(env['TMPDIR'])
    print('temporary folders left:', leftovers, flush=True)
finally:
    os.chmod(config_dir, 0o755)
    if first is not None and first.poll() is None:
        first.kill()
        try:
            err = first.communicate(timeout=5)[1]
            print('\n'.join(l for l in err.splitlines() if 'Error' in l or 'Permission' in l or 'Berechtigung' in l)[-800:])
        except Exception as e:
            print('stderr unread', e)
    daemon.kill()
    shutil.rmtree(root, ignore_errors=True)
