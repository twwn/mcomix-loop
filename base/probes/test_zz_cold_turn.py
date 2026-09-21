# Copy into <tree>/test/test_zz_cold_turn.py; run from the tree:
#   timeout -k 5 60 env -u WAYLAND_DISPLAY GDK_BACKEND=x11 xvfb-run -a \
#     python3 -m pytest test/test_zz_cold_turn.py -q -p no:cacheprovider -s | grep COLD
# Opens big60.cbz and, as soon as page 1 is on screen, jumps to a page
# far ahead that the extractor has not reached, timing how long that
# page takes to be available and how long page 1 took. Delete afterwards.
import os
import time

from . import MComixTest, pump, wait_for

from mcomix import constants, icons, main

BOOK = '~/.claude/skills/mcomix-loop/state/probes/big60.cbz'


class ColdTurn(MComixTest):

    def test_cold(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        icons.load_icons()
        start = time.perf_counter()
        window = main.MainWindow(open_path=BOOK)
        main.set_main_window(window)
        try:
            handler = window.imagehandler
            wait_for(lambda: handler.get_number_of_pages() == 60, seconds=20)
            wait_for(lambda: handler.page_is_available(1), seconds=20)
            first = time.perf_counter() - start
            for target in (50, 30, 58):
                available = sum(handler.page_is_available(n) for n in range(1, 61))
                begin = time.perf_counter()
                window.set_page(target)
                wait_for(lambda: handler.page_is_available(target), seconds=20)
                pump()
                print('COLD page %d after %.0f ms (%d of 60 extracted when asked)'
                      % (target, (time.perf_counter() - begin) * 1000, available))
            print('COLD first page after %.0f ms' % (first * 1000))
        finally:
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump()
