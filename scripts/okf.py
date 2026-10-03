#!/usr/bin/env python3
"""The loop's memory as an Open Knowledge Format (OKF v0.2) bundle.

The bundle root is the skill's state/ directory (base/ in the repository):

    index.md                  generated; okf_version
    notes.md                  type: Iteration Notes (rewritten every iteration)
    project.md                type: Installation (the user's)
    rejected.md               type: Rejection Register
    techniques/<slug>.md      type: Technique, sources: repo:<path> ...
    decisions/<date>-<slug>.md  type: Ruling, tags: [program] or [installation]
    probes/                   instruments the techniques name
    scratch/                  not part of the bundle

A source written `repo:<path>` is a file in the MComix checkout.

    okf.py list        techniques, one slug per line; [sources changed] where a
                       source file changed after the concept was last written
                       or verified, [source gone] where one no longer exists
    okf.py stale       the same, with the files that changed
    okf.py rulings     the rulings, one line each, for the prompt
    okf.py index       (re)write the index.md files
    okf.py check       conformance; exit 1 and name each problem
    okf.py state       what state.sh shows of the bundle, in one start-up:
                       index, list, the probes named but missing, problems
    okf.py ruling --tag program|installation --title T --text T [--by ACTOR]
                       record a ruling (a new file; rulings are never edited)
    okf.py verified <technique>...   the loop re-checked these (machine tier)
    okf.py confirm --as <id> <ruling>...   the user confirms (human tier);
                       the guard refuses this one inside the loop session

Stdlib only; the frontmatter is the small YAML subset these files use.
"""
import datetime as _dt
import os
import re
import subprocess
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(SKILL_DIR, 'state')
LOOP_ACTOR = 'mcomix-loop/claude'
RESERVED = ('index.md', 'log.md')
THEMES = [('testing', 'Running, testing, probing'), ('gtk', 'GTK and PyGObject'),
          ('code', 'The MComix code base'), ('windows', 'Windows'),
          ('text', 'Translations and documentation')]
RULING_TAGS = [('program', 'What MComix does'), ('installation', 'How this installation works')]


# ---------------------------------------------------------------- frontmatter
def _split_top(s, sep=','):
    out, depth, quote, cur = [], 0, None, ''
    for ch in s:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
            continue
        if ch in '"\'':
            quote = ch
        elif ch in '{[':
            depth += 1
        elif ch in '}]':
            depth -= 1
        elif ch == sep and depth == 0:
            out.append(cur.strip())
            cur = ''
            continue
        cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def _value(s):
    s = s.strip()
    if s.startswith('{') and s.endswith('}'):
        d = {}
        for part in _split_top(s[1:-1]):
            k, _, v = part.partition(':')
            d[k.strip()] = _value(v)
        return d
    if s.startswith('[') and s.endswith(']'):
        return [_value(p) for p in _split_top(s[1:-1])]
    if len(s) >= 2 and s[0] == s[-1] and s[0] in '"\'':
        return s[1:-1]
    return s


