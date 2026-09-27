// usage: node sceneshot.js <scene.json> <shot> <out.png> [w] [h]
const { chromium } = require("playwright");
(async () => {
  const [scene, shot, out, w = "1600", h = "900"] = process.argv.slice(2);
  const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const page = await browser.newPage({ viewport: { width: +w, height: +h } });
  page.on("console", m => { if (m.type() === "error") console.log("console:", m.text()); });
  page.on("pageerror", e => console.log("pageerror:", e.message));
  const t0 = Date.now();
  await page.goto(`http://127.0.0.1:8123/scene.html?scene=${scene}&shot=${shot}&w=${w}&h=${h}`);
  await page.waitForFunction(() => document.title === "done", null, { timeout: 600000 });
  await page.screenshot({ path: out });
  console.log(`${shot}: ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  await browser.close();
})();
