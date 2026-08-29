# Trace Weaver
JSONLログを trace/job/request 単位で束ね、**時間の穴・再試行シグナル・重複イベント・壊れた行**を1枚のHTMLにする無料OSS。

```bash
python trace_weaver.py app.jsonl --gap 30 --html report.html --json report.json
```
外部依存なし / Python 3.10+ / MIT。ログそのものを書き換えません。

- BOOTH: https://amase-memo.booth.pm/items/8778493
- 作者サイト: https://paper-daemon.github.io/
