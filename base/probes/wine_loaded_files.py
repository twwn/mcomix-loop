import os, re, sys
out, bundle = sys.argv[1], sys.argv[2]
sizes = {}
for d, _, fs in os.walk(bundle):
    for f in fs:
        sizes[f.lower()] = (os.path.getsize(os.path.join(d, f)), os.path.relpath(os.path.join(d, f), bundle))
seen = []
for line in open(out, errors='replace'):
    m = re.search(r'Loaded L"([^"]*)"', line)
    if m and 'dist\\\\MComix' in m.group(1):
        n = m.group(1).split('\\\\')[-1].lower()
        if n not in seen: seen.append(n)
tot = sum(sizes[n][0] for n in seen if n in sizes)
print(len(seen), 'bundle files loaded,', round(tot / 1e6, 1), 'MB of', round(sum(s for s, _ in sizes.values()) / 1e6, 1))
for n in sorted(seen, key=lambda n: -sizes.get(n, (0,))[0])[:int(sys.argv[3]) if len(sys.argv) > 3 else 40]:
    print('%9d %s' % sizes.get(n, (0, n)))
