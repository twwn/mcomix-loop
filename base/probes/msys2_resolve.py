"""Resolve an MSYS2 package set from the repository database, as pacman
would, and list the package files to download."""
import io, re, sys, tarfile, subprocess

raw = subprocess.run(['zstd', '-dc', sys.argv[1]], capture_output=True, check=True).stdout
db = tarfile.open(fileobj=io.BytesIO(raw))
packages, provides = {}, {}
for member in db.getmembers():
    if not member.name.endswith('/desc'):
        continue
    text = db.extractfile(member).read().decode()
    fields = {}
    for block in text.strip().split('\n\n'):
        lines = block.split('\n')
        fields[lines[0].strip('%')] = lines[1:]
    name = fields['NAME'][0]
    packages[name] = fields
    for p in fields.get('PROVIDES', []):
        provides.setdefault(re.split('[<>=]', p)[0], name)

def resolve(dep):
    base = re.split('[<>=]', dep)[0]
    return base if base in packages else provides.get(base)

wanted = sys.argv[2:]
seen, order = set(), []
stack = list(wanted)
while stack:
    dep = stack.pop()
    name = resolve(dep)
    if name is None:
        print('MISSING', dep, file=sys.stderr); continue
    if name in seen: continue
    seen.add(name); order.append(name)
    stack.extend(packages[name].get('DEPENDS', []))
total = 0
for name in sorted(order):
    f = packages[name]
    total += int(f['CSIZE'][0])
    print(f['FILENAME'][0])
print(f'{len(order)} packages, {total/1e6:.0f} MB', file=sys.stderr)
