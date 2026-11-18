"""Profile MainWindow() construction as MainWindowTest builds it.

Copy to test/_prof_main_window.py and run under xvfb:
    python3 -m pytest test/_prof_main_window.py -q -s -p no:warnings
Prints the median of construction and of the first pump, then the
cProfile top by cumulative and by own time, over ROUNDS windows.
"""

import cProfile
import io
import os
import pstats
import statistics
import time

from mcomix import constants, icons, keybindings, main
from mcomix.preferences import prefs

from . import MComixTest, get_testfile_path, pump

ROUNDS = int(os.environ.get('ROUNDS', '20'))
OPEN = os.environ.get('OPEN', '1') == '1'


class Probe(MComixTest):

    def test_profile(self):
        for directory in (constants.CONFIG_DIR, constants.DATA_DIR,
                          constants.THUMBNAIL_PATH):
            os.makedirs(directory, exist_ok=True)
        prefs['show toolbar'] = True
        prefs['show menubar'] = True
        icons.load_icons()
        built, pumped = [], []
        profile = cProfile.Profile()
        for number in range(ROUNDS + 1):
            keybindings._manager = None
            path = (get_testfile_path('archives', '01-ZIP-Normal.zip')
                    if OPEN else None)
            if number:
                profile.enable()
            start = time.perf_counter()
            window = main.MainWindow(open_path=path)
            middle = time.perf_counter()
            if number:
                profile.disable()
            main.set_main_window(window)
            pump(2000)
            end = time.perf_counter()
            if number:
                built.append(middle - start)
                pumped.append(end - middle)
            window.terminate_program()
            window.destroy()
            main.set_main_window(None)
            pump(2000)
        print('\nbuilt median %.1f ms, pump median %.1f ms (%d rounds, open=%s)'
              % (1000 * statistics.median(built),
                 1000 * statistics.median(pumped), ROUNDS, OPEN))
        for key in ('cumulative', 'tottime'):
            out = io.StringIO()
            stats = pstats.Stats(profile, stream=out)
            stats.sort_stats(key).print_stats(35)
            print(out.getvalue())
