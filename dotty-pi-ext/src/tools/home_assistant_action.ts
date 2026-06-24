import { Type } from "typebox";
import { callHomeAssistantAction } from "../lib/home_assistant.ts";

export const homeAssistantActionTool = {
  name: "home_assistant_action",
  label: "Home Assistant Action",
  description:
    "Trigger one allowlisted Home Assistant action by its configured name.",
  promptSnippet:
    "Trigger one allowlisted Home Assistant action such as night mode.",
  promptGuidelines: [
    "Use home_assistant_action only for explicitly requested Home Assistant actions that exist in the external allowlist.",
    "Pass the configured allowlist key in `name`, not a guessed service path.",
  ],
  parameters: Type.Object({
    name: Type.String({
      description: "Allowlisted Home Assistant action key from the external config file.",
    }),
  }),
  async execute(
    _toolCallId: string,
    params: { name: string },
    _signal: AbortSignal | undefined,
    _onUpdate: unknown,
    _ctx: unknown,
  ): Promise<{ content: Array<{ type: "text"; text: string }> }> {
    const text = await callHomeAssistantAction(params.name);
    return { content: [{ type: "text", text }] };
  },
};
