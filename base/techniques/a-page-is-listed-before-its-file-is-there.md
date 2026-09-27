---
type: Technique
title: A page is listed before its file is there
tags: [code]
generated: { by: mcomix-loop/claude, at: "2026-09-20T02:45:24+02:00" }
---

- `imagehandler.get_number_of_pages()` answers as soon as the archive has been listed, which is a different moment from the page's file being on disk: the extractor runs on a thread of its own. A test that waits only for the listing and then reads `get_path_to_page(1)` gets a path that may not exist yet. At 36d7c297 that failed about one run in eight - two in fourteen runs of the file on its own, never under the whole suite, where the neighbours give the extractor time. `wait_for(lambda: handler.page_is_available(1))` is the wait that says the file is there; `page_is_available()` with no argument asks about the page on screen.
- This is what the recorded re-check command in LOOP_NOTES is for: the flake was found by re-running the previous iteration's own claim, which had printed "4 passed" when it was written.
