import unittest, tempfile, json
from pathlib import Path
from trace_weaver import load, analyze, validate_output_paths

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

    def test_snake_and_camel_case_id_aliases_share_one_trace(self):
        rows = [
            (1, {'trace_id':'same','timestamp':0,'event':'start'}),
            (2, {'traceId':'same','timestamp':40,'event':'retry'}),
        ]
        report = analyze(rows, 30)
        self.assertEqual(len(report), 1)
        self.assertEqual(report[0]['id'], 'trace_id:same')
        self.assertEqual(report[0]['events'], 2)
        self.assertEqual(report[0]['duration'], 40.0)
        self.assertEqual(report[0]['gaps'], [40.0])
        self.assertEqual(report[0]['retries'], [2])

    def test_same_value_in_different_id_families_stays_separate(self):
        report = analyze([
            (1, {'traceId':'same','timestamp':0}),
            (2, {'jobId':'same','timestamp':0}),
            (3, {'requestId':'same','timestamp':0}),
            (4, {'runId':'same','timestamp':0}),
        ], 30)
        self.assertEqual({r['id'] for r in report}, {'trace_id:same','job_id:same','request_id:same','run_id:same'})

    def test_output_paths_must_not_overwrite_input(self):
        p = Path(tempfile.mktemp())
        with self.assertRaises(ValueError):
            validate_output_paths(p, p)
        with self.assertRaises(ValueError):
            validate_output_paths(p, Path(tempfile.mktemp()), p)

    def test_html_and_json_outputs_must_be_distinct(self):
        src = Path(tempfile.mktemp())
        out = Path(tempfile.mktemp())
        with self.assertRaises(ValueError):
            validate_output_paths(src, out, out)
