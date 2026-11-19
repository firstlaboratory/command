#!/usr/bin/env python3
"""Tamil calendar events (muhurtham, amavasai, pournami, pradosham, festivals, holidays) for this
month and the next two, from calendar.tamildot.com -> data/tamil.json. Standard library only."""
import json, os, re, sys, time, urllib.request
from datetime import date

OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'tamil.json')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'}
MON = ['January','February','March','April','May','June','July','August','September','October','November','December']

def lines(url):
    h = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode('utf-8', 'replace')
    h = re.sub(r'\s+', ' ', h)
    h = re.sub(r'<script.*?</script>|<style.*?</style>', '', h)
    t = re.sub(r'<(/?)(tr|table|h\d)[^>]*>', r'\n', h)
    t = re.sub(r'<t[dh][^>]*>', ' | ', t)
    t = re.sub(r'<[^>]+>', '', t).replace('&amp;', '&').replace('&nbsp;', ' ')
    return [l.strip() for l in t.split('\n') if l.strip()]

def month(y, m):
    L = lines(f'https://calendar.tamildot.com/tamil-monthly-calendar/{MON[m-1]}-{y}')
    ev, mu, fe = [], [], []
    sec = ''
    for l in L:
        if l.startswith('Festival Dates'): sec = 'fest'
        elif l.startswith('Subha Muhurtham'): sec = 'mu'
        elif 'Govt' in l and 'Holiday' in l: sec = 'hol'
        cells = [c.strip() for c in l.split('|') if c.strip()]
        # event rows: Name (Tamil) | Month | 4 & 20
        if len(cells) == 3 and cells[1] == MON[m-1] and re.fullmatch(r'[\d &,]+', cells[2]):
            nm = cells[0]; ta = (re.search(r'\(([^)]+)\)', nm) or [None, ''])[1]; en = re.sub(r'\s*\(.*', '', nm)
            for d in re.findall(r'\d+', cells[2]):
                ev.append({'d': f'{y}-{m:02d}-{int(d):02d}', 'en': en, 'ta': ta})
            continue
        dm = re.match(r'(\d{1,2}) ' + MON[m-1] + r', ' + str(y), cells[0]) if cells else None
        if dm:
            d = f'{y}-{m:02d}-{int(dm.group(1)):02d}'
            if sec == 'mu':
                mu.append({'d': d, 'v': 'valarpirai' in l.lower(), 't': 'theipirai' in l.lower()})
            elif sec == 'fest' and len(cells) >= 4 and cells[3].lower() == 'hindu':
                fe.append({'d': d, 'en': cells[2]})
        elif sec == 'hol' and len(cells) >= 3 and re.fullmatch(r'\d{1,2}', cells[0]):
            fe.append({'d': f'{y}-{m:02d}-{int(cells[0]):02d}', 'en': cells[2], 'hol': True})
    return ev, mu, fe

def main():
    t = date.today(); ev, mu, fe, ok = [], [], [], 0
    for k in range(3):
        y, m = t.year + (t.month - 1 + k) // 12, (t.month - 1 + k) % 12 + 1
        try:
            a, b, c = month(y, m); ev += a; mu += b; fe += c; ok += 1
            print(f'{y}-{m:02d}: {len(a)} events, {len(b)} muhurtham, {len(c)} festivals/holidays')
        except Exception as e:
            print(f'[warn] {y}-{m}: {e}', file=sys.stderr)
    if not ok: return
    seen = set(); fe = [x for x in fe if not ((x['d'], x['en']) in seen or seen.add((x['d'], x['en'])))]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump({'updated': int(time.time()), 'events': sorted(ev, key=lambda x: x['d']), 'muhurtham': sorted(mu, key=lambda x: x['d']),
                   'festivals': sorted(fe, key=lambda x: x['d'])}, f, ensure_ascii=False, separators=(',', ':'))

if __name__ == '__main__':
    main()
