/** 2023 Duke-ISCVID classification combinations; clinical findings are pre-adjudicated. */
export const majorFields = ['major_microbiologic', 'major_imaging', 'major_surgical'];
export const minorFields = ['minor_predisposition', 'minor_fever', 'minor_vascular', 'minor_immunologic', 'minor_microbiologic', 'minor_imaging', 'minor_physical'];
export const rejectFields = ['reject_alternative', 'reject_short_therapy', 'reject_negative_surgery'];
export const fields = ['definite_pathologic', ...rejectFields, ...majorFields, ...minorFields];

export function calculateCriteria(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw Error('An object of reviewed criteria is required');
  const unknown = Object.keys(input).filter(k => !fields.includes(k));
  const missing = fields.filter(k => typeof input[k] !== 'boolean');
  if (unknown.length || missing.length) throw Error('Missing, unknown, or non-boolean criterion fields');
  if (input.major_microbiologic && input.minor_microbiologic) throw Error('Microbiology cannot count as both major and minor');
  if (input.major_imaging && input.minor_imaging) throw Error('Imaging cannot count as both major and minor');
  if (input.major_surgical && input.major_imaging) throw Error('Surgical major requires absence of major imaging');
  if (input.major_surgical && input.definite_pathologic) throw Error('Surgical major cannot coexist with pathologic confirmation');
  if (input.definite_pathologic && rejectFields.some(f => input[f])) throw Error('Pathologic confirmation conflicts with a rejection criterion');
  const major_count = majorFields.filter(f => input[f]).length;
  const minor_count = minorFields.filter(f => input[f]).length;
  const rejection = rejectFields.find(f => input[f]);
  let classification, basis;
  if (rejection) [classification, basis] = ['Rejected', rejection];
  else if (input.definite_pathologic) [classification, basis] = ['Definite', 'pathologic criterion'];
  else if (major_count >= 2) [classification, basis] = ['Definite', 'at least 2 major criteria'];
  else if (major_count >= 1 && minor_count >= 3) [classification, basis] = ['Definite', 'at least 1 major and 3 minor criteria'];
  else if (minor_count >= 5) [classification, basis] = ['Definite', 'at least 5 minor criteria'];
  else if (major_count >= 1 && minor_count >= 1) [classification, basis] = ['Possible', 'at least 1 major and 1 minor criterion'];
  else if (minor_count >= 3) [classification, basis] = ['Possible', 'at least 3 minor criteria'];
  else [classification, basis] = ['Rejected', 'does not meet criteria for possible IE'];
  return {
    criteria_version: '2023 Duke-ISCVID', classification, basis, major_count, minor_count,
    note: 'Criteria classification only; incomplete evaluation must not be used to rule out IE.'
  };
}

const form = typeof document === 'undefined' ? null : document.getElementById('criteria-form');
if (form) {
  const resultEl = document.getElementById('result');
  const dl = document.getElementById('download');
  let lastResult = null;
  function clearResult() {
    lastResult = null;
    resultEl.className = 'result empty';
    resultEl.textContent = 'No assessment yet. Review the evidence, confirm completion, and select Classify.';
    dl.disabled = true;
  }
  form.addEventListener('change', clearResult);
  form.addEventListener('reset', () => queueMicrotask(clearResult));
  form.addEventListener('submit', event => {
    event.preventDefault();
    if (!document.getElementById('reviewed').checked) {
      resultEl.className = 'result error';
      resultEl.textContent = 'Confirm that all 14 criterion domains have been reviewed.';
      return;
    }
    const input = Object.fromEntries(fields.map(f => [f, form.elements[f].checked]));
    try {
      lastResult = { ...calculateCriteria(input), criteria: input };
      resultEl.className = 'result ' + lastResult.classification.toLowerCase();
      const header = document.createElement('strong');
      header.textContent = lastResult.classification + ' infective endocarditis';
      const p = document.createElement('p');
      p.textContent = `Basis: ${lastResult.basis}. Major: ${lastResult.major_count}; minor: ${lastResult.minor_count}.`;
      const warning = document.createElement('p');
      warning.textContent = 'Not a diagnosis. “Rejected” based solely on unmet criteria does not exclude IE when investigations are incomplete.';
      resultEl.replaceChildren(header, p, warning);
      dl.disabled = false;
    } catch (error) {
      lastResult = null;
      dl.disabled = true;
      resultEl.className = 'result error';
      resultEl.textContent = error.message;
    }
  });
  dl.addEventListener('click', () => {
    if (!lastResult) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(lastResult, null, 2) + '\n'], { type: 'application/json' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'duke-iscvid-assessment.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  });
}
