"""Localized metadata and public discovery files. No external dependencies."""
from html import escape
import json
import xml.etree.ElementTree as ET

BASE = 'https://strata-app.de/'
UPDATED = '2026-09-06'
PAGES = {'de': ('', 'support.html'), 'en': ('index_en.html', 'support_eng.html')}

def metadata(lang, title, description, support=False):
    position = int(support)
    canonical = BASE + PAGES[lang][position]
    image = BASE + f'assets/social-{lang}.png'
    image_alt = ('Strata: Apple-Health-Daten als CSV, JSON und Markdown exportieren.' if lang == 'de'
                 else 'Strata: export Apple Health data to CSV, JSON and Markdown.')
    store = f'https://apps.apple.com/{"de" if lang == "de" else "us"}/app/strata-app/id6760822991'
    publisher = {'@type': 'Person', '@id': BASE + '#developer', 'name': 'Robert Meyer',
                 'url': BASE + 'support.html#imprint'}
    website = {'@type': 'WebSite', '@id': BASE + '#website', 'url': BASE, 'name': 'Strata App',
               'inLanguage': ['de', 'en'], 'publisher': {'@id': BASE + '#developer'}}
    page = {'@type': 'ContactPage' if support else 'WebPage', '@id': canonical + '#webpage',
            'url': canonical, 'name': title, 'description': description, 'inLanguage': lang,
            'dateModified': UPDATED, 'isPartOf': {'@id': BASE + '#website'},
            'primaryImageOfPage': {'@type': 'ImageObject', 'url': image, 'width': 1200, 'height': 630}}
    graph = [publisher, website, page]
    if not support:
        app_id = canonical + '#app'
        page['mainEntity'] = {'@id': app_id}
        graph.append({'@type': 'SoftwareApplication', '@id': app_id, 'name': 'Strata App',
                      'url': canonical, 'description': description,
                      'applicationCategory': 'HealthApplication',
                      'operatingSystem': 'iOS 17.0 or later; iPadOS 17.0 or later',
                      'inLanguage': ['de', 'en'],
                      'author': {'@id': BASE + '#developer'}, 'image': BASE + 'assets/app-icon.webp',
                      'downloadUrl': store, 'installUrl': store,
                      'featureList': ['Apple Health data export', 'CSV', 'JSON', 'Markdown',
                                      'On-device processing', 'No subscription'],
                      'offers': {'@type': 'Offer', 'price': '9.99',
                                 'priceCurrency': 'EUR' if lang == 'de' else 'USD', 'url': store}})
    tags = ['<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<meta name="theme-color" content="#11191b">', f'<title>{escape(title)}</title>',
            '<meta name="robots" content="index, follow, max-image-preview:large">',
            '<meta name="referrer" content="strict-origin-when-cross-origin">',
            '<meta name="author" content="Robert Meyer">', '<meta name="application-name" content="Strata">',
            '<meta name="apple-itunes-app" content="app-id=6760822991">',
            f'<link rel="canonical" href="{canonical}">',
            '<link rel="describedby" href="llms.txt" type="text/plain">',
            '<link rel="icon" href="assets/favicon-32.png" type="image/png" sizes="32x32">',
            '<link rel="icon" href="assets/app-icon.webp" type="image/webp">',
            '<link rel="apple-touch-icon" href="assets/apple-touch-icon.png" sizes="180x180">']
    for language in ('de', 'en', 'x-default'):
        target = 'de' if language == 'x-default' else language
        tags.append(f'<link rel="alternate" hreflang="{language}" href="{BASE + PAGES[target][position]}">')
    values = [
        ('name', 'description', description), ('property', 'og:type', 'website'),
        ('property', 'og:locale', 'de_DE' if lang == 'de' else 'en_US'),
        ('property', 'og:locale:alternate', 'en_US' if lang == 'de' else 'de_DE'),
        ('property', 'og:site_name', 'Strata App'), ('property', 'og:title', title),
        ('property', 'og:description', description), ('property', 'og:url', canonical),
        ('property', 'og:image', image), ('property', 'og:image:type', 'image/png'),
        ('property', 'og:image:width', '1200'), ('property', 'og:image:height', '630'),
        ('property', 'og:image:alt', image_alt), ('name', 'twitter:card', 'summary_large_image'),
        ('name', 'twitter:title', title), ('name', 'twitter:description', description),
        ('name', 'twitter:image', image), ('name', 'twitter:image:alt', image_alt)]
    tags.extend(f'<meta {key}="{name}" content="{escape(value, quote=True)}">' for key, name, value in values)
    schema = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False).replace('<', '\\u003c')
    tags.append(f'<script type="application/ld+json">{schema}</script>')
    return '\n'.join(tags)

def write_discovery(root):
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    xhtml = 'http://www.w3.org/1999/xhtml'
    ET.register_namespace('', ns)
    ET.register_namespace('xhtml', xhtml)
    sitemap = ET.Element(f'{{{ns}}}urlset')
    for lang in ('de', 'en'):
        for position, path in enumerate(PAGES[lang]):
            item = ET.SubElement(sitemap, f'{{{ns}}}url')
            ET.SubElement(item, f'{{{ns}}}loc').text = BASE + path
            ET.SubElement(item, f'{{{ns}}}lastmod').text = UPDATED
            for alternate in ('de', 'en', 'x-default'):
                target = 'de' if alternate == 'x-default' else alternate
                ET.SubElement(item, f'{{{xhtml}}}link', rel='alternate', hreflang=alternate,
                              href=BASE + PAGES[target][position])
    ET.indent(sitemap, space='  ')
    ET.ElementTree(sitemap).write(root / 'sitemap.xml', encoding='utf-8', xml_declaration=True)
    (root / 'robots.txt').write_text('User-agent: *\nAllow: /\nDisallow: /_source/\n\nSitemap: ' + BASE + 'sitemap.xml\n')
