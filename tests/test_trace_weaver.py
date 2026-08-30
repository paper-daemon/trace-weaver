import unittest, tempfile, json
from pathlib import Path
from trace_weaver import load, analyze

class T(unittest.TestCase):
    def test_gap_retry_duplicate(self):
        p = Path(tempfile.mktemp())
        rows = [
            {'trace_id':'a','timestamp':0,'event':'start'},
            {'trace_id':'a','timestamp':50,'event':'retry attempt'},
            {'trace_id':'a','timestamp':50,'event':'retry attempt'},
        ]
        p.write_text('\n'.join(json.dumps(x) for x in rows))
        r = analyze(load(p)[0], 30)[0]
        self.assertEqual(r['gaps'], [50.0])
        self.assertEqual(len(r['duplicates']), 1)
        self.assertEqual(len(r['retries']), 2)

    def test_non_object_json_is_malformed(self):
        p = Path(tempfile.mktemp())
        p.write_text('{"trace_id":"a","timestamp":0}\n[1,2,3]\n"text"\n')
        rows, bad = load(p)
        self.assertEqual(len(rows), 1)
        self.assertEqual([x['line'] for x in bad], [2, 3])
        self.assertTrue(all('expected JSON object' in x['error'] for x in bad))

    def test_naive_iso_timestamp_is_utc(self):
        p = Path(tempfile.mktemp())
        p.write_text('\n'.join(json.dumps(x) for x in [
            {'trace_id':'a','timestamp':'2026-01-01T00:00:00'},
            {'trace_id':'a','timestamp':'2026-01-01T00:00:31Z'},
        ]))
        r = analyze(load(p)[0], 30)[0]
        self.assertEqual(r['gaps'], [31.0])

    def test_boolean_and_nonfinite_timestamps_are_not_treated_as_time(self):
        p = Path(tempfile.mktemp())
        p.write_text('\n'.join([
            '{"trace_id":"a","timestamp":true,"event":"bool"}',
            '{"trace_id":"a","timestamp":NaN,"event":"nan"}',
            '{"trace_id":"a","timestamp":10,"event":"real"}',
        ]))
        rows, bad = load(p)
        self.assertEqual(bad, [])
        r = analyze(rows, 0)[0]
        self.assertEqual(r['duration'], 0)
        self.assertEqual(r['gaps'], [])
