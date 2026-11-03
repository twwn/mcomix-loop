---
type: Technique
title: "Archive member dates: 7z prints UTC with today's offset"
tags: [code]
sources:
  - { resource: "repo:mcomix/archive/archive_base.py" }
  - { resource: "repo:mcomix/archive/sevenzip_external.py" }
  - { resource: "repo:mcomix/archive/rar_external.py" }
generated: { by: mcomix-loop/claude-opus-5-5, at: "2026-11-02T22:40:00Z" }
---

- (at 45347886) **An unpacked page carries no date of its own**: probed handler by handler, the extracted file's mtime is the extraction time for zipfile, tarfile and 7z; only the UnRAR library sets the member's date. A page's date has to come from the listing, through `member_date()`.
- **Where each format keeps it**: zip `ZipInfo.date_time` (local wall time, no zone); tar `TarInfo.mtime` (UTC epoch); UnRAR library `RARHeaderDataEx.FileTime` (DOS packed, local, two-second steps); `unrar vt` prints `mtime: 2011-01-07 14:01:41,000000000` (to the second); `7z l -slt` prints `Modified = 2011-01-07 14:58:31.0000000`. `lha lq2` prints `Apr 12  2015`, or `Nov  2 21:20` for a recent file, with no year; `unzip -ZT` prints `20261005.134510` (corrected at 7ea5ef1e: neither was read for dates before it).
- **7z prints a UTC-kept time moved by the offset in force today**, not the one on that date: the fixture 04-7Z-Normal.7z's 12:58:31 UTC came out 14:58:31 in October (CEST) where tarfile gives 13:58:31 CET. Only zip (local time) is printed as stored. `archive_base.today_shifted_timestamp()` undoes it (`calendar.timegm(shown) - time.localtime().tm_gmtoff`). A RAR4 or LHA level 0/1 read through 7z keeps local time and is then up to an hour off in the other direction; 7z is their last resort.
- **Check**: the same picture is in 01-ZIP-Normal.zip, 02-TAR-Normal.tar and 04-7Z-Normal.7z; all three handlers, and 7z over each, should agree (test/test_member_dates.py). The test only bites while the machine's current offset differs from the one on 2011-01-07 (it does in summer time).
