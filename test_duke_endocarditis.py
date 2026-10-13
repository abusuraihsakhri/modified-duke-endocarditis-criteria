"""Regressions against the 2023 Duke-ISCVID classification combinations."""
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest
from duke_endocarditis import FIELDS, calculate_metrics, process_batch


def flags(**choices):
    return {f: choices.get(f, False) for f in FIELDS}


@pytest.mark.parametrize(('given', 'expected', 'basis'), [
    ({'definite_pathologic': True}, 'Definite', 'pathologic criterion'),
    ({'major_microbiologic': True, 'major_imaging': True}, 'Definite', 'at least 2 major criteria'),
    ({'major_microbiologic': True, 'major_surgical': True}, 'Definite', 'at least 2 major criteria'),
    ({'major_microbiologic': True, 'minor_predisposition': True, 'minor_fever': True, 'minor_vascular': True}, 'Definite', 'at least 1 major and 3 minor criteria'),
    ({'minor_predisposition': True, 'minor_fever': True, 'minor_vascular': True, 'minor_immunologic': True, 'minor_microbiologic': True}, 'Definite', 'at least 5 minor criteria'),
    ({'major_imaging': True, 'minor_fever': True}, 'Possible', 'at least 1 major and 1 minor criterion'),
    ({'minor_predisposition': True, 'minor_fever': True, 'minor_vascular': True}, 'Possible', 'at least 3 minor criteria'),
    ({'major_imaging': True}, 'Rejected', 'does not meet criteria for possible IE'),
    ({}, 'Rejected', 'does not meet criteria for possible IE'),
    ({'major_imaging': True, 'minor_fever': True, 'reject_alternative': True}, 'Rejected', 'reject_alternative'),
    ({'major_microbiologic': True, 'major_imaging': True, 'reject_short_therapy': True}, 'Rejected', 'reject_short_therapy'),
    ({'reject_negative_surgery': True}, 'Rejected', 'reject_negative_surgery'),
])
def test_published_rules(given, expected, basis):
    result = calculate_metrics(**flags(**given))
    assert (result['classification'], result['basis']) == (expected, basis)


@pytest.mark.parametrize('given', [
    {'major_microbiologic': True, 'minor_microbiologic': True},
    {'major_imaging': True, 'minor_imaging': True},
    {'major_imaging': True, 'major_surgical': True},
    {'major_surgical': True, 'definite_pathologic': True},
    {'definite_pathologic': True, 'reject_alternative': True},
])
def test_mutually_exclusive(given):
    with pytest.raises(ValueError):
        calculate_metrics(**flags(**given))


def test_requires_review_of_all_fields():
    with pytest.raises(ValueError, match='missing'):
        calculate_metrics(major_imaging=True)
    with pytest.raises(ValueError, match='unknown'):
        calculate_metrics(**flags(), mystery=True)
    with pytest.raises(ValueError, match='boolean'):
        calculate_metrics(**flags(major_imaging='maybe'))


def test_batch_export_and_rejects_invalid(tmp_path):
    source, target = tmp_path / 'cases.csv', tmp_path / 'results.csv'
    with source.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['case', *FIELDS])
        writer.writeheader()
        writer.writerow({'case': '=HYPERLINK("https://bad.example")', **flags(major_microbiologic=True, major_imaging=True)})
        writer.writerow({'case': 'case-2', **flags(minor_fever=True, minor_vascular=True, minor_predisposition=True)})
    assert process_batch(str(source), str(target)) == 2
    with target.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert rows[0]['classification'] == 'Definite'
    assert rows[1]['classification'] == 'Possible'
    assert rows[0]['case'].startswith("'=")
    with pytest.raises(ValueError, match='must differ'):
        process_batch(str(source), str(source))
    source.write_text('major_imaging\ntrue\n')
    with pytest.raises(ValueError, match='Missing CSV columns'):
        process_batch(str(source), str(target))


def test_single_cli(tmp_path):
    root = Path(__file__).parent
    proc = subprocess.run([sys.executable, str(root/'duke_endocarditis.py'), 'single', '--major-microbiologic', '--minor-fever'], capture_output=True, text=True, check=True)
    assert json.loads(proc.stdout)['classification'] == 'Possible'
