# RSS of the native-PDF worker processes (FitzManager through forkserver), and their start-up.
import os, sys, time, signal, threading

def rss(pid):
    for line in open(f'/proc/{pid}/smaps_rollup'):
        if line.startswith('Pss:'):
            return int(line.split()[1]) // 1024

def descendants(root):
    parent = {}
    for p in os.listdir('/proc'):
        if p.isdigit():
            try:
                parent[int(p)] = int(open(f'/proc/{p}/stat').read().rsplit(')', 1)[1].split()[1])
            except OSError:
                pass
    out, todo = [], [root]
    while todo:
        r = todo.pop()
        kids = [p for p, pp in parent.items() if pp == r]
        out += kids; todo += kids
    return out

def main():
    sys.path.insert(0, os.getcwd())
    from mcomix.archive.native_pdf.manager import FitzProcessWrangler
    n = int(sys.argv[3])
    out = sys.argv[2]; os.makedirs(out, exist_ok=True)
    first = FitzProcessWrangler(sys.argv[1], log_level=None)
    names = list(first.iter_contents())
    times = []
    def one(i):
        t = time.perf_counter()
        w = FitzProcessWrangler(sys.argv[1], log_level=None)
        times.append(time.perf_counter() - t)
        list(w.extract_pages(names[i::n], out))
        done.wait()
    done = threading.Event()
    threads = [threading.Thread(target=one, args=(i,)) for i in range(n)]
    for t in threads: t.start()
    while len(times) < n: time.sleep(0.05)
    time.sleep(1.0)
    kids = descendants(os.getpid())
    sizes = sorted(rss(k) or 0 for k in kids)
    print(f'{n} workers: start-up median {sorted(times)[n//2]*1000:.0f} ms; {len(kids)} processes, PSS {sum(sizes)} MB total, largest {sizes[-3:]} MB; parent {rss(os.getpid())} MB', flush=True)
    for k in kids:
        try: os.kill(k, signal.SIGKILL)
        except OSError: pass
    os._exit(0)

if __name__ == '__main__':
    main()
