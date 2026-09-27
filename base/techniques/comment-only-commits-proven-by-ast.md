---
type: Technique
title: "Comment-only commits, proven by AST"
tags: [testing]
generated: { by: mcomix-loop/claude, at: "2026-09-27T12:00:00Z" }
---

- A commit that only rewrites comments and docstrings is proven by parsing each changed module at HEAD and in the tree, blanking every docstring (the first `Expr` of a Module, ClassDef or FunctionDef body whose value is a str constant) and comparing `ast.dump()`; comments are not in the tree at all.  The script is in the commit messages of bc7fe9b8 and 378e6c6a's iteration: `git diff --name-only`, then `git show HEAD:<file>` against the file.
- Finding comments that narrate history rather than describe the code: `git grep -nE "\b(used to|This was|used to be|until now)\b" -- 'mcomix/*.py' 'mcomix/**/*.py'` (zsh: quote the pathspecs; `grep -r --include=*.py` fails on the unmatched glob).  At 44950202 it listed 40 lines; about half were history told as reason.  Keep a history that explains code which still exists because of it (a database migration step, a reader of an old file format).
