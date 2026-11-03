"""Fail when a PE file of the Windows bundle imports a DLL nothing provides.

Every .exe, .dll and .pyd under the bundle is read with pefile, its import
and delay-import tables both. An import is satisfied by a file of that name
anywhere in the bundle, by an API set (api-ms-win-*, ext-ms-win-*), or by a
DLL in the system folder that ships with Windows; names compare in lower
case, as Windows compares them. The Visual C++ runtimes are left out of the
system folder on purpose: the runner has them installed, a fresh Windows
does not.

Usage: python pe_imports.py <bundle> [<system folder>]
(the system folder defaults to %SystemRoot%\\System32). Exit status 1, with
each unresolved name and what imports it, when anything is left over.
Written for the release workflow's Windows job; proved on a Wine-built
bundle against Wine's system32 (2026-11-01, 63e5d0b1: 167 PE files, 145
names, none unresolved; libtiff-6.dll removed from a copy, 1 unresolved).
"""
import collections
import os
import re
import sys

import pefile

#: What the runner's System32 holds but a Windows without the Visual C++
#: redistributable lacks.
REDISTRIBUTABLE = re.compile(r'^(vcruntime|msvcp|msvcr\d|concrt|vcomp|vccorlib|mfc\d|d3dx|ucrtbased)')


def main(bundle: str, system: str) -> int:
    provided = set()
    count = 0
    importers = collections.defaultdict(set)
    for root, _dirs, files in os.walk(bundle):
        for name in files:
            if not name.lower().endswith(('.exe', '.dll', '.pyd')):
                continue
            provided.add(name.lower())
            count += 1
            path = os.path.join(root, name)
            pe = pefile.PE(path, fast_load=True)
            pe.parse_data_directories(directories=[
                pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],
                pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT']])
            for table in ('DIRECTORY_ENTRY_IMPORT', 'DIRECTORY_ENTRY_DELAY_IMPORT'):
                for entry in getattr(pe, table, ()):
                    importers[entry.dll.decode('ascii').lower()].add(os.path.relpath(path, bundle))
            pe.close()
    system_dlls = {name.lower() for name in os.listdir(system)
                   if not REDISTRIBUTABLE.match(name.lower())}
    unresolved = sorted(name for name in importers
                        if name not in provided and name not in system_dlls
                        and not name.startswith(('api-ms-win-', 'ext-ms-win-')))
    print('%d PE files import %d DLLs; %d unresolved' % (
        count, len(importers), len(unresolved)))
    for name in unresolved:
        print('::error::%s is imported by %s, and neither the bundle nor Windows has it'
              % (name, ', '.join(sorted(importers[name]))))
    return 1 if unresolved else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else
                  os.path.join(os.environ['SystemRoot'], 'System32')))
