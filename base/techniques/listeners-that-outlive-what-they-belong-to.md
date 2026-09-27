---
type: Technique
title: Listeners that outlive what they belong to
tags: [gtk]
sources:
  - { resource: "repo:mcomix/bookmark_dialog.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-20T07:08:04+02:00" }
---

- **A dialog subscribed with `+=` keeps running after it closes** unless it unsubscribes (before aa498a4f it was never collected at all). The handlers `connect()`ed to its own widgets hold the Python object, so the weak reference `callback.CallbackList` keeps to a bound method's object never dies, and a dialog that subscribed with `+=` and never `-=` goes on running for the rest of the session. 'destroy' never comes for the same reason; 'unrealize' does, and is where to unsubscribe (c9d0b9ce, efe3ebc5, fc1787da).
- **The sweep that finds a missing `-=`**: walk every `mcomix/**/*.py` with a regular expression for `<target>.<event> += ` and `-= `, count each event per file, and print the files where the two disagree. At d76e3177 that listed 29 events; all but one belong to an object that dies with the window (the menus, the thumbnail bar, the main window, the image handler) or are a plain `+=` on a string or a number (`name`, `_search_typed_so_far`, `current_size`). The one that mattered was `bookmark_dialog.py`, which subscribes to four callbacks of the store and unsubscribed from three - the fourth had been added one iteration earlier.
- **A test for this proves the handler did not run, not that nothing crashed.** Closing the dialog and asking the store to do the thing the handler answers must leave the dialog's own rows as they were; counting rows is not enough when the handler removes one and adds another, so compare what the rows hold.
- **Count what is still subscribed rather than guessing**: a `Callback`-decorated method becomes an instance attribute after the first `+=`, so `owner.__dict__.get('page_changed')` is the `CallbackList`, and `lst._CallbackList__callbacks` is a list of `(weakref or None, function)`. Resolve each weakref and count the ones that are instances of the dialog class, after opening and closing it twice and `gc.collect()`. Two per callback is the leak.
- **A regression test for such a leak patches a method the handler reaches through `self.` at call time** (`_update_image_page`, `_add_comment`, `get_command`, `histogram.draw_histogram`). Patching the subscribed method itself does nothing, because the list captured the plain function when it was subscribed. Check that the handler's own early returns do not stop it first: the library's cover view returns before `add_books()` unless a collection is selected, and the first version of its test passed on HEAD for that reason.
- **Sweep**: `git grep -n "+= self\._" -- 'mcomix/*.py'` beside `git grep -n "-= self\._"`. What subscribes to something that lives longer than itself (the window, the file or image handler, the library backend) needs a matching `-=`; menus and sidebars that live as long as the window do not.
