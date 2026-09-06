"""Render original SVG brand cards. Requires rsvg-convert for PNG conversion."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
for lang in ('de', 'en'):
    de = lang == 'de'
    title = 'Deine Health-Daten.' if de else 'Your health data.'
    second = 'Bereit für mehr.' if de else 'Ready for more.'
    subtitle = 'Apple Health exportieren. Lokal. Ohne Abo.' if de else 'Export Apple Health. On-device. No subscription.'
    labels = ['Aktivität', 'Schlaf', 'Herz', 'Körper', 'Ernährung', 'Mental'] if de else ['Activity', 'Sleep', 'Heart', 'Body', 'Nutrition', 'Mind']
    colors = ['#c78365', '#7896c8', '#b97685', '#b3a68a', '#8bb08a', '#a193c6']
    layers = []
    for i in reversed(range(6)):
        y = 160 + i * 48
        layers.append(f'<g transform="translate(0 {y})"><path d="M775 25 910 76 1120 2v13L910 90 775 39Z" fill="{colors[i]}" fill-opacity=".18"/><path d="M775 25 985 -50 1120 2 910 76Z" fill="#202c2e" stroke="{colors[i]}" stroke-opacity=".65"/></g>')
    pills = ''.join(f'<rect x="{70 + i * 134}" y="407" width="118" height="43" rx="6" fill="#203a35"/><text x="{129 + i * 134}" y="434" text-anchor="middle" font-size="17" fill="#a0f4dc">{label}</text>' for i, label in enumerate(['CSV', 'JSON', 'Markdown']))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
<rect width="1200" height="630" fill="#11191b"/>
<g font-family="Arial"><text x="70" y="101" font-size="44" font-weight="bold" fill="#f4f5ee">strata<tspan fill="#a0f4dc">.</tspan></text>
<text x="70" y="244" font-size="62" fill="#f4f5ee" letter-spacing="-2">{title}</text>
<text x="70" y="315" font-size="62" fill="#a0f4dc" letter-spacing="-2">{second}</text>
<text x="73" y="366" font-size="21" fill="#aab8b5">{subtitle}</text>
{pills}{''.join(layers)}
<path d="M70 518H1130" stroke="#344240"/><text x="70" y="568" font-size="20" fill="#aab8b5">iPhone + iPad</text>
<text x="1130" y="568" text-anchor="end" font-size="20" fill="#a0f4dc">strata-app.de</text></g></svg>'''
    source = ROOT / '_source' / f'social-{lang}.svg'
    source.write_text(svg)
    subprocess.run(['rsvg-convert', str(source), '-o', str(ROOT / 'assets' / f'social-{lang}.png')], check=True)
print('Rendered two localized social cards (1200 × 630)')
