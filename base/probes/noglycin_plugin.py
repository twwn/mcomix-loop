"""pytest -p noglycin_plugin: every worker runs as on a tree without glycin."""
import unittest.mock

_patch = None


def pytest_configure(config):
    global _patch
    from mcomix import image_tools

    def no_glycin(*args):
        raise ValueError('Namespace Gly not available')
    _patch = unittest.mock.patch.object(image_tools, 'glycin', no_glycin)
    _patch.start()
