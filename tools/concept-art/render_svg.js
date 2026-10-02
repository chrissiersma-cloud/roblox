// usage: node render_svg.js jobs.json   (jobs: [{ svg, png, w, h }]) - renders SVG drawings with Chromium.
const fs = require("fs");
const { chromium } = require("playwright");
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 800, height: 800 } });
  page.on("pageerror", e => console.log("pageerror:", e.message));
  for (const job of jobs) {
    await page.setViewportSize({ width: job.w, height: job.h });
    await page.setContent(`<!doctype html><html><body style="margin:0;background:transparent">${fs.readFileSync(job.svg, "utf8")}</body></html>`);
    await page.evaluate(() => document.fonts.ready);
    await (await page.$("svg")).screenshot({ path: job.png, omitBackground: true });
  }
  await browser.close();
})();
