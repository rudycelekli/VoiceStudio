import assert from 'node:assert/strict';
import fs from 'node:fs';
import { test } from 'node:test';
import { parseSsmlLite } from '../../electron/src/shared/utils/ssmlLite.js';

// Resolve the renderer's bundler extensionless import; run its original code.
const source = fs.readFileSync(new URL('../../electron/src/shared/utils/longformParser.js', import.meta.url), 'utf8')
  .replace("'./ssmlLite'", JSON.stringify(new URL('../../electron/src/shared/utils/ssmlLite.js', import.meta.url).href));
const { parseScriptToSpans } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const cases = JSON.parse(fs.readFileSync(new URL('../fixtures/longform_parser_cases.json', import.meta.url), 'utf8'));

test('editor preserves the shared longform corpus including non-top and unmatched closes', () => {
  for (const c of cases) {
    assert.deepEqual(parseScriptToSpans(c.input, { defaultVoice: c.default_voice, defaultSpeed: c.default_speed }), c.expected, c.name);
  }
});

test('interleaved deeply nested text merges without changing its properties', () => {
  const depth = 4000;
  assert.deepEqual(parseSsmlLite('[slow]x'.repeat(depth) + '[/slow]'.repeat(depth)), [
    { text: 'x'.repeat(depth), speed: 0.85, spell: false, emphasis: false },
  ]);
});
