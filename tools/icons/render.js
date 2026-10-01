// usage: node render.js jobs.json
// jobs.json: [{ "svg": "in.svg", "png": "out.png", "size": 1024 }, ...]. Renders each SVG with Chromium.
const fs = require("fs");
const { chromium } = require("playwright");

(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1024, height: 1024 } });
  page.on("pageerror", e => console.log("pageerror:", e.message));
  for (const job of jobs) {
    const svg = fs.readFileSync(job.svg, "utf8");
    await page.setViewportSize({ width: job.size, height: job.size });
    await page.setContent(`<!doctype html><html><body style="margin:0;background:transparent">${svg}</body></html>`);
    await page.evaluate(() => document.fonts.ready);
    const el = await page.$("svg");
    await el.screenshot({ path: job.png, omitBackground: true });
  }
  await browser.close();
})();
