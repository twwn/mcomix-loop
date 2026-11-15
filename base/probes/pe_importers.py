import os, sys, pefile
bundle = sys.argv[1]; wanted = [w.lower() for w in sys.argv[2:]]
files = {}
for d, _, fs in os.walk(bundle):
    for f in fs:
        if f.lower().endswith(('.dll', '.exe', '.pyd')): files[f.lower()] = os.path.join(d, f)
imp = {}
for n, p in files.items():
    pe = pefile.PE(p, fast_load=True)
    pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'], pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT']])
    names = set()
    for attr in ('DIRECTORY_ENTRY_IMPORT', 'DIRECTORY_ENTRY_DELAY_IMPORT'):
        for e in getattr(pe, attr, []): names.add(e.dll.decode().lower())
    imp[n] = names
for w in wanted:
    print(w, '<-', sorted(n for n, s in imp.items() if w in s))
