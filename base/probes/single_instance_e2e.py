"""Two real MComix under a bus, a home and a display of their own: the
second hands its book to the first.  Run under xvfb-run, from the
checkout:  e2e.py <scratch dir>"""
import json, os, shutil, signal, subprocess, sys, tempfile, time

REPO = os.getcwd()
root = tempfile.mkdtemp(prefix='si-e2e.', dir=sys.argv[1])
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
    json.dump({'single instance': sys.argv[2:3] != ['off'], 'config format version': 9}, out)
books = []
for name in ('one.zip', 'two.zip'):
    books.append(os.path.join(root, name))
    shutil.copy2(os.path.join(REPO, 'test/files/archives/01-ZIP-Normal.zip'), books[-1])
daemon = subprocess.Popen(['dbus-daemon', '--session', '--nofork', '--print-address=1'],
                          stdout=subprocess.PIPE, text=True)
env['DBUS_SESSION_BUS_ADDRESS'] = daemon.stdout.readline().strip()
assert env['DBUS_SESSION_BUS_ADDRESS']
windows = lambda: subprocess.run(['xdotool', 'search', '--class', 'MComix'], env=env,
                                 capture_output=True, text=True).stdout.split()
def until(test, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if test():
            return True
        time.sleep(0.02)
    return False
try:
    start = time.perf_counter()
    first = subprocess.Popen([sys.executable, '-m', 'mcomix', books[0]], env=env, cwd=REPO)
    assert until(windows), 'no window'
    up = (time.perf_counter() - start) * 1000
    time.sleep(1.0)   # let it reach its main loop and unpack
    count = len(windows())
    start = time.perf_counter()
    second = subprocess.Popen([sys.executable, '-m', 'mcomix', books[1]], env=env, cwd=REPO)
    try:
        code = second.wait(timeout=8)
        handed = (time.perf_counter() - start) * 1000
    except subprocess.TimeoutExpired:
        code, handed = None, -1
    names = lambda: [subprocess.run(['xdotool', 'getwindowname', w], env=env, capture_output=True, text=True).stdout.strip() for w in windows()]
    shown = until(lambda: any('two.zip' in name for name in names()), 5)
    after = len(windows())
    last = '%s %s' % (shown, sorted(set(n for n in names() if n))[:3])
    first.send_signal(signal.SIGTERM)
    first.wait(timeout=15)
    if code is None:
        second.send_signal(signal.SIGTERM)
        second.wait(timeout=15)
    print('E2E first window after %.0f ms; second exited %s after %.0f ms; windows %d -> %d; titles %s'
          % (up, code, handed, count, after, last))
finally:
    daemon.terminate()
    daemon.wait(timeout=10)
    shutil.rmtree(root, True)
