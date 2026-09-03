const fs = require('fs');
const path = require('path');
const vm = require('vm');

const viewerPath = path.join(__dirname, 'ct_viewer.html');
const html = fs.readFileSync(viewerPath, 'utf8');
const match = html.match(/<script>([\s\S]*?)<\/script>/i);
if (!match) throw new Error('Viewer script block not found');
const declaredIds = new Set([...html.matchAll(/id="([^"]+)"/g)].map(result => result[1]));
const referencedIds = [...match[1].matchAll(/getElementById\(['"]([^'"]+)['"]\)/g)].map(result => result[1]);
const missingIds = [...new Set(referencedIds.filter(id => !declaredIds.has(id)))];
if (missingIds.length) throw new Error(`Missing DOM ids: ${missingIds.join(', ')}`);
if (!/id="brush-size"\s+min="5"/.test(html)) throw new Error('Brush minimum is not 5 px');
if (/btn-download-mask|Download Edited Mask|downloadEditedMask/.test(html)) {
  throw new Error('Edited-mask download UI or logic is still present');
}
for (const id of ['tool-smooth', 'tool-paint', 'tool-erase']) {
  if (!declaredIds.has(id)) throw new Error(`Missing mask-editing tool: ${id}`);
}
for (const id of ['output-fused', 'output-agent1', 'output-agent2']) {
  if (!declaredIds.has(id)) throw new Error(`Missing model-output selector: ${id}`);
}
if (!/fetch\(`\$\{API\}\/segment\/compare`/.test(html)) {
  throw new Error('Viewer does not request the comparison endpoint');
}

function classList() {
  const values = new Set();
  return {
    add: value => values.add(value),
    remove: value => values.delete(value),
    toggle: (value, force) => force ? values.add(value) : values.delete(value),
    contains: value => values.has(value),
  };
}

const elements = new Map();
function context2d() {
  return {
    createImageData: (width, height) => ({ data: new Uint8ClampedArray(width * height * 4) }),
    clearRect() {}, drawImage() {}, putImageData() {}, beginPath() {}, arc() {}, stroke() {}, fill() {},
    save() {}, restore() {}, setLineDash() {},
  };
}
function element(id) {
  if (!elements.has(id)) {
    const item = {
      id, value: '0', checked: false, disabled: false, textContent: '', innerHTML: '', className: '',
      style: {}, classList: classList(), addEventListener() {}, click() {},
    };
    if (id === 'canvas-ct' || id === 'canvas-overlay') {
      item.width = 128; item.height = 128;
      item.getContext = () => context2d();
      item.getBoundingClientRect = () => ({ left: 0, top: 0, width: 128, height: 128 });
    }
    elements.set(id, item);
  }
  return elements.get(id);
}

const sandbox = {
  console, Math, Map, Set, Uint8Array, Uint8ClampedArray, Float32Array, DataView,
  ArrayBuffer, Blob, Response, CompressionStream: global.CompressionStream,
  URL: { createObjectURL: () => 'blob:test', revokeObjectURL() {} },
  setTimeout: callback => callback(),
  alert() {},
  document: {
    body: { classList: classList() },
    getElementById: element,
    createElement: tag => tag === 'canvas'
      ? { width: 0, height: 0, getContext: () => context2d() }
      : { click() {}, style: {} },
  },
};
sandbox.window = { addEventListener() {} };

const context = vm.createContext(sandbox);
new vm.Script(match[1], { filename: 'ct_viewer.inline.js' }).runInContext(context);
element('brush-size').value = '34';
element('brush-strength').value = '75';

const comparison = vm.runInContext(`
  volShape = [4, 5, 2];
  const states = normalizeComparisonResponse({
    shape: [5, 4, 2],
    encoding: 'per-slice-foreground-rle-v1',
    outputs: {
      fused: { slices: { '0': { runs: [2, 3, 9, 2] } }, nonzero_voxels: 5 },
      agent1: { slices: { '0': { runs: [0, 2] } }, nonzero_voxels: 2 },
      agent2: { slices: { '1': { runs: [18, 2] } }, nonzero_voxels: 2 },
    },
  });
  comparisonStates = states;
  selectOutput('fused', false);
  ({
    fusedArea: Array.from(maskData.slices['0']).reduce((sum, value) => sum + value, 0),
    selected: selectedOutput,
    fusedEnabled: !outputFused.disabled,
    agent1Enabled: !outputAgent1.disabled,
    agent2Enabled: !outputAgent2.disabled,
  });
`, context);
if (comparison.fusedArea !== 5 || comparison.selected !== 'fused'
    || !comparison.fusedEnabled || !comparison.agent1Enabled || !comparison.agent2Enabled) {
  throw new Error(`Comparison-output test failed: ${JSON.stringify(comparison)}`);
}

vm.runInContext(`
  volShape = [128, 128, 1];
  currentZ = 0;
  const synthetic = new Uint8Array(128 * 128);
  for (let y = 0; y < 128; y++) {
    for (let x = 0; x < 128; x++) {
      if ((x - 60) ** 2 + (y - 64) ** 2 <= 30 ** 2) synthetic[y * 128 + x] = 1;
    }
  }
  for (let y = 61; y <= 67; y++) {
    for (let x = 89; x <= 112; x++) synthetic[y * 128 + x] = 1;
  }
  maskData = { shape: [128, 128, 1], slices: { '0': synthetic }, labels: [1] };
`, context);

const before = vm.runInContext(`Array.from(maskData.slices['0'])`, context);
const changed = vm.runInContext(`smoothMaskAt(99, 64)`, context);
const after = vm.runInContext(`Array.from(maskData.slices['0'])`, context);

const editing = vm.runInContext(`
  brushSize.value = '5';
  volShape = [64, 64, 2];
  currentZ = 1;
  maskData = { shape: [64, 64, 2], slices: {}, labels: [1] };
  activeTool = 'paint';
  const paintStarted = beginBrushStroke({ x: 20, y: 20 });
  endBrushStroke();
  const paintedCenter = maskData.slices['1'][20 * 64 + 20];
  const paintUndoWasCreated = undoStack.length === 1 && undoStack[0].existed === false;
  activeTool = 'erase';
  const eraseStarted = beginBrushStroke({ x: 20, y: 20 });
  endBrushStroke();
  const erasedCenter = maskData.slices['1'][20 * 64 + 20];
  ({ paintStarted, paintedCenter, paintUndoWasCreated, eraseStarted, erasedCenter });
`, context);
if (!editing.paintStarted || editing.paintedCenter !== 1 || !editing.paintUndoWasCreated) {
  throw new Error(`Painter test failed: ${JSON.stringify(editing)}`);
}
if (!editing.eraseStarted || editing.erasedCenter !== 0) {
  throw new Error(`Eraser test failed: ${JSON.stringify(editing)}`);
}

function area(mask) { return mask.reduce((sum, value) => sum + value, 0); }
function perimeter(mask) {
  let result = 0;
  for (let y = 0; y < 128; y++) for (let x = 0; x < 128; x++) {
    if (!mask[y * 128 + x]) continue;
    for (const [dx, dy] of [[1,0],[-1,0],[0,1],[0,-1]]) {
      const nx = x + dx, ny = y + dy;
      if (nx < 0 || nx >= 128 || ny < 0 || ny >= 128 || !mask[ny * 128 + nx]) result++;
    }
  }
  return result;
}
function components(mask) {
  const seen = new Uint8Array(mask.length);
  let count = 0;
  for (let start = 0; start < mask.length; start++) {
    if (!mask[start] || seen[start]) continue;
    count++;
    const queue = [start]; seen[start] = 1;
    while (queue.length) {
      const index = queue.pop(), x = index % 128, y = Math.floor(index / 128);
      for (const [dx, dy] of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]) {
        const nx = x + dx, ny = y + dy;
        if (nx < 0 || nx >= 128 || ny < 0 || ny >= 128) continue;
        const next = ny * 128 + nx;
        if (mask[next] && !seen[next]) { seen[next] = 1; queue.push(next); }
      }
    }
  }
  return count;
}

function changesOutsideBrush(first, second, cx, cy, radius) {
  let count = 0;
  for (let y = 0; y < 128; y++) for (let x = 0; x < 128; x++) {
    if ((x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2) continue;
    if (first[y * 128 + x] !== second[y * 128 + x]) count++;
  }
  return count;
}

const result = {
  changed,
  areaBefore: area(before),
  areaAfter: area(after),
  perimeterBefore: perimeter(before),
  perimeterAfter: perimeter(after),
  componentsAfter: components(after),
  changesOutsideBrush: changesOutsideBrush(before, after, 99, 64, 34),
};
if (result.changed <= 0) throw new Error(`Smoothing made no change: ${JSON.stringify(result)}`);
if (Math.abs(result.areaAfter - result.areaBefore) / result.areaBefore > 0.02) {
  throw new Error(`Smoothing changed area by more than 2%: ${JSON.stringify(result)}`);
}
if (result.perimeterAfter >= result.perimeterBefore) {
  throw new Error(`Smoothing did not reduce edge roughness: ${JSON.stringify(result)}`);
}
if (result.componentsAfter !== 1) {
  throw new Error(`Smoothing broke connectivity: ${JSON.stringify(result)}`);
}
if (result.changesOutsideBrush !== 0) {
  throw new Error(`Smoothing changed pixels outside the selected area: ${JSON.stringify(result)}`);
}
console.log(JSON.stringify({
  status: 'PASS',
  declaredDomIds: declaredIds.size,
  resolvedDomReferences: referencedIds.length,
  brushMinimum: 5,
  painterAndEraser: editing,
  ...result,
}, null, 2));
