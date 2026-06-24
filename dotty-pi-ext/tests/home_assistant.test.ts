import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import {
  callHomeAssistantAction,
  loadHomeAssistantConfig,
  readHomeAssistantItem,
} from "../src/lib/home_assistant.ts";

let failures = 0;

function assertEq(label: string, actual: unknown, expected: unknown): void {
  const a = typeof actual === "string" ? actual : JSON.stringify(actual);
  const e = typeof expected === "string" ? expected : JSON.stringify(expected);
  if (a === e) {
    process.stdout.write(`  PASS  ${label}\n`);
    return;
  }
  process.stderr.write(
    `  FAIL  ${label}\n        expected: ${e}\n        actual:   ${a}\n`,
  );
  failures++;
}

interface MockRoute {
  match: (url: string, init?: RequestInit) => boolean;
  respond: () => { status: number; body: unknown } | Promise<{ status: number; body: unknown }>;
}

function installFetchRoutes(routes: MockRoute[]): () => void {
  const original = globalThis.fetch;
  globalThis.fetch = (async (url: any, init: any) => {
    const u = typeof url === "string" ? url : url.toString();
    for (const route of routes) {
      if (route.match(u, init)) {
        const { status, body } = await route.respond();
        return {
          ok: status >= 200 && status < 300,
          status,
          async json() {
            return body;
          },
          async text() {
            return typeof body === "string" ? body : JSON.stringify(body);
          },
        } as Response;
      }
    }
    throw new Error(`unmocked fetch: ${u}`);
  }) as typeof fetch;
  return () => {
    globalThis.fetch = original;
  };
}

function makeConfig(): { dir: string; path: string } {
  const dir = mkdtempSync(join(tmpdir(), "dotty-ha-"));
  const path = join(dir, "home_assistant.json");
  writeFileSync(
    path,
    JSON.stringify({
      reads: {
        office_temperature: {
          type: "state",
          entity_id: "sensor.office_temperature",
          label: "Office temperature",
        },
      },
      actions: {
        night_mode: {
          type: "service",
          domain: "script",
          service: "turn_on",
          service_data: { entity_id: "script.night_mode" },
          label: "Night mode",
        },
      },
    }),
    "utf8",
  );
  return { dir, path };
}

async function testConfigLoad(): Promise<void> {
  process.stdout.write("Config load:\n");
  const { dir, path } = makeConfig();
  try {
    const cfg = loadHomeAssistantConfig({ configPath: path });
    assertEq("reads loaded", Object.keys(cfg.reads ?? {}), ["office_temperature"]);
    assertEq("actions loaded", Object.keys(cfg.actions ?? {}), ["night_mode"]);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

async function testReadSuccess(): Promise<void> {
  process.stdout.write("\nRead success:\n");
  const { dir, path } = makeConfig();
  const restore = installFetchRoutes([
    {
      match: (u, init) =>
        u.endsWith("/api/states/sensor.office_temperature") && init?.method === "GET",
      respond: () => ({
        status: 200,
        body: {
          state: "23.5",
          attributes: {
            friendly_name: "Office temperature",
            unit_of_measurement: "°C",
          },
        },
      }),
    },
  ]);
  try {
    const got = await readHomeAssistantItem("office_temperature", {
      enabled: true,
      baseUrl: "http://ha.local:8123",
      token: "secret",
      configPath: path,
    });
    assertEq("read reply", got, "Office temperature: 23.5 °C");
  } finally {
    restore();
    rmSync(dir, { recursive: true, force: true });
  }
}

async function testReadUnknown(): Promise<void> {
  process.stdout.write("\nRead unknown key:\n");
  const { dir, path } = makeConfig();
  try {
    const got = await readHomeAssistantItem("missing", {
      enabled: true,
      baseUrl: "http://ha.local:8123",
      token: "secret",
      configPath: path,
    });
    assertEq("unknown read", got, "(unknown Home Assistant read 'missing')");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

async function testActionSuccess(): Promise<void> {
  process.stdout.write("\nAction success:\n");
  const { dir, path } = makeConfig();
  let postedBody: unknown;
  const restore = installFetchRoutes([
    {
      match: (u, init) =>
        u.endsWith("/api/services/script/turn_on") && init?.method === "POST",
      respond: async () => {
        postedBody = JSON.parse(String((globalThis as any).__lastBody ?? "{}"));
        return { status: 200, body: [] };
      },
    },
  ]);
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async (url: any, init: any) => {
    (globalThis as any).__lastBody = init?.body;
    return await originalFetch(url, init);
  }) as typeof fetch;
  try {
    const got = await callHomeAssistantAction("night_mode", {
      enabled: true,
      baseUrl: "http://ha.local:8123",
      token: "secret",
      configPath: path,
    });
    assertEq("action reply", got, "Home Assistant action sent: Night mode");
    assertEq("posted body", postedBody, { entity_id: "script.night_mode" });
  } finally {
    restore();
    globalThis.fetch = originalFetch;
    delete (globalThis as any).__lastBody;
    rmSync(dir, { recursive: true, force: true });
  }
}

async function testDisabledReply(): Promise<void> {
  process.stdout.write("\nDisabled integration:\n");
  const { dir, path } = makeConfig();
  try {
    const got = await readHomeAssistantItem("office_temperature", {
      enabled: false,
      configPath: path,
    });
    assertEq("disabled reply", got, "(Home Assistant is unavailable right now)");
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

async function main(): Promise<void> {
  await testConfigLoad();
  await testReadSuccess();
  await testReadUnknown();
  await testActionSuccess();
  await testDisabledReply();
  process.stdout.write(`\n${failures === 0 ? "OK" : "FAIL"} — ${failures} failure(s)\n`);
  process.exit(failures === 0 ? 0 : 1);
}

main();
