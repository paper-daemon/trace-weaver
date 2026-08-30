#!/usr/bin/env python3
import argparse, json, html, math
from pathlib import Path
from datetime import datetime, timezone

ID_ALIASES = (
    ('trace_id', ('trace_id','traceId')),
    ('job_id', ('job_id','jobId')),
    ('request_id', ('request_id','requestId')),
    ('run_id', ('run_id','runId')),
)

def pick_id(x):
    for canonical, aliases in ID_ALIASES:
        for k in aliases:
            if x.get(k) not in (None, ''):
                return f'{canonical}:{x[k]}'
    return 'unkeyed'

def parse_ts(x):
    for k in ('timestamp','time','ts','created_at','createdAt'):
        v = x.get(k)
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            value = float(v)
            return value if math.isfinite(value) else None
        if isinstance(v, str):
            try:
                dt = datetime.fromisoformat(v.replace('Z','+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except ValueError:
                pass
    return None

def load(path):
    rows, bad = [], []
    for n, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f'expected JSON object, got {type(obj).__name__}')
            rows.append((n, obj))
        except Exception as e:
            bad.append({'line': n, 'error': str(e)})
    return rows, bad

def validate_output_paths(input_path, html_path, json_path=None):
    paths = [('input', Path(input_path).resolve()), ('html', Path(html_path).resolve())]
    if json_path:
        paths.append(('json', Path(json_path).resolve()))
    seen = {}
    for label, path in paths:
        if path in seen:
            raise ValueError(f'{label} path must differ from {seen[path]} path: {path}')
        seen[path] = label

def analyze(rows, gap=30):
    groups = {}
    for n, x in rows:
        groups.setdefault(pick_id(x), []).append((n, x, parse_ts(x)))
    result = []
    for key, items in groups.items():
        items.sort(key=lambda z: (z[2] is None, z[2] or 0, z[0]))
        gaps, retries, dupes, seen, prev = [], [], [], set(), None
        for n, x, t in items:
            sig = json.dumps(x, sort_keys=True, ensure_ascii=False)
            if sig in seen:
                dupes.append(n)
            seen.add(sig)
            text = ' '.join(str(x.get(k,'')) for k in ('event','status','message','action')).lower()
            if any(w in text for w in ('retry','backoff','attempt')):
                retries.append(n)
            if prev is not None and t is not None and t - prev > gap:
                gaps.append(round(t - prev, 3))
            if t is not None:
                prev = t
        times = [z[2] for z in items if z[2] is not None]
        result.append({
            'id': key,
            'events': len(items),
            'duration': round(max(times)-min(times), 3) if len(times) > 1 else 0,
            'gaps': gaps,
            'retries': retries,
            'duplicates': dupes,
        })
    return sorted(result, key=lambda r: (
        len(r['gaps']) + len(r['duplicates']) + len(r['retries']), r['events']
    ), reverse=True)

def render(report, bad):
    rows = ''.join(
        f"<tr><td>{html.escape(r['id'])}</td><td>{r['events']}</td><td>{r['duration']}s</td>"
        f"<td>{len(r['retries'])}</td><td>{len(r['duplicates'])}</td>"
        f"<td>{', '.join(map(str,r['gaps'])) or '-'}</td></tr>"
        for r in report
    )
    return (
        '<!doctype html><meta charset="utf-8"><title>Trace Weaver report</title>'
        '<style>body{font:15px system-ui;background:#f3efe7;color:#222;max-width:1100px;margin:auto;padding:40px}'
        'table{width:100%;border-collapse:collapse;background:#fffaf2}th,td{padding:10px;border-bottom:1px solid #ddd;text-align:left}'
        'th{background:#e2e8da}</style>'
        f'<h1>Trace Weaver</h1><p>{len(report)} traces · {len(bad)} malformed lines</p>'
        '<table><tr><th>trace</th><th>events</th><th>duration</th><th>retry signals</th><th>duplicates</th><th>gaps</th></tr>'
        + rows + '</table>'
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('jsonl')
    ap.add_argument('--gap', type=float, default=30)
    ap.add_argument('--html', default='trace-weaver-report.html')
    ap.add_argument('--json')
    a = ap.parse_args()
    try:
        validate_output_paths(a.jsonl, a.html, a.json)
    except ValueError as e:
        ap.error(str(e))
    rows, bad = load(a.jsonl)
    report = analyze(rows, a.gap)
    Path(a.html).write_text(render(report, bad), encoding='utf-8')
    data = {'traces': report, 'malformed_lines': bad}
    if a.json:
        Path(a.json).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'traces={len(report)} malformed={len(bad)} html={a.html}')

if __name__ == '__main__':
    main()
