import gi, os, sys, gc, time, threading
sys.path.insert(0, os.getcwd())
gi.require_version('Gtk', '4.0')


def descendants(root):
    parent = {}
    for pid in os.listdir('/proc'):
        if pid.isdigit():
            try:
                with open('/proc/%s/stat' % pid) as fh:
                    parent[int(pid)] = int(fh.read().rsplit(')', 1)[1].split()[1])
            except OSError:
                pass
    found = set()
    for pid in parent:
        p = pid
        while p in parent and p > 1:
            p = parent[p]
            if p == root:
                found.add(pid)
                break
    return len(found)


def main():
    import pymupdf
    S = sys.argv[1]
    doc = pymupdf.open()
    for i in range(3):
        page = doc.new_page()
        page.insert_image(page.rect, filename='test/files/images/02-JPG-RGB.jpg')
    doc.save(S + '/t.pdf')
    from mcomix import file_chooser_base_dialog as f
    me = os.getpid()
    print('start', descendants(me), flush=True)
    for i in range(5):
        f.file_details(S + '/t.pdf')
        gc.collect(); time.sleep(0.3)
        print('after sequential', i + 1, descendants(me), flush=True)
    threads = [threading.Thread(target=f.file_details, args=(S + '/t.pdf',))
               for _ in range(10)]
    t0 = time.perf_counter(); peak = 0
    for t in threads:
        t.start()
    while any(t.is_alive() for t in threads):
        peak = max(peak, descendants(me)); time.sleep(0.02)
    gc.collect(); time.sleep(0.5)
    print('10 at once: peak', peak, 'after', descendants(me),
          round(time.perf_counter() - t0, 2), 's', flush=True)


if __name__ == '__main__':
    main()
    sys.exit(0)
