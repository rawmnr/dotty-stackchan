import { Type } from "typebox";
import { readHomeAssistantItem } from "../lib/home_assistant.ts";

export const homeAssistantReadTool = {
  name: "home_assistant_read",
  label: "Home Assistant Read",
  description:
    "Read an allowlisted Home Assistant sensor or status item by its configured name.",
  promptSnippet:
    "Read one allowlisted Home Assistant item such as office temperature or backup status.",
  promptGuidelines: [
    "Use home_assistant_read when the user asks for a sensor, status, or summary that is configured in Home Assistant.",
    "Pass the configured allowlist key in `name`, not a guessed entity_id.",
  ],
  parameters: Type.Object({
    name: Type.String({
      description: "Allowlisted Home Assistant read key from the external config file.",
    }),
  }),
  async execute(
    _toolCallId: string,
    params: { name: string },
    _signal: AbortSignal | undefined,
    _onUpdate: unknown,
    _ctx: unknown,
  ): Promise<{ content: Array<{ type: "text"; text: string }> }> {
    const text = await readHomeAssistantItem(params.name);
    return { content: [{ type: "text", text }] };
  },
};
