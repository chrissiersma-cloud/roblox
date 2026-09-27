// usage: node shot.js "<query string>" out.png
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const page = await browser.newPage({ viewport: { width: 400, height: 400 } });
  page.on("console", m => { if (m.type() === "error") console.log("console:", m.text()); });
  page.on("pageerror", e => console.log("pageerror:", e.message));
  await page.goto("http://127.0.0.1:8123/index.html?" + process.argv[2]);
  await page.waitForFunction(() => document.title === "done", null, { timeout: 120000 });
  const size = await page.evaluate(() => [document.getElementById("c").width, document.getElementById("c").height]);
  await page.setViewportSize({ width: size[0], height: size[1] });
  await page.screenshot({ path: process.argv[3], clip: { x: 0, y: 0, width: size[0], height: size[1] } });
  await browser.close();
})();
