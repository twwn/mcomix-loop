---
type: Technique
title: "GTK's renderer under Xvfb"
tags: [gtk]
sources:
  - { resource: "repo:test/__init__.py" }
generated: { by: mcomix-loop/claude, at: "2026-09-19T11:31:50+02:00" }
---

- **Xvfb has no DRI3, so GSK turns GL down (its GL is llvmpipe) and takes Vulkan** - on the machine's GPU where there is one (corrected: an earlier note said Vulkan ran in software; `GDK_DEBUG=vulkan` lists the device and GSK prints "Using Vulkan device 0"). `GSK_DEBUG=renderer` prints the choice; `window.get_native().get_renderer()` after a `present()` and a few turns of the main context names the class.
- **The cairo renderer is the faster one for the suite** (8.9-10.7 s against 14.7-17.6 s with Vulkan at 69c7a989). `test/__init__.py` sets cairo with `setdefault` since eb0657f0, so a renderer named in the environment still wins; a probe not built on `test/` should set it too, for speed and to stay clear of the Vulkan renderer's unrealize assertion. Check what hardware a library uses with its own debug output before writing it down.