def parse(text):
    """(frontmatter dict or None, body, error or None)."""
    if not text.startswith('---\n'):
        return None, text, 'no frontmatter'
    end = text.find('\n---\n', 3)
    if end < 0:
        if text.endswith('\n---'):
            end = len(text) - 4
        else:
            return None, text, 'frontmatter not closed'
    fm, body = text[4:end], text[end + 5:]
    data, key = {}, None
    for n, line in enumerate(fm.split('\n'), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if line.startswith('  - ') or line.startswith('- '):
            if key is None or not isinstance(data.get(key), list):
                return None, body, f'frontmatter line {n}: list item without a key'
            data[key].append(_value(line.split('- ', 1)[1]))
            continue
        if line[0] in ' \t':
            return None, body, f'frontmatter line {n}: unexpected indentation'
        k, sep, v = line.partition(':')
        if not sep or not re.fullmatch(r'[A-Za-z_][\w-]*', k):
            return None, body, f'frontmatter line {n}: not "key: value"'
        key = k
        data[k] = _value(v) if v.strip() else []
    return data, body, None


def _q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"' if re.search(r'[:#{}\[\],&*!|>\'"%@`]', s) else s


def dump(data):
    lines = ['---']
    for k, v in data.items():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            lines.append(f'{k}:')
            for item in v:
                lines.append('  - { ' + ', '.join(f'{a}: {_q(str(b))}' for a, b in item.items()) + ' }')
        elif isinstance(v, list):
            lines.append(f'{k}: [' + ', '.join(_q(str(x)) for x in v) + ']')
        elif isinstance(v, dict):
            lines.append(f'{k}: {{ ' + ', '.join(f'{a}: {_q(str(b))}' for a, b in v.items()) + ' }')
        else:
            lines.append(f'{k}: {_q(str(v))}')
    lines.append('---')
    return '\n'.join(lines) + '\n'


# ---------------------------------------------------------------- helpers
def now_iso():
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def to_epoch(s):
    try:
        return _dt.datetime.fromisoformat(str(s).replace('Z', '+00:00')).timestamp()
    except ValueError:
        return None


def verifications(fm):
    v = fm.get('verified')
    if isinstance(v, dict):
        return [v]
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def last_written(fm):
    times = [to_epoch((fm.get('generated') or {}).get('at'))] if isinstance(fm.get('generated'), dict) else []
    times += [to_epoch(x.get('at')) for x in verifications(fm)]
    times = [t for t in times if t]
    return max(times) if times else None


def human_confirmed(fm):
    return any(str(x.get('by', '')).startswith('human:') for x in verifications(fm))


def concepts(state, sub):
    d = os.path.join(state, sub)
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        if name.endswith('.md') and name not in RESERVED:
            path = os.path.join(d, name)
            with open(path, encoding='utf-8') as f:
                fm, body, err = parse(f.read())
            out.append((name[:-3], path, fm or {}, body, err))
    return out


def repo_dir():
    for d in (os.environ.get('CLAUDE_PROJECT_DIR'), os.getcwd()):
        if not d:
            continue
        try:
            top = subprocess.run(['git', '-C', d, 'rev-parse', '--show-toplevel'], capture_output=True,
                                 text=True, check=True).stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        top = top.split('/.claude/worktrees/')[0]
        if os.path.isfile(os.path.join(top, 'mcomix', 'constants.py')):
            return top
    return None


def source_paths(fm):
    out = []
    for s in fm.get('sources') or []:
        r = s.get('resource', '') if isinstance(s, dict) else str(s)
        if r.startswith('repo:'):
            out.append(r[5:])
    return out


def staleness(state):
    """{slug: (changed paths, gone paths)} for techniques whose sources moved on."""
    repo = repo_dir()
    items = concepts(state, 'techniques')
    if not repo or not items:
        return {}
    wanted = {p for _, _, fm, _, _ in items for p in source_paths(fm)}
    if not wanted:
        return {}
    oldest = min((last_written(fm) or 0) for _, _, fm, _, _ in items)
    log = subprocess.run(['git', '-C', repo, 'log', f'--since=@{int(oldest)}', '--format=%x00%ct',
                          '--name-only', '--no-renames', 'HEAD'], capture_output=True, text=True).stdout
    latest, t = {}, 0
    for line in log.split('\n'):
        if line.startswith('\x00'):
            t = int(line[1:])
        elif line and line in wanted and line not in latest:
            latest[line] = t
    out = {}
    for slug, _, fm, _, _ in items:
        written = last_written(fm) or 0
        paths = source_paths(fm)
        changed = [p for p in paths if latest.get(p, 0) > written]
        gone = [p for p in paths if not os.path.exists(os.path.join(repo, p))]
        if changed or gone:
            out[slug] = (changed, gone)
    return out


# ---------------------------------------------------------------- commands
def cmd_list(state, items=None):
    stale = staleness(state)
    for slug, _, _, _, err in items if items is not None else concepts(state, 'techniques'):
        mark = ''
        if slug in stale:
            mark = ' [source gone]' if stale[slug][1] else ' [sources changed]'
        print(slug + mark + (' [bad frontmatter]' if err else ''))


def cmd_stale(state):
    for slug, (changed, gone) in sorted(staleness(state).items()):
        print(f'{slug}: ' + ', '.join([f'{p} changed' for p in changed] + [f'{p} gone' for p in gone]))


def cmd_rulings(state):
    items = concepts(state, 'decisions')
    if not items:
        print('(no rulings recorded)')
        return
    for tag, heading in RULING_TAGS:
        group = [c for c in items if tag in (c[2].get('tags') or [])]
        if not group:
            continue
        print(f'{heading}:')
        for slug, _, fm, body, _ in group:
            text = ' '.join(body.split())
            date = slug[:10] if re.match(r'\d{4}-\d{2}-\d{2}', slug) else ''
            flag = '' if human_confirmed(fm) else ' (unconfirmed)'
            print(f'- {date + ": " if date else ""}{text}{flag}')


def cmd_index(state, quiet=False):
    def write(path, text):
        old = open(path, encoding='utf-8').read() if os.path.exists(path) else None
        if old != text:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
    tech = concepts(state, 'techniques')
    rul = concepts(state, 'decisions')
    lines = ['# Techniques', '']
    for tag, heading in THEMES:
        group = [c for c in tech if tag in (c[2].get('tags') or [])]
        if group:
            lines += [f'## {heading}', ''] + [f'* [{c[2].get("title", c[0])}]({c[0]}.md)' for c in group] + ['']
    rest = [c for c in tech if not set(c[2].get('tags') or []) & {t for t, _ in THEMES}]
    if rest:
        lines += ['## Other', ''] + [f'* [{c[2].get("title", c[0])}]({c[0]}.md)' for c in rest] + ['']
    if tech:
        write(os.path.join(state, 'techniques', 'index.md'), '\n'.join(lines).rstrip() + '\n')
    lines = ['# Rulings', '']
    for tag, heading in RULING_TAGS:
        group = [c for c in rul if tag in (c[2].get('tags') or [])]
        if group:
            lines += [f'## {heading}', '']
            lines += [f'* [{c[2].get("title", c[0])}]({c[0]}.md) - '
                      f'{"confirmed" if human_confirmed(c[2]) else "unconfirmed"}' for c in group] + ['']
    if rul:
        write(os.path.join(state, 'decisions', 'index.md'), '\n'.join(lines).rstrip() + '\n')
    root = ['---', 'okf_version: "0.2"', '---', '', '# MComix loop knowledge', '',
            '* [Techniques](techniques/) - how to measure, test and probe the MComix GTK4 code base',
            '* [Rulings](decisions/) - the user\'s rulings: what MComix does, how this installation works',
            '* [Rejected](rejected.md) - what was examined and deliberately left alone, and why',
            '* [Installation](project.md) - the facts of one installation',
            '* [Notes](notes.md) - the loop\'s current handoff: iteration state, not knowledge', '',
            'A source written `repo:<path>` is a file in the MComix checkout '
            '(<https://github.com/twwn/mcomix>). Probes the techniques name are under `probes/`.', '']
    write(os.path.join(state, 'index.md'), '\n'.join(root))
    if not quiet:
        print(f'index: {len(tech)} techniques, {len(rul)} rulings')


def problems(state):
    problems = []
    for dirpath, dirnames, files in os.walk(state):
        rel = os.path.relpath(dirpath, state)
        if rel.split(os.sep)[0] in ('scratch', 'probes'):
            dirnames[:] = []
            continue
        for name in files:
            if not name.endswith('.md'):
                continue
            path = os.path.join(dirpath, name)
            relp = os.path.relpath(path, state)
            with open(path, encoding='utf-8') as f:
                text = f.read()
            if name in RESERVED:
                if name == 'index.md' and text.startswith('---\n') and relp != 'index.md':
                    problems.append(f'{relp}: only the bundle-root index.md may have frontmatter')
                continue
            fm, _, err = parse(text)
            if err:
                problems.append(f'{relp}: {err}')
                continue
            if not str(fm.get('type', '')).strip():
                problems.append(f'{relp}: no type')
            gen = fm.get('generated')
            if gen is not None and (not isinstance(gen, dict) or not gen.get('by')):
                problems.append(f'{relp}: generated needs {{ by, at }}')
            for k, v in [('generated.at', (gen or {}).get('at') if isinstance(gen, dict) else None)] + \
                    [('verified.at', x.get('at')) for x in verifications(fm)]:
                if v is not None and (to_epoch(v) is None or not re.search(r'(Z|[+-]\d\d:\d\d)$', str(v))):
                    problems.append(f'{relp}: {k} is not an ISO 8601 time with an offset: {v}')
            if relp.startswith('decisions' + os.sep):
                if fm.get('type') != 'Ruling':
                    problems.append(f'{relp}: type must be Ruling')
                if not set(fm.get('tags') or []) & {t for t, _ in RULING_TAGS}:
                    problems.append(f'{relp}: tags must include program or installation')
                if not isinstance(gen, dict):
                    problems.append(f'{relp}: a ruling records who wrote it down (generated)')
            if relp.startswith('techniques' + os.sep):
                if fm.get('type') != 'Technique' or not fm.get('title'):
                    problems.append(f'{relp}: needs type: Technique and a title')
                for s in fm.get('sources') or []:
                    r = s.get('resource', '') if isinstance(s, dict) else ''
                    if not re.match(r'(repo:|https?://|/|\.)', r):
                        problems.append(f'{relp}: source without a resource URI: {s}')
    return problems


def cmd_check(state):
    found = problems(state)
    for p in found:
        print(p)
    return 1 if found else 0


def cmd_state(state):
    cmd_index(state, quiet=True)
    items = concepts(state, 'techniques')
    if not items:
        print('MISSING')
    cmd_list(state, items)
    named = set()
    for _, path, _, _, _ in items:
        with open(path, encoding='utf-8') as f:
            named |= {m.rstrip('.') for m in re.findall(r'STATE/probes/[A-Za-z0-9_./-]+', f.read())}
    missing = sorted(p for p in named if not os.path.exists(os.path.join(state, p[len('STATE/'):])))
    if missing:
        print('probes named but not on disk (rebuild from the description before use): ' + ' '.join(missing))
    found = problems(state)
    if found:
        print('== bundle problems (fix before ending the iteration) ==')
        print('\n'.join(found))


def _slug(text, limit=48):
    s = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    if len(s) > limit:
        s = s[:limit].rsplit('-', 1)[0]
    return s


def cmd_ruling(state, args):
    import argparse
    ap = argparse.ArgumentParser(prog='okf.py ruling')
    ap.add_argument('--tag', required=True, choices=[t for t, _ in RULING_TAGS])
    ap.add_argument('--title', required=True)
    ap.add_argument('--text', required=True, help='the user\'s words in quotes, then what they mean')
    ap.add_argument('--by', default=LOOP_ACTOR)
    a = ap.parse_args(args)
    d = os.path.join(state, 'decisions')
    os.makedirs(d, exist_ok=True)
    stamp = now_iso()
    base = f'{stamp[:10]}-{_slug(a.title)}'
    path, n = os.path.join(d, base + '.md'), 2
    while os.path.exists(path):
        path, n = os.path.join(d, f'{base}-{n}.md'), n + 1
    fm = {'type': 'Ruling', 'title': a.title, 'tags': [a.tag], 'generated': {'by': a.by, 'at': stamp}}
    with open(path, 'x', encoding='utf-8') as f:
        f.write(dump(fm) + '\n' + ' '.join(a.text.split()) + '\n')
    cmd_index(state, quiet=True)
    print(path)


def _add_verification(paths, actor):
    stamp = now_iso()
    for path in paths:
        with open(path, encoding='utf-8') as f:
            fm, body, err = parse(f.read())
        if err:
            sys.exit(f'{path}: {err}')
        fm['verified'] = verifications(fm) + [{'by': actor, 'at': stamp}]
        with open(path, 'w', encoding='utf-8') as f:
            f.write(dump(fm) + body)
        print(f'{path}: verified by {actor}')


def main(argv):
    state = STATE
    if len(argv) > 2 and argv[1] == '--state':
        state, argv = argv[2], [argv[0]] + argv[3:]
    cmd = argv[1] if len(argv) > 1 else ''
    if cmd == 'list':
        cmd_list(state)
    elif cmd == 'stale':
        cmd_stale(state)
    elif cmd == 'rulings':
        cmd_rulings(state)
    elif cmd == 'index':
        cmd_index(state)
    elif cmd == 'check':
        return cmd_check(state)
    elif cmd == 'state':
        cmd_state(state)
    elif cmd == 'ruling':
        cmd_ruling(state, argv[2:])
    elif cmd == 'verified':
        paths = [p for p in argv[2:] if '/techniques/' in os.path.abspath(p)]
        if len(paths) != len(argv[2:]) or not paths:
            sys.exit('okf.py verified: technique files only (the loop does not confirm rulings)')
        _add_verification(paths, os.environ.get('OKF_ACTOR', LOOP_ACTOR))
    elif cmd == 'confirm':
        if len(argv) < 5 or argv[2] != '--as':
            sys.exit('usage: okf.py confirm --as <your id> <ruling file>...')
        _add_verification(argv[4:], f'human:{argv[3]}')
        cmd_index(state, quiet=True)
    else:
        print(__doc__.strip())
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
