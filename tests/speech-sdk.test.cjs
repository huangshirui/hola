const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8');

test('Azure Speech SDK is the browser speech recognition provider', () => {
  const html = read('dist/index.html');
  const adapter = read('dist/azure-speech-recognition.js');
  const worker = read('worker/index.js');
  const pkg = JSON.parse(read('package.json'));

  const sdkScript = '/vendor/microsoft.cognitiveservices.speech.sdk.bundle-min.js';
  const adapterScript = '/azure-speech-recognition.js';
  assert.ok(html.indexOf(sdkScript) >= 0);
  assert.ok(html.indexOf(adapterScript) > html.indexOf(sdkScript));
  assert.ok(html.indexOf('/app.js') > html.indexOf(adapterScript));

  assert.match(adapter, /SpeechConfig\.fromAuthorizationToken/);
  assert.match(adapter, /speechRecognitionLanguage = LANGUAGE/);
  assert.match(adapter, /window\.SpeechRecognition = AzureSpeechRecognition/);
  assert.match(adapter, /provider: 'azure-speech-sdk'/);
  assert.match(adapter, /const LANGUAGE = 'es-ES'/);
  assert.doesNotMatch(adapter, /new nativeRecognition/);

  assert.match(worker, /\/api\/speech\/token/);
  assert.equal(pkg.dependencies['microsoft-cognitiveservices-speech-sdk'], '1.52.0');
});
