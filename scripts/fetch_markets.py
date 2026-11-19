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
    out = {}
    for k in ('24', '22'):
        m = re.search(k + r'\s*K[^₹]{0,120}?(?:₹|Rs\.?|&#8377;)\s*([\d,]{4,7})(?:\.\d+)?\b', h, re.I)
        if m:
            v = num(m.group(1))
            out['g' + k] = v if v < 30000 else round(v / 10, 2)   # per gram
    return out

def petrol():
    h = re.sub(r'\s+', ' ', get('https://www.goodreturns.in/petrol-price-in-chennai.html'))
    m = re.search(r'(?:₹|Rs\.?|&#8377;)\s*(1\d{2}\.\d{1,2})\s*(?:/|per)\s*(?:L|litre|Ltr)', h, re.I) or re.search(r'Chennai[^₹]{0,80}(?:₹|Rs\.?|&#8377;)\s*(1\d{2}\.\d{1,2})', h, re.I)
    return round(num(m.group(1)), 2) if m else None

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
        else: print('[warn] gold: pattern not found', file=sys.stderr)
    except Exception as e: print(f'[warn] gold: {e}', file=sys.stderr)
    try:
        p = petrol()
        if p: chennai['petrol'] = p; chennai['petrol_at'] = int(time.time()); ok += 1
        else: print('[warn] petrol: pattern not found', file=sys.stderr)
    except Exception as e: print(f'[warn] petrol: {e}', file=sys.stderr)
    if not ok: print('nothing fetched; keeping old file', file=sys.stderr); return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump({'updated': int(time.time()), 'items': items, 'chennai': chennai}, f, separators=(',', ':'))
    print('markets:', json.dumps({'items': items, 'chennai': chennai}))

if __name__ == '__main__':
    main()
