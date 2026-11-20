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
// Everything that must not appear before a decision.
const revealTexts = dataset.well_proposals.flatMap(({ reveal }) =>
  [reveal.well_name, reveal.operator, reveal.discovery_name, reveal.field_name, String(reveal.year)].filter(Boolean),
);

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
    for (const secret of revealTexts) {
      // Whole words only: the decade "1990s" is allowed, the year 1990 is not.
      const pattern = new RegExp(`(^|\\W)${secret.replace(/[.*+?^${}()|[\]\\/]/g, "\\$&")}(\\W|$)`);
      assert.ok(!pattern.test(text), `"${secret}" shown before a decision`);
    }
    assert.ok(!/chance|probability/i.test(text), "a chance of success is shown");

    const drill = page.getByRole("button", { name: /^Drill/ });
    const drop = page.getByRole("button", { name: /^Drop/ });
    assert.ok(await drill.isDisabled(), "Drill is enabled before Confidence is set");
    assert.ok(await drop.isDisabled(), "Drop is enabled before Confidence is set");

    // Alternate between moving the slider and tapping it to keep 50%.
    const slider = page.getByTestId("confidence-slider");
    if (decisions % 2 === 0) await slider.fill("70");
    else await slider.click();
    await (decisions % 2 === 0 ? drill : drop).click();
    decisions++;

    await page.getByTestId("reveal").waitFor();
    assert.match(await page.getByTestId("budget-change").innerText(), /^[+−]?\d/);
    if (decisions % 2 === 0) assert.equal(await page.getByTestId("would-have").count(), 1);
    assert.ok(await credit.isVisible());
    await page.getByRole("button", { name: /Next Well Proposal|See your result/ }).click();
  }

  assert.ok(decisions >= 1 && decisions <= 10, `${decisions} decisions`);
  const result = await page.getByTestId("result").innerText();
  for (const label of ["Net budget", "Discoveries", "Dry wells drilled", "Dry wells avoided", "Discoveries missed"]) {
    assert.ok(result.includes(label), `result is missing ${label}`);
  }
  assert.ok(await credit.isVisible());
  await page.screenshot({ path: new URL("../dist/smoke-result.png", import.meta.url).pathname });
});
