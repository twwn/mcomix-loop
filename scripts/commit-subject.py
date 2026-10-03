#!/usr/bin/env python3
"""The subject the `git commit` in a Bash command will give its commit.

    commit-subject.py <cwd> < command

Run by guard.sh before the command runs, so that commits.log can name the
loop's own commits. The subject is the first paragraph of the first -m, of
the -F file, or of the heredoc fed to -F -, joined as git's %s joins it.
A -F file the same command writes with a heredoc (`cat > msg <<EOF`) is read
from the heredoc; `$NAME` is resolved from assignments earlier in the
command, and from HOME.

Exit 0 and print the subject; exit 0 and print nothing when the commit
takes its message some other way (--no-edit, --fixup); exit 3 when it has
a -m or -F this cannot read before the command runs: a command
substitution, a variable it cannot resolve, or a file the command writes
some other way than a heredoc.
"""
import os
import re
import shlex
import subprocess
import sys

UNREADABLE = 3
HEREDOC = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_]\w*)\2")
SEPARATORS = {';', '&', '&&', '|', '||', '|&', ';;', '(', ')', '\n'}
GIT_OPTS_WITH_VALUE = {'-C', '-c', '--git-dir', '--work-tree', '--namespace', '--exec-path', '--super-prefix'}


class Unreadable(Exception):
    pass


def split_heredocs(raw):
    """(the command with every heredoc body taken out, the bodies in order)."""
    lines, code, bodies, i = raw.split('\n'), [], [], 0
    while i < len(lines):
        code.append(lines[i])
        ops = list(HEREDOC.finditer(lines[i]))
        i += 1
        for m in ops:
            body = []
            while i < len(lines):
                line = lines[i]
                i += 1
                if (line.lstrip('\t') if m.group(1) else line) == m.group(3):
                    break
                body.append(line)
            bodies.append('\n'.join(body) + '\n')
    return '\n'.join(code), bodies


def simple_commands(code, bodies):
    """[(tokens, its heredoc or None)], split at every separator; newlines outside quotes separate too."""
    lex = shlex.shlex(code, posix=True, punctuation_chars='();<>|&\n')
    lex.whitespace = ' \t\r'
    lex.whitespace_split = True
    out, cur, doc, n = [], [], None, 0
    for t in lex:
        if t in SEPARATORS:
            out.append((cur, doc))
            cur, doc = [], None
        elif t in ('<<', '<<-') or (t.startswith('<<') and set(t) <= set('<-')):
            doc = bodies[n] if n < len(bodies) else None
            n += 1
            cur.append(t)
        else:
            cur.append(t)
    out.append((cur, doc))
    return out


def subject(message):
    paras = re.split(r'\n\s*\n', message.strip('\n'))
    return ' '.join(paras[0].split()) if paras and paras[0].strip() else ''


def main():
    raw, cwd = sys.stdin.read(), sys.argv[1]
    code, bodies = split_heredocs(raw)
    try:
        commands = simple_commands(code, bodies)
    except ValueError:    # a quote left open: nothing can be told
        return UNREADABLE if re.search(r'\bcommit\b.*(-m|--message|-F|--file)', raw) else 0
    names = {'HOME': os.environ.get('HOME', '')}
    written = {}          # path -> the heredoc the command writes to it, or None for anything else

    def resolve(word):
        w = re.sub(r'\$\{(\w+)\}|\$(\w+)', lambda m: names.get(m.group(1) or m.group(2), '\0'), word)
        if '\0' in w or '$(' in w or '`' in w:
            raise Unreadable
        return w

    def path(word, base):
        w = resolve(word)
        if w == '~' or w.startswith('~/'):
            w = names['HOME'] + w[1:]
        return os.path.normpath(os.path.join(base, w))

    try:
        for toks, doc in commands:
            words = list(toks)
            while words and re.match(r'[A-Za-z_]\w*=', words[0]):    # NAME=value before a command, or alone
                name, _, value = words.pop(0).partition('=')
                try:
                    names[name] = resolve(value)
                except Unreadable:
                    names.pop(name, None)
            for k, t in enumerate(words):
                nxt = words[k + 1] if k + 1 < len(words) else ''
                if t in ('>', '>|', '&>', '>>') and nxt:
                    try:
                        p = path(nxt, cwd)
                    except Unreadable:
                        continue
                    if t == '>>' and os.path.isfile(p) and os.path.getsize(p):
                        continue        # appended to: its first paragraph stays what is on disk
                    written[p] = doc
            if words[:1] == ['tee']:
                for w in words[1:]:
                    if w.startswith('>') or w.startswith('<'):
                        break
                    if not w.startswith('-'):
                        try:
                            written[path(w, cwd)] = None
                        except Unreadable:
                            pass

            if not words or (words[0] != 'git' and not words[0].endswith('/git')):
                continue
            base, j = cwd, 1
            while j < len(words) and words[j].startswith('-'):
                if words[j] == '-C' and j + 1 < len(words):
                    base = path(words[j + 1], cwd)
                j += 2 if words[j] in GIT_OPTS_WITH_VALUE else 1
            if words[j:j + 1] != ['commit']:
                continue
            args = words[j + 1:]
            for i, a in enumerate(args):
                if a == '--':
                    break
                val = args[i + 1] if i + 1 < len(args) else None
                if a in ('-m', '--message') or a.startswith('--message=') or (a.startswith('-m') and not a.startswith('--')):
                    msg = val if a in ('-m', '--message') else a.split('=', 1)[1] if a.startswith('--') else a[2:]
                    if msg is None:
                        return UNREADABLE
                    print(subject(resolve(msg)))
                    return 0
                if a in ('-F', '--file') or a.startswith('--file=') or (a.startswith('-F') and len(a) > 2):
                    f = val if a in ('-F', '--file') else a[7:] if a.startswith('--file=') else a[2:]
                    if f == '-':
                        if doc is None:
                            return UNREADABLE
                        print(subject(doc))
                        return 0
                    if not f:
                        return UNREADABLE
                    p = path(f, base)
                    if p in written:
                        if written[p] is None:
                            return UNREADABLE
                        print(subject(written[p]))
                        return 0
                    try:
                        with open(p, encoding='utf-8', errors='replace') as fh:
                            print(subject(fh.read()))
                    except OSError:
                        return UNREADABLE
                    return 0
                if a in ('-C', '--reuse-message') or a.startswith('--reuse-message='):
                    rev = val if a in ('-C', '--reuse-message') else a.split('=', 1)[1]
                    out = subprocess.run(['git', '-C', base, 'log', '-1', '--format=%s', rev or 'HEAD'],
                                         capture_output=True, text=True)
                    print(out.stdout.strip() if out.returncode == 0 else '')
                    return 0
            return 0
    except Unreadable:
        return UNREADABLE
    return 0


if __name__ == '__main__':
    sys.exit(main())
