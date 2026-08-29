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
