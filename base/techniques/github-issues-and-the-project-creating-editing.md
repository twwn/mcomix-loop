---
type: Technique
title: "GitHub issues and the project: creating, editing and closing them past the guard"
tags: [text]
sources:
  - { resource: "repo:.github/ISSUE_TEMPLATE" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-10-03T18:00:00Z" }
---

# GitHub issues and the project: creating, editing and closing them past the guard

The guard lets through `gh issue create|edit|comment|close|reopen --repo twwn/mcomix` and `gh project item-add|item-edit 1 --owner twwn`, the two `STATE/config.sh` names (`ISSUES_REPO`, `ISSUES_PROJECT`). The token needs the `project` scope for the second (`gh auth status` lists it among the token scopes since 2026-10-03).

- **The guard reads the command text, not what a script runs.** `--repo twwn/mcomix` has to be literal in the command: a `gh issue create` without it is refused ("name the repository"), even inside a heredoc or a `cat >` that only writes a file mentioning it. Write bodies with the Write tool rather than a heredoc in Bash when the body or a neighbouring line mentions a gh command.
- **A shell function with the literal flags works** for a batch, title and body file as arguments:
  `mk(){ url=$(gh issue create --repo twwn/mcomix --label enhancement --title "$2" --body-file "$I/$1.md") && gh project item-add 1 --owner twwn --url "$url" >/dev/null && echo "$1 $url"; }`
  `gh project item-add` prints the item id (`PVTI_...`), which nothing needs.
- **Labels** are read with `gh label list --repo twwn/mcomix` (refused before the guard was updated; corrected at d11add5a) or `gh api repos/twwn/mcomix/labels --jq '.[].name'`.
- **Closing with a commit**: `gh issue close <n> --repo twwn/mcomix --reason completed --comment "Done in <hash>."`. A hash not yet pushed is plain text until the user pushes; GitHub links it then.
- Items 35-47 were created at e09b3a74 as issues #29-#41, so issue = item - 6 still holds. The batch function took a third argument, the size, and ran `gh project item-edit 1 --owner twwn --url "$url" --field Size --value "$3"` right after the item-add: the new item is editable by URL at once.
- The feature list's items 7-34 (STATE/scratch/sf/features.md) were created at 2a144342 as issues #1-#28, in order: issue number = item - 6. Their bodies are the scratch files sf/issues/NN.md, which do not survive; the issues themselves are the record.
- **Editing an item's field by name** (at d11add5a): `gh project item-edit 1 --owner twwn --url https://github.com/twwn/mcomix/issues/<n> --field Size --value Small` (or `--field Status --value "In Progress"`) works; the guard refuses the id form below ("a node ID the guard cannot match"), which is kept only as a record of the ids. The Size field (created at d11add5a): `PVTSSF_lAHOAA2KGM4BlhNyzhkRaoQ`, Small `78df4b3c`, Medium `4d575a4f`, Large `b46bc01c`, Campaign `9cb1668a`. `gh project item-list 1 --owner twwn --format json -L 100 --jq '.items[] | "\(.content.number):\(.size)"'` reads every item's size.
- **Moving an item's Status by id** (refused by the guard since it was updated; corrected at d11add5a): project `PVT_kwHOAA2KGM4BlhNy`, field Status `PVTSSF_lAHOAA2KGM4BlhNyzhkNzTA`, options Todo `f75ad846`, In Progress `47fc9ee4`, Done `98236657`. The item id is what `gh project item-add` printed, or `gh project item-list 1 --owner twwn --format json --jq '.items[] | select(.content.number==N) | .id'`. Then `gh project item-edit --project-id PVT_kwHOAA2KGM4BlhNy --id <item> --field-id PVTSSF_lAHOAA2KGM4BlhNyzhkNzTA --single-select-option-id 47fc9ee4`. (Read at 252cc9e8 with `gh api graphql -f query='query{user(login:"twwn"){projectV2(number:1){id field(name:"Status"){... on ProjectV2SingleSelectField{id options{id name}}}}}}'`.)
- **The project's built-in workflows** (read with the graphql field `workflows{nodes{name enabled}}`): "Item added to project" sets Todo; "Item closed" sets Done (seen on #25 and #27); "Auto-close issue" closes an issue set to Done; "Auto-add sub-issues to project". "Auto-add to project" was missing until the user enabled it after 252cc9e8 (read at d11add5a, with the project public and a second view, "View 2", BOARD_LAYOUT, columns by Status); an issue a user files now enters the project by itself.
- Issue bodies are public: they carry no reference to the loop's own files (the "Item N of the loop's feature list" lines were taken out of #1-#28 at 252cc9e8).
