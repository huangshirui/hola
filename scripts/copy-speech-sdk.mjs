import { copyFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';

const sourceDir = 'node_modules/microsoft-cognitiveservices-speech-sdk/distrib/browser';
const targetDir = 'dist/vendor';
const files = [
  'microsoft.cognitiveservices.speech.sdk.bundle-min.js',
  'speech-processor.js',
];

await mkdir(targetDir, { recursive: true });
for (const file of files) {
  await copyFile(join(sourceDir, file), join(targetDir, file));
}

console.log(`Copied Azure Speech SDK browser assets to ${targetDir}`);
