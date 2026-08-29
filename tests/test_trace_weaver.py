import unittest,tempfile,json
from pathlib import Path
from trace_weaver import load,analyze
class T(unittest.TestCase):
 def test_gap_retry_duplicate(self):
  rows=[{'trace_id':'a','timestamp':0,'event':'start'},{'trace_id':'a','timestamp':50,'event':'retry attempt'},{'trace_id':'a','timestamp':50,'event':'retry attempt'}]
  p=Path(tempfile.mktemp()); p.write_text(chr(10).join(map(json.dumps,rows)))
  r=analyze(load(p)[0],30)[0]; self.assertEqual(r['gaps'],[50.0]); self.assertEqual(len(r['duplicates']),1); self.assertEqual(len(r['retries']),2)
