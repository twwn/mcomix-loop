# Copy into <tree>/test/test_zz_page_turn.py and run from the tree:
#   timeout -k 5 60 env -u WAYLAND_DISPLAY GDK_BACKEND=x11 xvfb-run -a \
#     python3 -m pytest test/test_zz_page_turn.py -q -p no:cacheprovider -s | grep -E "TURN|^ +[0-9]"
# Opens STATE/probes/big60.cbz (60 pages of 1200x1800 JPEG), waits until
# every page is extracted, then turns 30 pages one at a time, each
# drawn before the next, and prints the median wall time per turn and
# the top of a cProfile of the whole run by cumulative time.
# PROFILE=0 skips the profile (for timing alone). Delete afterwards.
import cProfile
import io
import os
import pstats
import statistics
import time

from . import MComixTest, pump, wait_for

from mcomix import constants, icons, main

BOOK = '~/.claude/skills/mcomix-loop/state/probes/big60.cbz'


class PageTurn(MComixTest):

    def test_turn(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        icons.load_icons()
        window = main.MainWindow(open_path=BOOK)
        main.set_main_window(window)
        try:
            window.set_default_size(1280, 900)
            window.present()
            handler = window.imagehandler
            wait_for(lambda: handler.get_number_of_pages() == 60, seconds=20)
            wait_for(lambda: all(handler.page_is_available(n)
                                 for n in range(1, 61)), seconds=30)
            pump()
            times = []
            profiling = os.environ.get('PROFILE', '1') == '1'
            profile = cProfile.Profile()
            if profiling:
                profile.enable()
            for _ in range(30):
                start = time.perf_counter()
                window.flip_page(1)
                wait_for(lambda: handler.page_is_available(), seconds=5)
                pump()
                times.append(time.perf_counter() - start)
            if profiling:
                profile.disable()
            print('TURN median %.1f ms, max %.1f ms over %d turns'
                  % (statistics.median(times) * 1000, max(times) * 1000,
                     len(times)))
            if profiling:
                # pstats refuses a profiler that never ran, so with
                # PROFILE=0 there is nothing to print.
                out = io.StringIO()
                pstats.Stats(profile, stream=out).sort_stats(
                    'cumulative').print_stats('mcomix', 25)
                print(out.getvalue())
        finally:
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump()
