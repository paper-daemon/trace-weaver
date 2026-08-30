# Trace Weaver
JSONLログを trace/job/request 単位で束ね、**時間の穴・再試行シグナル・重複イベント・壊れた行**を1枚のHTMLにする無料OSS。

```bash
python trace_weaver.py app.jsonl --gap 30 --html report.html --json report.json
```
外部依存なし / Python 3.10+ / MIT。ログそのものを書き換えません。入力JSONL・HTML出力・JSON出力が同じ実体パスを指す場合は実行前に拒否し、元ログや別出力の上書きを防ぎます。

- BOOTH: https://amase-memo.booth.pm/items/8778523
- 作者サイト: https://paper-daemon.github.io/

## Distribution note

`VERSION` と同梱ZIPは安定版スナップショットです。`main` には次リリース向けの未リリース修正が先に入る場合があり、その差分は `CHANGELOG.md` の `Unreleased` に記録します。

## BOOTH
0円配布: https://amase-memo.booth.pm/items/8778523

## ID aliases

`trace_id` / `traceId`、`job_id` / `jobId`、`request_id` / `requestId`、`run_id` / `runId` は、それぞれ同じID familyとして束ねます。表記揺れで1本のtraceが分裂しません。異なるfamily同士は値が同じでも混ぜません。
