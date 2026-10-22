const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ts = require('typescript');
const source = ts.transpileModule(fs.readFileSync(require.resolve('../src/services/api.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
}).outputText;
function harness(response) {
  const state = { clicks: 0, objects: 0, cleared: 0, events: 0 };
  const anchor = { click() { state.clicks++; }, remove() {} };
  const context = { exports: {}, Uint8Array,
    localStorage: { getItem: () => 'session-token', removeItem: () => state.cleared++ },
    sessionStorage: { getItem: () => null, removeItem: () => state.cleared++ },
    window: { dispatchEvent: () => state.events++ }, CustomEvent: class {},
    fetch: async (url, options) => { state.headers = options.headers; return response; },
    URL: { createObjectURL() { state.objects++; return 'blob:zip'; }, revokeObjectURL() {} },
    document: { createElement: () => anchor, body: { appendChild() {} } }, setTimeout: fn => fn()
  };
  vm.runInNewContext(source, context);
  return { download: context.exports.downloadZip, suggested: context.exports.suggestedPackagePrefix, state, anchor };
}

test('numeric clients receive a valid suggested Java package', () => {
  const h = harness();
  assert.equal(h.suggested('pe.com.001'), 'pe.com.client_001');
  assert.equal(h.suggested('com.tcs.inventory'), 'com.tcs.inventory');
});
test('sends the session and downloads an actual ZIP with its filename', async () => {
  const h = harness(new Response(new Uint8Array([80,75,3,4,1]), { headers: { 'Content-Disposition': 'attachment; filename="project.zip"' } }));
  await h.download('/api/download');
  assert.equal(h.state.headers.Authorization, 'Bearer session-token');
  assert.equal(h.state.clicks, 1); assert.equal(h.anchor.download, 'project.zip');
});
test('surfaces generation errors instead of saving download.json', async () => {
  const h = harness(new Response(JSON.stringify({detail:'Generation has no files'}), {status:400}));
  await assert.rejects(h.download('/api/download'), /Generation has no files/);
  assert.equal(h.state.objects, 0); assert.equal(h.state.clicks, 0);
});
test('rejects JSON returned with an incorrect success status', async () => {
  const h = harness(new Response('{"error":"failure"}'));
  await assert.rejects(h.download('/api/download'), /ZIP válido/);
  assert.equal(h.state.clicks, 0);
});
test('expired sessions request sign in and never download an error', async () => {
  const h = harness(new Response('{"detail":"Expired session"}', {status:401}));
  await assert.rejects(h.download('/api/download'), /Expired session/);
  assert.equal(h.state.events, 1); assert.equal(h.state.clicks, 0);
});
