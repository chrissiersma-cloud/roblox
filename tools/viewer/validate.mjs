import validator from "gltf-validator";
import fs from "fs";
const dir = process.argv[2];
let bad = 0;
for (const f of fs.readdirSync(dir).filter(f => f.endsWith(".glb"))) {
  const r = await validator.validateBytes(new Uint8Array(fs.readFileSync(`${dir}/${f}`)));
  const { numErrors, numWarnings, numInfos } = r.issues;
  if (numErrors || numWarnings) {
    bad++;
    console.log(f, numErrors, "errors", numWarnings, "warnings");
    for (const m of r.issues.messages.slice(0, 5)) console.log("   ", m.severity, m.code, m.message, m.pointer);
  }
}
console.log(bad ? `${bad} files with issues` : "all files valid");
