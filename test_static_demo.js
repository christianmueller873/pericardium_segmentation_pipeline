const fs = require('fs');
const path = require('path');

const demoPath = path.join(__dirname, 'demo', 'index.html');
const manifestPath = path.join(__dirname, 'demo', 'precomputed', 'sample_manifest.json');
const html = fs.readFileSync(demoPath, 'utf8');
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

for (const id of [
  'select-fused', 'select-agent1', 'select-agent2', 'scan', 'overlay', 'slice',
  'tool-paint', 'tool-erase', 'tool-smooth', 'reset-slice',
]) {
  if (!html.includes(`id="${id}"`)) throw new Error(`Static demo is missing ${id}`);
}
if (!html.includes('SYNTHETIC DATA · NO LIVE INFERENCE')) {
  throw new Error('Static demo lacks its prominent synthetic-data notice');
}
if (/fetch\s*\(|XMLHttpRequest|\.nii(?:\.gz)?|\.dcm/i.test(html)) {
  throw new Error('Static demo unexpectedly references network or medical-image input');
}
if (manifest.contains_medical_data || manifest.contains_patient_data || manifest.contains_model_output) {
  throw new Error('Synthetic manifest contains an unsafe provenance claim');
}
if (manifest.accuracy_claim !== 'none') throw new Error('Synthetic demo claims accuracy');

console.log(JSON.stringify({
  status: 'PASS',
  sample: manifest.sample_id,
  dimensions: manifest.dimensions,
  outputs: manifest.outputs,
  containsMedicalData: manifest.contains_medical_data,
}, null, 2));
