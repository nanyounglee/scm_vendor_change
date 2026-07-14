#!/usr/bin/env python3
"""
bank/reports.json 을 갱신하고, index.html 의 EMBEDDED_REPORTS 스냅샷을 재생성합니다.

사용법:
  python3 bank/sync_bank.py <내보내기한_JSON_파일>

동작:
  1. 입력 JSON(대시보드 [📤 내보내기] 결과물, 보고서 배열)을 읽어
     bank/reports.json 과 id 기준으로 병합합니다 (동일 id는 입력 파일이 최신으로 덮어씀).
  2. 병합 결과를 bank/reports.json 에 저장하고, 보고서별 bank/<id>-<굿즈명>.md 를 재생성합니다.
     더 이상 존재하지 않는 id의 .md 파일은 정리합니다.
  3. index.html 안의 `const EMBEDDED_REPORTS = [...]` 와 `const BANK_SYNCED_AT = '...'`
     라인을 병합 결과로 교체합니다. index.html 은 사람이 열지 않는 매우 긴 한 줄짜리
     파일이므로 정규식으로 해당 줄만 치환합니다.
"""
import json
import re
import sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
BANK_DIR = ROOT / 'bank'
REPORTS_JSON = BANK_DIR / 'reports.json'
INDEX_HTML = ROOT / 'index.html'

QN = ['1ea', '50ea', '100ea', '300ea', '500ea', '1,000ea', '3,000ea']
LN = ['100ea', '300ea', '500ea', '1,000ea', '3,000ea']
V_LABEL = {'GO': '✅ GO — 전환 권고', 'HOLD': '⏸ HOLD — 추가 검토', 'NO': '❌ NO — 전환 불가'}


def slug(text):
    return re.sub(r'[^0-9A-Za-z가-힣_-]+', '_', text or 'untitled').strip('_')[:60] or 'untitled'


def build_md(r):
    def row(vals, unit):
        return ' | '.join((f'{v}{unit}' if v else '—') for v in vals)

    return f"""# 협력사 변경 검토 보고서

**문서번호**: SCM-{r.get('date', '').replace('-', '')}-{str(r.get('id', ''))[-4:]}
**작성일**: {r.get('date', '')}
**분기**: {r.get('quarter', '')}
**진행 현황**: {r.get('workflowStatus', '전환 검토중')}

---

## 1. 대상 아이템

| 항목 | 내용 |
|---|---|
| 굿즈명 | {r.get('goods', '')} |
| 파츠유형 | {r.get('ptype', '')} |
| 파츠명 | {r.get('part', '')} |

## 2. 전환 검토 배경

**대분류**: {r.get('rMain', '')}
**세부사유**: {r.get('rSub') or '—'}

## 3. ASIS 현황

| 항목 | 내용 |
|---|---|
| 협력사 | {r.get('asSup', '')} |
| 소재 | {r.get('asMat', '')} |
| 임가공 | {r.get('asProc', '')} |
| MOQ | {r.get('asMoq', '')} |

### 수량별 단가

| {' | '.join(QN)} |
|{'|'.join(['---'] * len(QN))}|
| {row(r.get('asP', []), '원')} |

### 리드타임

| {' | '.join(LN)} |
|{'|'.join(['---'] * len(LN))}|
| {row(r.get('asLt4', []), '일')} |

## 4. TOBE 정보

| 항목 | 내용 |
|---|---|
| 협력사 | {r.get('tbSup', '')} |
| MOQ | {r.get('tbMoq', '')} |
| 샘플 | {r.get('tbSample', '')} |

### 수량별 단가

| {' | '.join(QN)} |
|{'|'.join(['---'] * len(QN))}|
| {row(r.get('tbP', []), '원')} |

## 5. 전환 판단

**{V_LABEL.get(r.get('verdict'), r.get('verdict', ''))}**

{r.get('opinion', '')}

---
*SCM팀 외주생산관리 파트 · {r.get('date', '')}*
"""


def main():
    if len(sys.argv) != 2:
        print('사용법: python3 bank/sync_bank.py <내보내기한_JSON_파일>')
        sys.exit(1)

    incoming_path = Path(sys.argv[1])
    incoming = json.loads(incoming_path.read_text(encoding='utf-8'))
    if not isinstance(incoming, list):
        print('입력 파일은 보고서 배열(JSON list) 이어야 합니다.')
        sys.exit(1)

    existing = json.loads(REPORTS_JSON.read_text(encoding='utf-8')) if REPORTS_JSON.exists() else []
    merged = {r['id']: r for r in existing if 'id' in r}
    added, updated = 0, 0
    for r in incoming:
        if 'id' not in r:
            continue
        if r['id'] in merged:
            updated += 1
        else:
            added += 1
        merged[r['id']] = r

    result = sorted(merged.values(), key=lambda r: r.get('date', ''), reverse=True)
    REPORTS_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

    # 보고서별 md 재생성, 더 이상 없는 id는 정리
    keep_files = set()
    for r in result:
        fname = f"{r['id']}-{slug(r.get('goods', ''))}.md"
        (BANK_DIR / fname).write_text(build_md(r), encoding='utf-8')
        keep_files.add(fname)
    for md_file in BANK_DIR.glob('*.md'):
        if md_file.name != 'README.md' and md_file.name not in keep_files:
            md_file.unlink()

    # index.html 의 EMBEDDED_REPORTS / BANK_SYNCED_AT 갱신
    html = INDEX_HTML.read_text(encoding='utf-8')
    compact_json = json.dumps(result, ensure_ascii=False, separators=(',', ':'))
    html, n1 = re.subn(
        r'const EMBEDDED_REPORTS = \[.*?\];',
        lambda _: f'const EMBEDDED_REPORTS = {compact_json};',
        html, count=1, flags=re.DOTALL,
    )
    today = date.today().isoformat()
    html, n2 = re.subn(
        r"const BANK_SYNCED_AT = '.*?';",
        f"const BANK_SYNCED_AT = '{today}';",
        html, count=1,
    )
    if n1 != 1 or n2 != 1:
        print(f'경고: index.html 치환 실패 (EMBEDDED_REPORTS={n1}, BANK_SYNCED_AT={n2}) — 수동 확인 필요')
        sys.exit(1)
    INDEX_HTML.write_text(html, encoding='utf-8')

    print(f'✅ bank 동기화 완료 — 신규 {added}건, 갱신 {updated}건, 전체 {len(result)}건 (기준일 {today})')


if __name__ == '__main__':
    main()
