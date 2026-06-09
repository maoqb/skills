#!/usr/bin/env python3
"""Minimal, dependency-free Markdown -> styled standalone HTML for aosp-module-doc.

Supports: ATX headings (with anchor ids), paragraphs, fenced code blocks, tables,
images (as <figure>), blockquotes, unordered lists, inline `code` and **bold**.

Special: a `## 目录` section in the source is replaced in the HTML by an
auto-generated, clickable table of contents (built from the H2/H3 headings).

Usage:  python3 md2html.py input.md output.html
"""
import sys, re, html


def is_toc(text):
    return text.strip() in ("目录", "目 录")


def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', t)
    t = re.sub(r'`([^`]+)`', lambda m: '<code>%s</code>' % m.group(1), t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    return t


def collect_headings(lines):
    """Return [(level, text, id)] for H2/H3, skipping the 目录 heading."""
    heads, cnt, in_code = [], 0, False
    for line in lines:
        if line.startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r'(#{2,3})\s+(.*)$', line)
        if m and not is_toc(m.group(2)):
            cnt += 1
            heads.append((len(m.group(1)), m.group(2).strip(), 'sec%d' % cnt))
    return heads


def build_nav(heads):
    items = []
    for lv, text, hid in heads:
        cls = ' class="sub"' if lv == 3 else ''
        items.append('<li%s><a href="#%s">%s</a></li>' % (cls, hid, inline(text)))
    return '<nav class="toc"><p class="toc-title">目录</p><ul>%s</ul></nav>' % ''.join(items)


def convert(md):
    lines = md.split('\n')
    nav = build_nav(collect_headings(lines))
    out, i, n, hc = [], 0, len(lines), 0
    while i < n:
        line = lines[i]

        if line.startswith('```'):
            i += 1
            buf = []
            while i < n and not lines[i].startswith('```'):
                buf.append(html.escape(lines[i], quote=False)); i += 1
            i += 1
            out.append('<pre><code>%s</code></pre>' % '\n'.join(buf)); continue

        m = re.match(r'!\[(.*?)\]\((.*?)\)\s*$', line)
        if m:
            alt, src = m.group(1), m.group(2)
            out.append('<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>'
                       % (html.escape(src), html.escape(alt), inline(alt)))
            i += 1; continue

        m = re.match(r'(#{1,6})\s+(.*)$', line)
        if m:
            lv, text = len(m.group(1)), m.group(2).strip()
            if lv == 2 and is_toc(text):              # replace 目录 with auto nav
                out.append(nav); i += 1
                while i < n and not lines[i].startswith('## '):
                    i += 1
                continue
            if lv in (2, 3):
                hc += 1
                out.append('<h%d id="sec%d">%s</h%d>' % (lv, hc, inline(text), lv))
            else:
                out.append('<h%d>%s</h%d>' % (lv, inline(text), lv))
            i += 1; continue

        if line.lstrip().startswith('|') and i + 1 < n and re.match(r'\s*\|[\s:|-]+\|\s*$', lines[i+1]):
            header = [c.strip() for c in line.strip().strip('|').split('|')]
            i += 2
            rows = []
            while i < n and lines[i].lstrip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            th = ''.join('<th>%s</th>' % inline(c) for c in header)
            trs = ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % inline(c) for c in r) for r in rows)
            out.append('<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (th, trs)); continue

        if line.startswith('>'):
            buf = []
            while i < n and lines[i].startswith('>'):
                buf.append(inline(re.sub(r'^>\s?', '', lines[i]))); i += 1
            out.append('<blockquote>%s</blockquote>' % '<br>'.join(buf)); continue

        if re.match(r'\s*-\s+', line):
            buf = []
            while i < n and re.match(r'\s*-\s+', lines[i]):
                buf.append('<li>%s</li>' % inline(re.sub(r'^\s*-\s+', '', lines[i]))); i += 1
            out.append('<ul>%s</ul>' % ''.join(buf)); continue

        if line.strip() == '':
            i += 1; continue

        buf = []
        while i < n and lines[i].strip() != '' and not lines[i].startswith(('#', '>', '```', '|', '-')) \
                and not re.match(r'!\[(.*?)\]\((.*?)\)', lines[i]):
            buf.append(lines[i]); i += 1
        out.append('<p>%s</p>' % inline(' '.join(buf)))
    return '\n'.join(out)


CSS = """
:root { --fg:#1a1a1a; --muted:#6b7280; --line:#e5e7eb; --accent:#2563eb; --codebg:#f6f8fa; }
* { box-sizing: border-box; }
body { max-width: 880px; margin: 0 auto; padding: 48px 24px 96px;
  font: 16px/1.75 -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; color: var(--fg); }
h1 { font-size: 1.9em; border-bottom: 2px solid var(--line); padding-bottom: .3em; margin-top: 0; }
h2 { font-size: 1.45em; margin-top: 2.2em; border-bottom: 1px solid var(--line); padding-bottom: .25em; scroll-margin-top: 16px; }
h3 { font-size: 1.15em; margin-top: 1.8em; color: #111; scroll-margin-top: 16px; }
h4 { font-size: 1.02em; margin-top: 1.4em; color: #374151; }
p { margin: 1em 0; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code { font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: .88em;
  background: var(--codebg); padding: .12em .35em; border-radius: 4px; }
pre { background: var(--codebg); border: 1px solid var(--line); border-radius: 8px; padding: 14px 16px; overflow-x: auto; line-height: 1.5; }
pre code { background: none; padding: 0; font-size: .85em; }
blockquote { margin: 1em 0; padding: .4em 1em; border-left: 4px solid var(--accent); background: #f8fafc; color: #374151; border-radius: 0 6px 6px 0; }
blockquote p { margin: .3em 0; }
table { border-collapse: collapse; width: 100%; margin: 1.2em 0; font-size: .94em; }
th, td { border: 1px solid var(--line); padding: 8px 12px; text-align: left; vertical-align: top; }
th { background: #f3f4f6; }
tbody tr:nth-child(even) { background: #fafafa; }
ul { padding-left: 1.4em; }
li { margin: .3em 0; }
figure { margin: 1.6em 0; text-align: center; }
figure img { max-width: 100%; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
figcaption { color: var(--muted); font-size: .85em; margin-top: .5em; }
nav.toc { margin: 1.5em 0 2em; padding: 16px 20px; background: #fafafa; border: 1px solid var(--line); border-radius: 8px; }
nav.toc .toc-title { font-weight: 600; margin: 0 0 .5em; }
nav.toc ul { list-style: none; padding-left: 0; margin: 0; }
nav.toc li { margin: .2em 0; }
nav.toc li.sub { padding-left: 1.5em; font-size: .94em; }
"""


def main():
    src, dst = sys.argv[1], sys.argv[2]
    md = open(src, encoding='utf-8').read()
    title = 'Document'
    m = re.search(r'^#\s+(.*)$', md, re.M)
    if m:
        title = m.group(1).strip()
    doc = ('<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           '<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n</body>\n</html>\n'
           % (html.escape(title), CSS, convert(md)))
    open(dst, 'w', encoding='utf-8').write(doc)
    print('wrote', dst)


if __name__ == '__main__':
    main()
