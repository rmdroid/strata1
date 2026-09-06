"""Check the deliverable without a server, browser, network or installed packages."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import re
import struct
import xml.etree.ElementTree as ET
import sys

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://strata-app.de/'
FILES = {'index.html': 'de', 'index_en.html': 'en', 'support.html': 'de', 'support_eng.html': 'en'}
errors = []

def check(condition, message):
    if not condition:
        errors.append(message)

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.scripts = []
        self.script = None
        self.text = path.read_text()
        self.feed(self.text)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag == 'script':
            self.script = [attrs, '']
    def handle_data(self, data):
        if self.script is not None:
            self.script[1] += data
    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            self.scripts.append(self.script)
            self.script = None
    def find(self, tag, **attrs):
        return [a for t, a in self.tags if t == tag and all(a.get(k) == v for k, v in attrs.items())]

pages = {name: Page(ROOT / name) for name in FILES}
canonical = {name: BASE + ('' if name == 'index.html' else name) for name in FILES}

def check_reference(href, filename):
    u = urlsplit(href)
    if u.scheme and not href.startswith(BASE):
        return
    if u.netloc and u.netloc != 'strata-app.de':
        return
    path = unquote(u.path).lstrip('/')
    target = path or ('index.html' if u.netloc else filename)
    check((ROOT / target).is_file(), f'{filename}: missing reference {href}')
    if u.fragment and target in pages:
        ids = {a['id'] for _, a in pages[target].tags if 'id' in a}
        check(unquote(u.fragment) in ids, f'{filename}: missing anchor {href}')

titles = []
descriptions = []
for name, page in pages.items():
    lang = FILES[name]
    check(page.find('html', lang=lang), f'{name}: html language')
    check(len(page.find('h1')) == 1, f'{name}: exactly one h1')
    ids = [a['id'] for _, a in page.tags if 'id' in a]
    check(len(ids) == len(set(ids)), f'{name}: duplicate IDs')
    title = re.search(r'<title>(.*?)</title>', page.text).group(1)
    titles.append(title)
    check(20 <= len(title) <= 80, f'{name}: title length')
    meta = page.find('meta', name='description')
    check(len(meta) == 1 and 80 <= len(meta[0]['content']) <= 170, f'{name}: description')
    descriptions.append(meta[0]['content'])
    check(page.find('link', rel='canonical') == [{'rel': 'canonical', 'href': canonical[name]}], f'{name}: canonical')
    alternates = {a.get('hreflang'): a.get('href') for a in page.find('link', rel='alternate')}
    pair = ('support.html', 'support_eng.html') if name.startswith('support') else ('index.html', 'index_en.html')
    expected = {'de': canonical[pair[0]], 'en': canonical[pair[1]], 'x-default': canonical[pair[0]]}
    check(alternates == expected, f'{name}: reciprocal language alternatives')
    check(page.find('meta', property='og:url')[0]['content'] == canonical[name], f'{name}: OG URL')
    for key, value in [('og:image:width', '1200'), ('og:image:height', '630')]:
        check(page.find('meta', property=key)[0]['content'] == value, f'{name}: {key}')
    image = page.find('meta', property='og:image')[0]['content']
    check_reference(image, name)
    check(page.find('meta', name='twitter:image')[0]['content'] == image, f'{name}: Twitter image')
    for tag, attrs in page.tags:
        for attr in ('src', 'href'):
            if attrs.get(attr):
                check_reference(attrs[attr], name)
        if tag == 'img':
            check('alt' in attrs and 'width' in attrs and 'height' in attrs, f'{name}: image accessibility/dimensions')
        if attrs.get('aria-labelledby'):
            check(all(x in ids for x in attrs['aria-labelledby'].split()), f'{name}: label target')
    graphs = [json.loads(data)['@graph'] for attrs, data in page.scripts if attrs.get('type') == 'application/ld+json']
    check(len(graphs) == 1, f'{name}: structured data')
    apps = [node for node in graphs[0] if node['@type'] == 'SoftwareApplication']
    check(len(apps) == (0 if name.startswith('support') else 1), f'{name}: schema page type')
    if apps:
        check(apps[0]['offers']['priceCurrency'] == ('EUR' if lang == 'de' else 'USD'), f'{name}: currency')
        check(apps[0]['offers']['price'] == '9.99', f'{name}: offer')
    config = next(json.loads(data) for attrs, data in page.scripts if attrs.get('id') == 'page-config')
    check(config['lang'] == lang and len(config['screens']) == 7, f'{name}: gallery config')
    for screen in config['screens']:
        check_reference(f'assets/{lang}/{screen["file"]}.webp', name)
        check(screen['width'] > 0 and screen['height'] > 0, f'{name}: gallery dimensions')
    check(not page.find('script', src='https://cv.rm-on.de/script.js'), f'{name}: analytics must require consent')
    check(not page.find('script', src='https://n8n.top-beraternetzwerk.de/webhook/termine'), f'{name}: no eager contact request')
    inline = [data for attrs, data in page.scripts if not attrs.get('type') and not attrs.get('src')]
    check(len(inline) == 1 and inline[0] == (ROOT / '_source/app.js').read_text(), f'{name}: current runtime script')

check(len(set(titles)) == 4 and len(set(descriptions)) == 4, 'Distinct localized titles and descriptions')
tree = ET.parse(ROOT / 'sitemap.xml')
ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'x': 'http://www.w3.org/1999/xhtml'}
urls = tree.findall('s:url', ns)
check({x.find('s:loc', ns).text for x in urls} == set(canonical.values()) and len(urls) == 4, 'Sitemap canonical coverage')
for item in urls:
    url = item.find('s:loc', ns).text
    name = next(k for k, v in canonical.items() if v == url)
    actual = {a.get('hreflang'): a.get('href') for a in item.findall('x:link', ns)}
    expected = {a['hreflang']: a['href'] for a in pages[name].find('link', rel='alternate')}
    check(actual == expected, f'{name}: sitemap and HTML hreflang agree')
robots = (ROOT / 'robots.txt').read_text()
check('Disallow: /\n' not in robots and f'Sitemap: {BASE}sitemap.xml' in robots, 'Robots permits public crawling and names sitemap')
llms = (ROOT / 'llms.txt').read_text()
check(llms.startswith('# Strata App\n') and '\n> ' in llms, 'llms.txt introductory format')
for href in re.findall(r'\]\((https?://[^)]+)\)', llms):
    check_reference(href, 'llms.txt')
for lang in ('de', 'en'):
    png = (ROOT / f'assets/social-{lang}.png').read_bytes()
    check(png[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', png[16:24]) == (1200, 630), f'{lang}: social card dimensions')

if errors:
    print('\n'.join('FAIL: ' + error for error in errors))
    sys.exit(1)
print('PASS: 4 pages; links and anchors; localized metadata; gallery assets; structured data; sitemap; robots.txt; llms.txt; social cards.')
