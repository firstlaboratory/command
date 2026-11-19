#!/usr/bin/env python3
"""Fetch headlines (Google News RSS) and India trending searches (Google Trends RSS)
into data/news.json. Standard library only. Run by GitHub Actions every 3 hours."""
import json, os, sys, time, urllib.request, xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'news.json')
GN = 'https://news.google.com/rss'
Q = 'hl=en-IN&gl=IN&ceid=IN:en'
CATEGORIES = [
    ('india',    'India',      f'{GN}/headlines/section/topic/NATION?{Q}'),
    ('tn',       'Tamil Nadu', f'{GN}/search?q=%22Tamil+Nadu%22+OR+Chennai+when:1d&{Q}'),
    ('tech',     'Tech',       f'{GN}/headlines/section/topic/TECHNOLOGY?{Q}'),
    ('business', 'Business',   f'{GN}/headlines/section/topic/BUSINESS?{Q}'),
    ('auto',     'Auto',       f'{GN}/search?q=automobile+OR+%22auto+industry%22+OR+EV+India+when:2d&{Q}'),
    ('world',    'World',      f'{GN}/headlines/section/topic/WORLD?{Q}'),
]
TRENDS = 'https://trends.google.com/trending/rss?geo=IN'
PER_CAT = 12

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (CommandCentre news bot)'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def local(tag):
    return tag.rsplit('}', 1)[-1]

def child(el, name):
    for c in el:
        if local(c.tag) == name:
            return c
    return None

def text(el, name):
    c = child(el, name)
    return (c.text or '').strip() if c is not None else ''

def ts(s):
    try:
        return int(parsedate_to_datetime(s).timestamp())
    except Exception:
        return 0

def parse_news(xml):
    root = ET.fromstring(xml)
    out = []
    for it in root.iter():
        if local(it.tag) != 'item':
            continue
        title, link = text(it, 'title'), text(it, 'link')
        src = text(it, 'source')
        if src and title.endswith(' - ' + src):
            title = title[: -len(src) - 3]
        if title and link:
            out.append({'t': title, 'u': link, 's': src, 'p': ts(text(it, 'pubDate'))})
    out.sort(key=lambda x: -x['p'])
    return out[:PER_CAT]

def parse_trends(xml):
    root = ET.fromstring(xml)
    out = []
    for it in root.iter():
        if local(it.tag) != 'item':
            continue
        q = text(it, 'title')
        if not q:
            continue
        news = []
        for n in it:
            if local(n.tag) == 'news_item':
                nt, nu, ns = text(n, 'news_item_title'), text(n, 'news_item_url'), text(n, 'news_item_source')
                if nt and nu:
                    news.append({'t': nt, 'u': nu, 's': ns})
        out.append({'q': q, 'traffic': text(it, 'approx_traffic'), 'p': ts(text(it, 'pubDate')), 'news': news[:2]})
    return out[:20]

def main():
    old = {}
    try:
        with open(OUT) as f:
            old = json.load(f)
    except Exception:
        pass
    old_cats = {c['id']: c for c in old.get('categories', [])}
    cats, ok = [], 0
    for cid, name, url in CATEGORIES:
        try:
            items = parse_news(get(url))
            if not items:
                raise ValueError('empty')
            cats.append({'id': cid, 'name': name, 'items': items}); ok += 1
        except Exception as e:
            print(f'[warn] {name}: {e}', file=sys.stderr)
            if cid in old_cats:
                cats.append(old_cats[cid])
    try:
        trends = parse_trends(get(TRENDS)); ok += 1
    except Exception as e:
        print(f'[warn] trends: {e}', file=sys.stderr)
        trends = old.get('trends', [])
    if ok == 0:
        print('No feeds succeeded; keeping old file', file=sys.stderr)
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump({'updated': int(time.time()), 'categories': cats, 'trends': trends}, f, ensure_ascii=False, separators=(',', ':'))
    print(f'Wrote {OUT}: {sum(len(c["items"]) for c in cats)} headlines, {len(trends)} trends')

if __name__ == '__main__':
    main()
