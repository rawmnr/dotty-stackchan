import {
  classifyToolRisk,
  decideToolUse,
  refusalText,
  withToolGuardrails,
} from "../src/lib/tool_guardrails.ts";

let failures = 0;
function assertEq(label: string, got: unknown, want: unknown): void {
  if (got !== want) {
    console.error(`FAIL ${label}: got ${JSON.stringify(got)}, want ${JSON.stringify(want)}`);
    failures++;
  } else {
    console.log(`ok - ${label}`);
  }
}

function assert(label: string, cond: boolean): void {
  if (!cond) {
    console.error(`FAIL ${label}`);
    failures++;
  } else {
    console.log(`ok - ${label}`);
  }
}

delete process.env.DOTTY_TOOL_ALLOWLIST;
delete process.env.DOTTY_TOOL_DENYLIST;
delete process.env.DOTTY_ALLOW_SENSITIVE_TOOLS;

assertEq("take_photo classified sensitive", classifyToolRisk("take_photo"), "sensitive_action");
assertEq("play_song classified safe", classifyToolRisk("play_song"), "safe_action");
assertEq("unknown classified blocked", classifyToolRisk("does_not_exist"), "blocked_action");

let d = decideToolUse("take_photo");
assertEq("sensitive denied by default", d.allowed, false);
assertEq("sensitive denial reason", d.reason, "sensitive_requires_confirmation_path");
assert("sensitive refusal mentions confirmation", refusalText("take_photo", d).includes("confirmation"));

process.env.DOTTY_ALLOW_SENSITIVE_TOOLS = "true";
d = decideToolUse("take_photo");
assertEq("sensitive can be explicitly enabled", d.allowed, true);
delete process.env.DOTTY_ALLOW_SENSITIVE_TOOLS;

process.env.DOTTY_TOOL_DENYLIST = "play_song";
d = decideToolUse("play_song");
assertEq("denylist blocks safe action", d.allowed, false);
assertEq("denylist reason", d.reason, "denylist");
delete process.env.DOTTY_TOOL_DENYLIST;

process.env.DOTTY_TOOL_ALLOWLIST = "memory_lookup,think_hard";
d = decideToolUse("play_song");
assertEq("allowlist blocks omitted tool", d.allowed, false);
assertEq("allowlist omission reason", d.reason, "not_in_allowlist");
d = decideToolUse("think_hard");
assertEq("allowlist keeps listed tool", d.allowed, true);
delete process.env.DOTTY_TOOL_ALLOWLIST;

let executed = false;
const wrapped = withToolGuardrails({
  name: "take_photo",
  async execute() {
    executed = true;
    return { content: [{ type: "text" as const, text: "ok" }] };
  },
});
const blockedResult = await wrapped.execute("tc-1", {}, undefined, undefined, undefined);
assertEq("wrapped sensitive tool returns one text item", blockedResult.content.length, 1);
assertEq("wrapped sensitive tool does not execute inner handler", executed, false);
assert("wrapped sensitive tool returns refusal text", blockedResult.content[0]!.text.includes("blocked"));

if (failures > 0) process.exit(1);
console.log("guardrails.test.ts passed");
