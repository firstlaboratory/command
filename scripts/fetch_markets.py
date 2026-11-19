#!/usr/bin/env python3
"""Market snapshot -> data/markets.json. Indices & FX from Yahoo Finance chart API;
Chennai gold & petrol from goodreturns.in (best effort). Standard library only."""
import json, os, re, sys, time, urllib.request

OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'markets.json')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36',
      'Accept-Language': 'en-IN,en;q=0.9'}
YAHOO = [('nifty', 'Nifty 50', '^NSEI'), ('sensex', 'Sensex', '^BSESN'), ('usdinr', 'USD/INR', 'INR=X'),
         ('bank', 'Bank Nifty', '^NSEBANK'), ('brent', 'Brent $', 'BZ=F')]

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
        return r.read().decode('utf-8', 'replace')

def yahoo(sym):
    j = json.loads(get('https://query1.finance.yahoo.com/v8/finance/chart/' + urllib.request.quote(sym) + '?range=5d&interval=1d'))
    m = j['chart']['result'][0]['meta']
    price, prev = m.get('regularMarketPrice'), m.get('chartPreviousClose') or m.get('previousClose')
    return {'price': round(price, 2), 'chg': round((price - prev) / prev * 100, 2) if prev else None, 't': m.get('regularMarketTime')}

def num(s):
    return float(s.replace(',', ''))

def gold():
    h = re.sub(r'\s+', ' ', get('https://www.goodreturns.in/gold-rates/chennai.html'))
    R = r'(?:₹|&#8377;|&#x20b9;|Rs\.?)\s*([\d,]{4,7})'
    def find(k):
        for pat in (k + r'K Gold\s*/\s*g.{0,400}?' + R,
                    k + r'\s*(?:K|Carat|Karat)[^₹]{0,250}?(?:1\s*)?gram[^₹]{0,120}?' + R):
            m = re.search(pat, h, re.I)
            if m:
                v = num(m.group(1))
                if 3000 < v < 60000: return v
        return None
    g24, g22 = find('24'), find('22')
    if g24 and g22 and not (0.88 < g22 / g24 < 0.95):   # 22K should be ~91.6% of 24K
        print(f'[warn] gold ratio off: 24K={g24} 22K={g22}', file=sys.stderr); return {}
    out = {}
    if g24: out['g24'] = g24
    if g22: out['g22'] = g22
    return out

def fuel(kind):
    h = re.sub(r'\s+', ' ', get(f'https://www.goodreturns.in/{kind}-price-in-chennai.html'))
    for pat in (r'Rs\.?\s*(\d{2,3}\.\d{1,2})\s*/\s*Ltr',
                r'in Chennai stands at\s*(?:₹|Rs\.?|&#8377;)\s*(\d{2,3}\.\d{1,2})',
                r'(?:₹|Rs\.?|&#8377;)\s*(\d{2,3}\.\d{1,2})\s*(?:/|per)\s*(?:L|litre|Ltr)'):
        m = re.search(pat, h, re.I)
        if m and 60 < float(m.group(1)) < 200: return round(float(m.group(1)), 2)
    return None

def main():
    try:
        with open(OUT) as f: old = json.load(f)
    except Exception: old = {}
    items, ok = [], 0
    for key, name, sym in YAHOO:
        try:
            items.append({'id': key, 'name': name, **yahoo(sym)}); ok += 1
        except Exception as e:
            print(f'[warn] {name}: {e}', file=sys.stderr)
            prev = next((i for i in old.get('items', []) if i['id'] == key), None)
            if prev: items.append(prev)
    chennai = dict(old.get('chennai', {}))
    try:
        g = gold()
        if g: chennai.update(g); chennai['gold_at'] = int(time.time()); ok += 1
        else:
            print('[warn] gold: pattern not found', file=sys.stderr)
            for k in ('g22', 'g24'): chennai.pop(k, None)
    except Exception as e: print(f'[warn] gold: {e}', file=sys.stderr)
    for kind in ('petrol', 'diesel'):
        try:
            v = fuel(kind)
            if v: chennai[kind] = v; chennai[kind + '_at'] = int(time.time()); ok += 1
            else: print(f'[warn] {kind}: pattern not found', file=sys.stderr)
        except Exception as e: print(f'[warn] {kind}: {e}', file=sys.stderr)
    if not ok: print('nothing fetched; keeping old file', file=sys.stderr); return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump({'updated': int(time.time()), 'items': items, 'chennai': chennai}, f, separators=(',', ':'))
    print('markets:', json.dumps({'items': items, 'chennai': chennai}))

if __name__ == '__main__':
    main()
