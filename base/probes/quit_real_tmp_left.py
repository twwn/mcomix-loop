"""A real MComix, in a home, bus, display and TMPDIR of its own, opens a
book and is told to quit; prints what it left in its TMPDIR, and what each
folder left there holds.  Run under xvfb-run from the checkout:
    quit_real_tmp_left.py <scratch dir> <pdf|zip> <sigterm|keys>
pdf: a three-page PDF built with PyMuPDF, read by the native PDF reader,
whose worker processes run through multiprocessing (forkserver)."""
import json, os, shutil, signal, subprocess, sys, tempfile, time

REPO = os.getcwd()
kind, how = sys.argv[2], sys.argv[3]
root = tempfile.mkdtemp(prefix='quittmp.', dir=sys.argv[1])
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
with open(os.path.join(home, 'config', 'mcomix', 'preferences.conf'), 'w') as out:
    json.dump({'config format version': 9}, out)
if kind == 'pdf':
    import pymupdf
    book = os.path.join(root, 'three.pdf')
    doc = pymupdf.open()
    for n in range(3):
        doc.new_page().insert_text((72, 72), 'page %d' % n)
    doc.save(book)
else:
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
def tmp_now():
    found = {}
    for name in sorted(os.listdir(env['TMPDIR'])):
        path = os.path.join(env['TMPDIR'], name)
        found[name] = sorted(os.listdir(path)) if os.path.isdir(path) else 'file'
    return found
first = None
try:
    first = subprocess.Popen([sys.executable, '-m', 'mcomix', book], env=env, cwd=REPO,
                             stderr=subprocess.PIPE, text=True)
    assert until(windows), 'no window'
    time.sleep(3.0)
    print('open, TMPDIR holds:', tmp_now(), flush=True)
    if how == 'sigterm':
        first.send_signal(signal.SIGTERM)    # run.py: idle_add(window.terminate_program)
    else:
        win = windows()[0]
        subprocess.run(['xdotool', 'windowactivate', '--sync', win], env=env)
        subprocess.run(['xdotool', 'key', '--window', win, 'ctrl+q'], env=env)
    try:
        first.wait(timeout=15)
        print('process exited, code', first.returncode, flush=True)
    except subprocess.TimeoutExpired:
        print('process STILL ALIVE 15 s after quit', flush=True)
    time.sleep(1.5)  # children of the PDF reader
    print('after quit, TMPDIR holds:', tmp_now(), flush=True)
    left = subprocess.run(['pgrep', '-f', root], capture_output=True, text=True).stdout.split()
    print('processes still naming the scratch root:', len(left), flush=True)
finally:
    if first is not None and first.poll() is None:
        first.kill()
    if first is not None:
        try:
            err = first.communicate(timeout=5)[1]
            print('stderr tail:', err.strip().splitlines()[-3:] if err.strip() else '(none)')
        except Exception as e:
            print('stderr unread', e)
    daemon.kill()
    shutil.rmtree(root, ignore_errors=True)
