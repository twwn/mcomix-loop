"""pytest plugin: delay each archive member's extraction, to expose tests
that read a page before it is there."""
import time
from unittest import mock

def pytest_configure(config):
    from mcomix import archive_extractor
    orig = archive_extractor.Extractor._extract_file
    def slow(self, name):
        time.sleep(0.15)
        return orig(self, name)
    mock.patch.object(archive_extractor.Extractor, '_extract_file', slow).start()
