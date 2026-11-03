---
type: Technique
title: A slow cover - how to build one and time the wait
tags: [testing, code]
sources:
  - { resource: "repo:mcomix/thumbnail_list.py" }
  - { resource: "repo:mcomix/library/book_area.py" }
  - { resource: "repo:mcomix/worker_thread.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-11-03T13:23:41Z" }
---

- **A big solid archive is not slow by being big.**  `STATE/probes/mk_slow_covers.py <empty dir>` builds what is. Three first attempts read in under 170 ms: 430 MB of plain noise goes into stored LZMA2 chunks and comes out in 80 ms; `-ms=on -mx=1` split it into 7 blocks, of which only the last was decoded (check `Blocks =` in `7z l -slt`); and a cover first in the stream stops the decoder early (140 ms). What took 5.0 s: pages of six-bit noise, `-ms=1g -mx=5 -md=64m`, the cover last in the stream. It is the worst case, and made for the purpose: the numbers say so wherever they are quoted.
- **Time only the slow book's own read.**  `_OneBookTest` already holds a book, and wiping the covers has it read again. A wrapper of `get_book_thumbnail` that does not filter on the path fires on that small book first, and my first run reported reads of 2 to 13 ms beside blocks of 442 ms. The last row of a run can also be blocked by the previous book's second read: 4966 ms behind a PNG that takes 430 ms.
- **The two probes.**  `SLOW_DIR=<dir> BIG60=STATE/probes/big60.cbz sh STATE/scratch/sweep/threads/run.sh STATE/probes/test_zz_cover_block.py` prints the read and the block for each book. `STATE/probes/test_zz_cover_typing.py` has `-k typing`, eight `display_covers()` 200 ms apart with the worst stall, the reads started and how many ran at once, and `-k closing`, the join that is left. run.sh gives them 120 s.
- **Taking a join off the main thread: count the work as well as the stall.**  The stall went from 4770 ms to 2 ms with the join gone, and the same run showed 8 reads at once where there had been 1, since the join was also what had kept a book's next read behind its first. Timing the stall alone would have called that a fix. Now the later worker waits in `book_area._cover_of()` and finds the cover in the cache.
- **Leave a pool running rather than retire it.**  `WorkerThread.clear_orders()` takes the queue and leaves the uids of the orders in flight for `_run` to remove, so nothing raises KeyError and the pool stays at its size. `stop()` is the only thing that joins, and `_stop` is one flag shared by every thread and reset after the join, so a stop that does not join would need a flag per thread as well.
- **A test that the main thread did not wait.**  Park the worker on an event with a timeout (`go_on.wait(10)`), set a second event after it, and assert that second event is still clear when the call returns. With the join the call takes the whole timeout and the assertion fails; without it nothing depends on timing. `CoverInFlightTest` and `test_new_entries_do_not_wait_for_a_thumbnail_being_made` do this. To show that a second read does not start, `wait_for(lambda: len(reads) > 1, seconds=0.5)` first: asserting at once would pass with the bug, the second worker not having got there yet.
