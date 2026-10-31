// No third-party dependencies: uses globally installed TypeScript.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
let ts
try { ts = require(path.resolve(__dirname, '../../frontend/node_modules/typescript')) }
catch { ts = require('typescript') }

const file = path.resolve(__dirname, '../../frontend/src/pages/V2Preview.tsx')
const text = fs.readFileSync(file, 'utf8')
const start = text.indexOf('async function colorizeCachedThumbnail(')
const end = text.indexOf('\nfunction IconLabel(', start)
assert.ok(start >= 0 && end > start, 'colorization function found')
const result = ts.transpileModule(text.slice(start, end), {
  fileName: file, reportDiagnostics: true,
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS }
})
assert.equal(result.diagnostics.length, 0, 'TypeScript colorization parses')
const pixels = new Uint8ClampedArray([
  0, 0, 0, 60,       // thin black anti-aliased line
  0, 0, 0, 255,      // solid black line
  20, 130, 215, 99, // existing colorful pixel must survive
  0, 0, 0, 0        // transparent pixel unchanged
])
let written = null
class FakeImage {
  naturalWidth = 2
  naturalHeight = 2
  async decode() {}
}
const context = {
  drawImage() {},
  getImageData() { return { data: pixels } },
  putImageData(data) { written = data.data },
}
const canvas = {
  getContext() { return context },
  toDataURL() { return 'data:image/webp;base64,COLORED' },
}
const sandbox = {
  Image: FakeImage,
  document: { createElement() { return canvas } },
  console
}
const colorize = vm.runInNewContext(`${result.outputText}\ncolorizeCachedThumbnail`, sandbox)
colorize('data:image/webp;base64,ORIGINAL').then(output => {
  assert.equal(output, 'data:image/webp;base64,COLORED')
  assert.deepEqual(Array.from(written), [
    236, 208, 164, 168,
    236, 208, 164, 255,
    20, 130, 215, 99,
    0, 0, 0, 0
  ])
  console.log('CP1.4 thumbnail pixel smoke test: PASS')
}).catch(e => { console.error(e); process.exitCode = 1 })
