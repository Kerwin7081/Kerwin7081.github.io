import { mkdir } from "node:fs/promises";
import { spawn } from "node:child_process";
import path from "node:path";

const { chromium } = await import("playwright");

const root = process.cwd();
const artifactDir = path.join(root, "artifacts", "v3-preview");
await mkdir(artifactDir, { recursive: true });

const server = spawn(
  "python3",
  ["-m", "http.server", "4173", "--bind", "127.0.0.1", "--directory", root],
  { stdio: "ignore" },
);

async function waitForServer() {
  const url = "http://127.0.0.1:4173/";
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error("local preview server did not become ready");
}

const cases = [
  {
    id: "coinbase-light",
    path: "coinbase-new-positioning-everything-exchange-agentic-finance-20260731/",
    tables: true,
  },
  {
    id: "nvidia-dark",
    path: "nvidia-rubin-five-racks-sive-aaoi/",
    tables: true,
  },
  {
    id: "ai-supply-chain-table",
    path: "ai-supply-chain-power-bottlenecks-20260731/",
    tables: true,
  },
  {
    id: "xiaoxiao-interactive",
    path: "xiaoxiao-block-world/",
    interactive: true,
  },
  {
    id: "ineffable-migration-candidate",
    path: "ineffable-superlearner-rubin-a5x-20260723/",
    tables: true,
  },
];

const results = [];
const browser = await chromium.launch({ headless: true });

try {
  await waitForServer();

  for (const testCase of cases) {
    for (const viewport of [
      { width: 390, height: 844 },
      { width: 1440, height: 1000 },
    ]) {
      const context = await browser.newContext({
        viewport,
        deviceScaleFactor: 1,
        colorScheme: "light",
        isMobile: viewport.width === 390,
        hasTouch: viewport.width === 390,
      });
      const page = await context.newPage();
      const runtimeErrors = [];

      page.on("pageerror", (error) => runtimeErrors.push(error.message));
      page.on("console", (message) => {
        if (message.type() === "error") runtimeErrors.push(message.text());
      });

      await page.goto(`http://127.0.0.1:4173/${testCase.path}`, {
        waitUntil: "domcontentloaded",
        timeout: 30000,
      });
      await page.waitForTimeout(900);

      const gate = page
        .locator(".kw-access-gate input, #kw-access-key, #access-key, #gate-input")
        .first();
      if (await gate.count()) {
        await gate.fill("k");
        await page.waitForTimeout(320);
      }

      const state = await page.evaluate(() => {
        const html = document.documentElement;
        const body = document.body;
        const gates = [
          ...document.querySelectorAll(".kw-access-gate, .kw-editorial-gate, .access-gate"),
        ];
        const visibleGate = gates.some((node) => {
          const style = getComputedStyle(node);
          return (
            style.display !== "none" &&
            style.visibility !== "hidden" &&
            Number(style.opacity || 1) > 0.02
          );
        });
        return {
          width: html.clientWidth,
          scrollWidth: html.scrollWidth,
          visibleGate,
          v3ResearchShell: Boolean(document.querySelector(".kw-site-rail")),
          v3ExperienceShell: Boolean(
            document.querySelector(".kw-access-gate") &&
              body.classList.contains("kw-experience"),
          ),
          tables: document.querySelectorAll("table").length,
          interactive: document.querySelectorAll(
            "button, input, select, textarea, canvas, [role=button]",
          ).length,
          title: document.title,
        };
      });

      const failures = [];
      if (testCase.id !== "xiaoxiao-interactive" && !state.v3ResearchShell) {
        failures.push("v3 research shell missing");
      }
      if (testCase.id === "xiaoxiao-interactive" && !state.v3ExperienceShell) {
        failures.push("v3 experience shell missing");
      }
      if (state.visibleGate) failures.push("access gate still visible after k unlock");
      if (state.scrollWidth > state.width + 1) {
        failures.push(`horizontal overflow ${state.scrollWidth} > ${state.width}`);
      }
      if (testCase.tables && state.tables < 1) failures.push("expected table missing");
      if (testCase.interactive && state.interactive < 1) {
        failures.push("expected interactive control missing");
      }
      if (runtimeErrors.length) failures.push(...runtimeErrors.map((error) => `runtime: ${error}`));

      const suffix = `${viewport.width}`;
      await page.screenshot({
        path: path.join(artifactDir, `${testCase.id}-${suffix}.png`),
        fullPage: false,
      });
      results.push({
        id: testCase.id,
        viewport: `${viewport.width}x${viewport.height}`,
        state,
        failures,
      });
      await context.close();
    }
  }
} finally {
  await browser.close();
  server.kill("SIGTERM");
}

console.log(JSON.stringify(results, null, 2));
if (results.some((result) => result.failures.length)) process.exitCode = 1;
