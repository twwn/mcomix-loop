---
type: Technique
title: "A collection's covers include the collections under it"
tags: [code]
sources:
  - { resource: "repo:test/test_collection_area.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-23T21:06:31+02:00" }
---

- `Collection.get_books()` returns the books of the collection and every collection under it, so anything that adds or removes covers while a collection is on show has to ask "is this collection within the one on show", not "is it the one on show": `LibraryBackend.collection_is_within(collection, ancestor)` (ancestor None or COLLECTION_ALL holds everything).  77c4fb7a fixed the new-book handler and the drag into a sub-collection. (Corrected at 72a28f86:) "Remove from this collection" keeps the cover of a book still under the collection on show (the `still_here` set in book_area), and since 72a28f86 so does a drag of books out of it onto another collection. Taking a book out of the collection on show does not take it out of the ones under it, so any "remove these covers" has to ask which books the collection still holds through get_books().
- A test that needs a real book row in this fixture inserts it into `book` and `contain` through `self.backend._con`, and sets `self.backend.book_added_to_collection = lambda *_args: None` before a drop: the fixture's `_Event` stub is not callable, and filing a book that exists fires it.
- test_collection_area.py's fixture files "Inner" under "Comics"; a drop on Inner needs `self.area._list.expand_to(self._collection_row( self.inner))` and a settle first, or `_middle_of()` finds no row.
