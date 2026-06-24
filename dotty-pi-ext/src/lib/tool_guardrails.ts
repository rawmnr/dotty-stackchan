export type ToolRisk =
  | "read_only"
  | "safe_action"
  | "sensitive_action"
  | "blocked_action";

export interface GuardrailDecision {
  risk: ToolRisk;
  allowed: boolean;
  reason: string;
}

const DEFAULT_RISK_BY_TOOL: Record<string, ToolRisk> = {
  memory_lookup: "read_only",
  recall_person: "read_only",
  think_hard: "read_only",
  play_song: "safe_action",
  remember: "safe_action",
  remember_person: "safe_action",
  take_photo: "sensitive_action",
};

function parseList(value: string | undefined): Set<string> {
  return new Set(
    (value ?? "")
      .split(",")
      .map((part) => part.trim())
      .filter(Boolean),
  );
}

function envTrue(value: string | undefined): boolean {
  return /^(1|true|yes|on)$/i.test(value ?? "");
}

export function classifyToolRisk(toolName: string): ToolRisk {
  return DEFAULT_RISK_BY_TOOL[toolName] ?? "blocked_action";
}

export function decideToolUse(toolName: string): GuardrailDecision {
  const risk = classifyToolRisk(toolName);
  const allowlist = parseList(process.env.DOTTY_TOOL_ALLOWLIST);
  const denylist = parseList(process.env.DOTTY_TOOL_DENYLIST);
  const allowSensitive = envTrue(process.env.DOTTY_ALLOW_SENSITIVE_TOOLS);

  if (denylist.has(toolName)) {
    return {
      risk,
      allowed: false,
      reason: "denylist",
    };
  }

  if (risk === "blocked_action") {
    return {
      risk,
      allowed: false,
      reason: "unclassified",
    };
  }

  if (allowlist.size > 0 && !allowlist.has(toolName)) {
    return {
      risk,
      allowed: false,
      reason: "not_in_allowlist",
    };
  }

  if (risk === "sensitive_action" && !allowSensitive) {
    return {
      risk,
      allowed: false,
      reason: "sensitive_requires_confirmation_path",
    };
  }

  return {
    risk,
    allowed: true,
    reason: "allowed",
  };
}

export function refusalText(toolName: string, decision: GuardrailDecision): string {
  if (decision.risk === "sensitive_action") {
    return `(${toolName} blocked: sensitive action requires explicit confirmation, and that confirmation path is not wired yet)`;
  }
  if (decision.reason === "denylist") {
    return `(${toolName} blocked by security policy)`;
  }
  return `(${toolName} blocked: action is not approved)`;
}

type TextResult = Promise<{ content: Array<{ type: "text"; text: string }> }>;

type ExecutableTool<P = unknown> = {
  name: string;
  execute: (
    toolCallId: string,
    params: P,
    signal: AbortSignal | undefined,
    onUpdate: unknown,
    ctx: unknown,
  ) => TextResult;
  [key: string]: unknown;
};

export function withToolGuardrails<P>(tool: ExecutableTool<P>): ExecutableTool<P> {
  return {
    ...tool,
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      const decision = decideToolUse(tool.name);
      process.stderr.write(
        `[guardrails] tool=${tool.name} risk=${decision.risk} allowed=${decision.allowed} reason=${decision.reason}\n`,
      );
      if (!decision.allowed) {
        return {
          content: [{ type: "text", text: refusalText(tool.name, decision) }],
        };
      }
      return await tool.execute(toolCallId, params, signal, onUpdate, ctx);
    },
  };
}
