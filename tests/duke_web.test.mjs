import test from 'node:test';
import assert from 'node:assert/strict';
import { calculateCriteria, fields } from '../web/app.mjs';
const flags = (...names) => Object.fromEntries(fields.map(f => [f, names.includes(f)]));
const cases = [
  [[], 'Rejected'],
  [['major_microbiologic'], 'Rejected'],
  [['minor_predisposition', 'minor_fever', 'minor_vascular'], 'Possible'],
  [['major_imaging', 'minor_fever'], 'Possible'],
  [['major_microbiologic', 'major_imaging'], 'Definite'],
  [['definite_pathologic'], 'Definite'],
  [['major_microbiologic', 'minor_fever', 'minor_immunologic', 'minor_vascular'], 'Definite'],
  [['minor_predisposition','minor_fever','minor_vascular','minor_immunologic','minor_microbiologic'], 'Definite'],
  [['major_microbiologic','major_imaging','reject_alternative'], 'Rejected'],
];
for(const [present, expected] of cases) test(`criteria: ${present.join(',') || 'none'}`, () => assert.equal(calculateCriteria(flags(...present)).classification, expected));
for(const present of [['major_imaging','minor_imaging'],['major_microbiologic','minor_microbiologic'],['major_imaging','major_surgical'],['definite_pathologic','reject_short_therapy']]) test('conflicting: '+present.join(','), () => assert.throws(() => calculateCriteria(flags(...present))));
test('invalid field', () => assert.throws(() => calculateCriteria({...flags(), extra:true})));
test('missing field', () => assert.throws(() => calculateCriteria({major_imaging:true})));
