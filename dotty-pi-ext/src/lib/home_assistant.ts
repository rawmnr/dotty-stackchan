import { readFileSync } from "node:fs";

export interface HomeAssistantOptions {
  baseUrl?: string;
  token?: string;
  timeoutMs?: number;
  configPath?: string;
  enabled?: boolean;
}

type ReadEntry = {
  type: "state";
  entity_id: string;
  label?: string;
};

type ActionEntry = {
  type: "service";
  domain: string;
  service: string;
  service_data?: Record<string, unknown>;
  label?: string;
};

type HAConfig = {
  reads?: Record<string, ReadEntry>;
  actions?: Record<string, ActionEntry>;
};

const DEFAULT_TIMEOUT_MS = Number(
  process.env.HOME_ASSISTANT_TIMEOUT_SECONDS
    ? Number(process.env.HOME_ASSISTANT_TIMEOUT_SECONDS) * 1000
    : 10000,
);
const DEFAULT_CONFIG_PATH = process.env.HOME_ASSISTANT_CONFIG_PATH ??
  "/root/.pi/home_assistant.json";

function envTrue(value: string | undefined): boolean {
  return /^(1|true|yes|on)$/i.test(value ?? "");
}

function trimSlash(url: string): string {
  return url.replace(/\/+$/, "");
}

function requireEnabled(opts: HomeAssistantOptions): void {
  const enabled = opts.enabled ?? envTrue(process.env.HOME_ASSISTANT_ENABLED);
  if (!enabled) {
    throw new Error("home_assistant_disabled");
  }
}

function resolveBaseUrl(opts: HomeAssistantOptions): string {
  const url = trimSlash(
    opts.baseUrl ??
      process.env.HOME_ASSISTANT_BASE_URL ??
      "",
  );
  if (!url) throw new Error("home_assistant_base_url_missing");
  return url;
}

function resolveToken(opts: HomeAssistantOptions): string {
  const token = (opts.token ?? process.env.HOME_ASSISTANT_TOKEN ?? "").trim();
  if (!token) throw new Error("home_assistant_token_missing");
  return token;
}

function resolveTimeoutMs(opts: HomeAssistantOptions): number {
  return opts.timeoutMs ?? DEFAULT_TIMEOUT_MS;
}

export function loadHomeAssistantConfig(
  opts: HomeAssistantOptions = {},
): HAConfig {
  const path = opts.configPath ?? DEFAULT_CONFIG_PATH;
  const raw = readFileSync(path, "utf8");
  const parsed = JSON.parse(raw) as HAConfig;
  return {
    reads: parsed.reads ?? {},
    actions: parsed.actions ?? {},
  };
}

async function haFetch(
  path: string,
  init: RequestInit,
  opts: HomeAssistantOptions = {},
): Promise<Response> {
  requireEnabled(opts);
  const baseUrl = resolveBaseUrl(opts);
  const token = resolveToken(opts);
  const timeoutMs = resolveTimeoutMs(opts);
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), timeoutMs);
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  headers.set("Content-Type", "application/json");
  try {
    return await fetch(`${baseUrl}${path}`, {
      ...init,
      headers,
      signal: ac.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

function logHa(message: string): void {
  process.stderr.write(`[home_assistant] ${message}\n`);
}

export async function readHomeAssistantItem(
  name: string,
  opts: HomeAssistantOptions = {},
): Promise<string> {
  const startedAt = Date.now();
  try {
    requireEnabled(opts);
    const cfg = loadHomeAssistantConfig(opts);
    const entry = cfg.reads?.[name];
    if (!entry) {
      return `(unknown Home Assistant read '${name}')`;
    }
    const resp = await haFetch(`/api/states/${entry.entity_id}`, { method: "GET" }, opts);
    const durationMs = Date.now() - startedAt;
    if (!resp.ok) {
      logHa(`kind=read name=${name} status=${resp.status} duration_ms=${durationMs}`);
      return `(Home Assistant read failed: HTTP ${resp.status})`;
    }
    const body = await resp.json() as {
      state?: unknown;
      attributes?: { friendly_name?: unknown; unit_of_measurement?: unknown };
    };
    const state = typeof body.state === "string" ? body.state : "unknown";
    const friendly = typeof body.attributes?.friendly_name === "string"
      ? body.attributes.friendly_name
      : (entry.label ?? name);
    const unit = typeof body.attributes?.unit_of_measurement === "string"
      ? ` ${body.attributes.unit_of_measurement}` : "";
    logHa(`kind=read name=${name} status=${resp.status} duration_ms=${durationMs}`);
    return `${friendly}: ${state}${unit}`.trim();
  } catch (err) {
    const durationMs = Date.now() - startedAt;
    logHa(
      `kind=read name=${name} status=error duration_ms=${durationMs} error=${String(err)}`,
    );
    return "(Home Assistant is unavailable right now)";
  }
}

export async function callHomeAssistantAction(
  name: string,
  opts: HomeAssistantOptions = {},
): Promise<string> {
  const startedAt = Date.now();
  try {
    requireEnabled(opts);
    const cfg = loadHomeAssistantConfig(opts);
    const entry = cfg.actions?.[name];
    if (!entry) {
      return `(unknown Home Assistant action '${name}')`;
    }
    const resp = await haFetch(
      `/api/services/${entry.domain}/${entry.service}`,
      {
        method: "POST",
        body: JSON.stringify(entry.service_data ?? {}),
      },
      opts,
    );
    const durationMs = Date.now() - startedAt;
    if (!resp.ok) {
      logHa(`kind=action name=${name} status=${resp.status} duration_ms=${durationMs}`);
      return `(Home Assistant action failed: HTTP ${resp.status})`;
    }
    logHa(`kind=action name=${name} status=${resp.status} duration_ms=${durationMs}`);
    return `Home Assistant action sent: ${entry.label ?? name}`;
  } catch (err) {
    const durationMs = Date.now() - startedAt;
    logHa(
      `kind=action name=${name} status=error duration_ms=${durationMs} error=${String(err)}`,
    );
    return "(Home Assistant action failed)";
  }
}
