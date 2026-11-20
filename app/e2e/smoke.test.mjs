// Smoke test: drives the built app in a headless browser through one full
// Campaign. Run with `npm run test:smoke`, which builds the app first.

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { after, before, test } from "node:test";
import { preview } from "vite";

// Playwright is installed globally in this environment, not as a dependency.
const { chromium } = createRequire(import.meta.url)("playwright");

const dataset = JSON.parse(await readFile(new URL("../dist/well_proposals.json", import.meta.url), "utf8"));
const byWellName = new Map(dataset.well_proposals.map((p) => [p.reveal.well_name, p]));

// Every well name, operator and year in the dataset: none may appear in any
// Dossier.
const neverBeforeADecision = dataset.well_proposals.flatMap(({ reveal }) =>
  [reveal.well_name, reveal.operator, String(reveal.year)].filter(Boolean),
);

// A well's own discovery and field: checked once the Reveal says which well
// it was, ignoring geological units. As in the pipeline's leak validator,
// "HOD FM" is not a leak of the HOD field: the formation is older than the
// well. Keep in step with _GEOLOGICAL_UNIT in
// pipeline/src/wildcat_pipeline/leaks.py.
function ownDiscoveryAndField({ reveal }) {
  return [reveal.discovery_name, reveal.field_name].filter(Boolean);
}

function withoutGeologicalUnits(text) {
  return text.replace(/[\w-]+\s+(?:fm|formation|gp|group)\b/gi, " ");
}

// Whole words only, as in the leak validator: the decade "1990s" is allowed,
// the year 1990 is not, and 2/4-3 is not inside 12/4-31.
function assertNotShown(secrets, text) {
  for (const secret of secrets) {
    const pattern = new RegExp(`(?<![\\w/-])${secret.replace(/[.*+?^${}()|[\]\\/]/g, "\\$&")}(?![\\w/-])`, "i");
    assert.ok(!pattern.test(text), `"${secret}" shown before a decision`);
  }
}

let server;
let browser;

before(async () => {
  server = await preview({ preview: { port: 0, host: "127.0.0.1" }, logLevel: "silent" });
  browser = await chromium.launch();
});

after(async () => {
  await browser?.close();
  await server?.close();
});

test("shows each Well Proposal's summary in its Dossier", async () => {
  // The shipped dataset may have been built without summaries, so this test
  // gives every Well Proposal one of its own.
  const withSummaries = {
    ...dataset,
    well_proposals: dataset.well_proposals.map((p) => ({
      ...p,
      dossier: { ...p.dossier, summary: `A structure in block ${p.dossier.block}, drilled in the ${p.dossier.decade}.` },
    })),
  };
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await page.route("**/well_proposals.json", (route) => route.fulfill({ json: withSummaries }));
  await page.goto(server.resolvedUrls.local[0]);

  await page.getByTestId("dossier").waitFor();
  const shown = await page.getByTestId("dossier-summary").innerText();
  const summaries = new Set(withSummaries.well_proposals.map((p) => p.dossier.summary));
  assert.ok(summaries.has(shown), `the Dossier shows "${shown}", which is no summary in the dataset`);
  await page.close();
});

test("plays one full Campaign without showing Reveal data before a decision", async () => {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await page.goto(server.resolvedUrls.local[0]);

  const credit = page.getByTestId("sodir-credit");
  await credit.waitFor();
  assert.match(await credit.innerText(), /Sodir/);
  assert.match(await credit.innerText(), /NLOD/);
  assert.equal(await page.getByTestId("budget").innerText(), "500");

  let decisions = 0;
  while (!(await page.getByTestId("result").isVisible())) {
    await page.getByTestId("dossier").waitFor();
    assert.equal(await page.getByTestId("reveal").count(), 0);
    const text = await page.locator("body").innerText();
    assertNotShown(neverBeforeADecision, text);
    assert.ok(!/chance|probability/i.test(text), "a chance of success is shown");
    const summary = page.getByTestId("dossier-summary");
    const shownSummary = (await summary.count()) ? await summary.innerText() : "";

    const drill = page.getByRole("button", { name: /^Drill/ });
    const drop = page.getByRole("button", { name: /^Drop/ });
    assert.ok(await drill.isDisabled(), "Drill is enabled before Confidence is set");
    assert.ok(await drop.isDisabled(), "Drop is enabled before Confidence is set");

    // Alternate between moving the slider and tapping it to keep 50%.
    const slider = page.getByTestId("confidence-slider");
    if (decisions % 2 === 0) await slider.fill("70");
    else await slider.click();
    // Drill once and Drop the rest, so the budget always lasts all 10.
    const drilling = decisions === 0;
    await (drilling ? drill : drop).click();
    decisions++;

    await page.getByTestId("reveal").waitFor();
    const wellName = await page.getByTestId("reveal-well-name").innerText();
    const shown = byWellName.get(wellName);
    assert.ok(shown, `the Reveal names ${wellName}, which is not in the dataset`);
    assertNotShown(ownDiscoveryAndField(shown), withoutGeologicalUnits(text));
    assert.equal(shownSummary, shown.dossier.summary, "the Dossier does not show its summary");
    assert.match(await page.getByTestId("budget-change").innerText(), /^[+−]?\d/);
    assert.equal(await page.getByTestId("would-have").count(), drilling ? 0 : 1);
    assert.ok(await credit.isVisible());
    await page.getByRole("button", { name: /Next Well Proposal|See your result/ }).click();
  }

  assert.equal(decisions, 10);
  const result = await page.getByTestId("result").innerText();
  for (const label of ["Net budget", "Discoveries", "Dry wells drilled", "Dry wells avoided", "Discoveries missed"]) {
    assert.ok(result.includes(label), `result is missing ${label}`);
  }
  assert.ok(await credit.isVisible());
  await page.screenshot({ path: new URL("../dist/smoke-result.png", import.meta.url).pathname });
});
