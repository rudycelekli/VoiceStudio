import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
// Resolve the renderer's extensionless dependency without its bundler.
const moduleUrl = new URL('../../electron/src/shared/utils/longformParser.js', import.meta.url);
const dependencyUrl = new URL('../../electron/src/shared/utils/ssmlLite.js', import.meta.url);
const source = readFileSync(moduleUrl, 'utf8').replace("'./ssmlLite'", JSON.stringify(dependencyUrl.href));
const { parseScriptToSpans } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

const cases = JSON.parse(readFileSync(new URL('../fixtures/longform_parser_cases.json', import.meta.url), 'utf8'));
for (const item of cases) {
  test(`longform shared corpus: ${item.name}`, () => {
    assert.deepEqual(parseScriptToSpans(item.input, {
      defaultVoice: item.default_voice,
      defaultSpeed: item.default_speed ?? null,
    }), item.expected);
  });
}
