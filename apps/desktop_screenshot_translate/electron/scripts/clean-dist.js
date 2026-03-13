const fs = require('node:fs');
const path = require('node:path');

function resolveDistRoot() {
  return path.resolve(__dirname, '..', 'dist');
}

function main() {
  const distRoot = resolveDistRoot();
  if (fs.existsSync(distRoot)) {
    fs.rmSync(distRoot, { recursive: true, force: true });
    console.log(`[OK] removed ${distRoot}`);
  } else {
    console.log(`[OK] dist not present, nothing to clean: ${distRoot}`);
  }
}

main();
