// dotty-pi-ext — pi extension that exposes Dotty's voice tools.
// Loaded by the dotty-pi container's pi runtime via the extensions/
// bind-mount (see ../dotty-pi/README.md).
//
// This entry point is intentionally thin: it just registers tools. All
// behaviour lives in tools/* (testable in isolation) and lib/* (the
// underlying clients — sqlite for brain.db, fetch for xiaozhi admin,
// etc).

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { memoryLookupTool } from "./tools/memory_lookup.ts";
import { playSongTool } from "./tools/play_song.ts";
import { thinkHardTool } from "./tools/think_hard.ts";

export default function (pi: ExtensionAPI) {
  pi.registerTool(memoryLookupTool);
  pi.registerTool(thinkHardTool);
  pi.registerTool(playSongTool);
  // take_photo (blocked on perception-cache rehoming) and set_led
  // (not yet in bridge.py — per #36 carryover) land later.
}
