"""Holds a thumbnail worker between delivering a thumbnail and taking the
order off its set, which is the window the floors job is suspected to meet."""
import time

from mcomix import thumbnail_list

_worker = thumbnail_list._ThumbnailViewBase._thumbnail_worker


def _slow(self, item):
    _worker(self, item)
    time.sleep(0.3)


thumbnail_list._ThumbnailViewBase._thumbnail_worker = _slow
