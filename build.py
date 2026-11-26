#!/usr/bin/env python3
"""Генератор бейджей.

  python build.py                          пересобрать все SVG, README.md и index.html
  python build.py add "Название" ЦВЕТ ИК [Категория] [папка]
                                           добавить бейдж, например:
                                           python build.py add "Bun" E8B84A Bn "Веб"
                                           (папку указывайте только для новой категории)
Ничего ставить не нужно: только Python 3.
"""
import json, sys, html, re
from pathlib import Path

ROOT = Path(__file__).parent
CFG = ROOT / "badges.json"
OUT = ROOT / "badges"
CHAR_W = 7.7  # ширина символа при font-size 10, letter-spacing


def lum(hexcolor):
    h = hexcolor.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def load_icon(bid):
    """Иконка из icons/<id>.svg: возвращает (содержимое, viewBox) или None."""
    f = ROOT / "icons" / f"{bid}.svg"
    if not f.exists():
        return None
    raw = f.read_text(encoding="utf-8")
    m = re.search(r"<svg[^>]*>(.*)</svg>", raw, re.S)
    if not m:
        return None
    vb = re.search(r'viewBox="([^"]+)"', raw)
    box = [float(x) for x in vb.group(1).replace(",", " ").split()] if vb else [0, 0, 24, 24]
    body = re.sub(r"<title>.*?</title>", "", m.group(1), flags=re.S)
    return body, box


def make_svg(item, height=28, use_icon=True):
    label = item["label"].upper()
    color = item["color"].lstrip("#").upper()
    fg = "#1F1F1F" if lum(color) > 0.45 else "#FFFFFF"
    tl = round(len(label) * CHAR_W, 1)
    w = round(32 + tl + 12)
    name = html.escape(item["label"])
    inner = None
    if use_icon:
        inner = (item["svg"], [0, 0, 24, 24]) if item.get("svg") else load_icon(item["id"])
    if inner:            # настоящий логотип: рисуется цветом текста бейджа
        body, vb = inner
        sc = 14 / max(vb[2], vb[3])
        tx = 9 + (14 - vb[2] * sc) / 2 - vb[0] * sc
        ty = 7 + (14 - vb[3] * sc) / 2 - vb[1] * sc
        icon = (f'<g transform="translate({tx:.2f} {ty:.2f}) scale({sc:.4f})" fill="{fg}" color="{fg}">'
                f'{body}</g>')
    else:                # значок-монограмма
        icon = (f'<rect x="8" y="6" width="16" height="16" rx="3" fill="{fg}" fill-opacity="0.2"/>'
                f'<text x="16" y="17.3" fill="{fg}" font-family="Verdana,\'DejaVu Sans\',Geneva,sans-serif" '
                f'font-size="8" font-weight="bold" text-anchor="middle">{html.escape(item["icon"])}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{height}" '
            f'viewBox="0 0 {w} {height}" role="img" aria-label="{name}">\n'
            f'  <title>{name}</title>\n'
            f'  <rect width="{w}" height="{height}" rx="2" fill="#{color}"/>\n'
            f'  {icon}\n'
            f'  <text x="32" y="18" fill="{fg}" font-family="Verdana,\'DejaVu Sans\',Geneva,sans-serif" '
            f'font-size="10" font-weight="bold" textLength="{tl}" lengthAdjust="spacing">{html.escape(label)}</text>\n'
            f'</svg>\n')


def urls(cfg, item, variant):
    return (f'https://raw.githubusercontent.com/{cfg["owner"]}/{cfg["repo"]}/{cfg["branch"]}'
            f'/badges/{variant}/{item["dir"]}/{item["id"]}.svg')


def snippets(cfg, item, variant):
    u = urls(cfg, item, variant)
    return {"md": f'![{item["label"]}]({u})',
            "html": f'<img src="{u}" alt="{item["label"]}" height="{cfg["height"]}" />',
            "url": u}


def build_readme(cfg):
    items = [i for c in cfg["categories"] for i in c["items"]]
    total, with_icon = len(items), sum(1 for i in items if i["has_icon"])
    pages = f'https://{cfg["owner"].lower()}.github.io/{cfg["repo"]}/'
    raw = f'https://raw.githubusercontent.com/{cfg["owner"]}/{cfg["repo"]}/{cfg["branch"]}/badges'
    h = cfg["height"]
    L = []
    L.append('# Бейджи для README\n')
    L.append(f'**{total} готовых бейджей** в одном стиле, у каждого есть выбор из двух видов:\n')
    L.append(f'- **С иконкой**: настоящий логотип технологии (сейчас у {with_icon} бейджей).')
    L.append(f'- **С буквами**: значок из двух букв (есть у всех {total}).\n')
    L.append('Это обычные SVG-файлы: они лежат в репозитории, не зависят от shields.io и не ломаются из-за «неизвестных иконок».\n')
    L.append('## Как пользоваться\n')
    L.append(f'1. **Самый удобный способ:** откройте [страницу с галереей]({pages}), выберите вид (с иконками или с буквами), '
             f'нажмите на бейдж, и код скопируется в буфер обмена. Вставьте его в свой README.')
    L.append('2. **Через этот README:** найдите бейдж в таблицах ниже и скопируйте его код '
             '(в каждой категории есть блоки «скопировать всю категорию» с кнопкой копирования).')
    L.append(f'3. **Напрямую:** ссылка на бейдж имеет вид `{raw}/ВИД/КАТЕГОРИЯ/ИМЯ.svg`, '
             f'где ВИД это `with-icon` или `letters`.\n')
    L.append('Чтобы бейджи стояли по центру в профиле, оберните их в:\n')
    L.append('```html\n<div align="center">\n\n  <!-- сюда вставьте бейджи -->\n\n</div>\n```\n')
    L.append('Если хотите, чтобы бейдж был ссылкой, оберните его так: `[![Python](ссылка-на-бейдж)](https://python.org)`.\n')
    L.append('## Галерея\n')
    for cat in cfg["categories"]:
        L.append(f'### {cat["name"]}\n')
        L.append('| Название | С иконкой | С буквами | Код (Markdown) |')
        L.append('|---|---|---|---|')
        for it in cat["items"]:
            alt = html.escape(it["label"])
            let_img = f'<img src="badges/letters/{it["dir"]}/{it["id"]}.svg" alt="{alt}" height="{h}" />'
            md_l = snippets(cfg, it, "letters")["md"]
            if it["has_icon"]:
                ico_img = f'<img src="badges/with-icon/{it["dir"]}/{it["id"]}.svg" alt="{alt}" height="{h}" />'
                code = f'С иконкой: `{snippets(cfg, it, "with-icon")["md"]}`<br>С буквами: `{md_l}`'
            else:
                ico_img, code = '—', f'`{md_l}`'
            L.append(f'| {alt} | {ico_img} | {let_img} | {code} |')
        L.append('')
        icon_items = [i for i in cat["items"] if i["has_icon"]]
        if icon_items:
            L.append('<details><summary>Скопировать всю категорию: с иконками</summary>\n')
            L.append('```markdown')
            L += [snippets(cfg, i, "with-icon")["md"] for i in icon_items]
            L.append('```\n')
            L.append('</details>\n')
        L.append('<details><summary>Скопировать всю категорию: с буквами</summary>\n')
        L.append('```markdown')
        L += [snippets(cfg, i, "letters")["md"] for i in cat["items"]]
        L.append('```\n')
        L.append('</details>\n')
    L.append('## Структура папок\n')
    L.append('```text')
    L.append('badges/')
    L.append('  with-icon/         # версия с настоящим логотипом')
    for cat in cfg["categories"]:
        n = sum(1 for i in cat["items"] if i["has_icon"])
        if n:
            L.append(f'    {cat["slug"]}/'.ljust(26) + f'# {cat["name"]} ({n})')
    L.append('  letters/           # версия с буквами (есть у всех)')
    for cat in cfg["categories"]:
        L.append(f'    {cat["slug"]}/'.ljust(26) + f'# {cat["name"]} ({len(cat["items"])})')
    L.append('icons/               # исходные логотипы (SVG)')
    L.append('```\n')
    L.append('## Иконки\n')
    L.append('Если в папке `icons/` лежит файл с тем же именем, что и бейдж (например, `icons/python.svg` для бейджа `python`), '
             'для него создаётся версия с иконкой. Версия с буквами создаётся всегда.\n')
    L.append('Чтобы добавить или заменить иконку: положите одноцветный SVG (лучше квадратный, viewBox 24×24) '
             'в `icons/ИМЯ.svg` и запустите `python build.py`. Цвет указывать не нужно, генератор покрасит иконку сам. '
             'Логотипы можно взять на [simpleicons.org](https://simpleicons.org). Источники и лицензии: `icons/NOTICE.md`.\n')
    L.append('## Добавить свой бейдж\n')
    L.append('Нужен только Python 3:\n')
    L.append('```bash\npython build.py add "Bun" E8B84A Bn "Веб"\n```\n')
    L.append('Параметры: название, цвет (HEX без `#`), 1-2 буквы для значка, категория и (для новой категории) '
             'имя папки латиницей. Скрипт создаст SVG и обновит README и страницу галереи.\n')
    L.append('## Настройка\n')
    L.append('В `badges.json` в начале файла указаны `owner`, `repo` и `branch`. Если вы назвали репозиторий '
             'иначе или у вас другое имя пользователя, поменяйте их и запустите `python build.py`: '
             'все ссылки в README и на странице обновятся.\n')
    L.append(f'Страница-галерея работает через GitHub Pages: *Settings → Pages → Deploy from a branch → `{cfg["branch"]}` / `(root)`*.\n')
    return "\n".join(L)


HTML = r"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Бейджи: нажми и скопируй</title>
<style>
:root{--bg:#0d1117;--card:#161b22;--line:#30363d;--fg:#e6edf3;--mute:#8b949e;--acc:#3a9b68}
@media (prefers-color-scheme:light){:root{--bg:#f6f8fa;--card:#fff;--line:#d0d7de;--fg:#1f2328;--mute:#59636e;--acc:#2d7d54}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,Segoe UI,Roboto,sans-serif;padding:24px 16px 80px}
main{max-width:1000px;margin:0 auto}
h1{margin:0 0 4px;font-size:26px}
p.sub{margin:0 0 20px;color:var(--mute)}
.bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:14px}
input[type=search]{flex:1 1 220px;padding:9px 12px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--fg);font:inherit}
.seg{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{background:var(--card);color:var(--fg);border:0;padding:9px 12px;font:inherit;cursor:pointer}
.seg button[aria-pressed=true]{background:var(--acc);color:#fff}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px}
.chips button{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:5px 12px;font:inherit;cursor:pointer}
.chips button[aria-pressed=true]{border-color:var(--acc);color:var(--acc)}
h2{font-size:17px;margin:26px 0 10px;color:var(--mute);font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}
.card{display:flex;flex-direction:column;align-items:flex-start;gap:10px;padding:14px;border:1px solid var(--line);background:var(--card);border-radius:10px;cursor:pointer;text-align:left;color:var(--fg);font:inherit}
.card:hover,.card:focus-visible{border-color:var(--acc);outline:none}
.card img{max-width:100%;height:28px}
.card span{font-size:12px;color:var(--mute)}
.all{margin-left:auto}
.all button{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:9px 12px;font:inherit;cursor:pointer}
#toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%) translateY(20px);background:var(--acc);color:#fff;padding:10px 18px;border-radius:8px;opacity:0;pointer-events:none;transition:.2s}
#toast.show{opacity:1;transform:translateX(-50%)}
.empty{color:var(--mute);padding:30px 0}
</style>
</head>
<body>
<main>
  <h1>Бейджи: нажми и скопируй</h1>
  <p class="sub">Выберите формат, нажмите на бейдж, и код окажется в буфере обмена.</p>
  <div class="bar">
    <input type="search" id="q" placeholder="Поиск: python, unity, docker…" aria-label="Поиск">
    <div class="seg" id="vari">
      <button data-v="with-icon" aria-pressed="true">С иконками</button>
      <button data-v="letters" aria-pressed="false">С буквами</button>
    </div>
    <div class="seg" id="fmt">
      <button data-f="md" aria-pressed="true">Markdown</button>
      <button data-f="html" aria-pressed="false">HTML</button>
      <button data-f="url" aria-pressed="false">Ссылка</button>
    </div>
    <div class="all"><button id="copyAll">Скопировать показанные</button></div>
  </div>
  <div class="chips" id="chips"></div>
  <div id="list"></div>
</main>
<div id="toast" role="status"></div>
<script>
const DATA = __DATA__;
let fmt = 'md', vari = 'with-icon', cat = '', q = '';
const $ = s => document.querySelector(s);
function vkind(it){return (vari==='with-icon' && it.has_icon) ? 'with-icon' : 'letters'}
function snip(it){
  const u = `https://raw.githubusercontent.com/${DATA.owner}/${DATA.repo}/${DATA.branch}/badges/${vkind(it)}/${it.dir}/${it.id}.svg`;
  if(fmt==='md') return `![${it.label}](${u})`;
  if(fmt==='html') return `<img src="${u}" alt="${it.label}" height="${DATA.height}" />`;
  return u;
}
function toast(t){const e=$('#toast');e.textContent=t;e.classList.add('show');clearTimeout(toast.t);toast.t=setTimeout(()=>e.classList.remove('show'),1400)}
async function copy(text,msg){
  try{await navigator.clipboard.writeText(text)}
  catch(e){const a=document.createElement('textarea');a.value=text;document.body.appendChild(a);a.select();document.execCommand('copy');a.remove()}
  toast(msg)
}
function visible(){
  const s=q.trim().toLowerCase();
  return DATA.categories.map(c=>({name:c.name,items:c.items.filter(i=>(!cat||c.name===cat)&&(!s||i.label.toLowerCase().includes(s)||i.id.includes(s)))})).filter(c=>c.items.length);
}
function render(){
  const vis=visible(), box=$('#list'); box.innerHTML='';
  if(!vis.length){box.innerHTML='<p class="empty">Ничего не найдено.</p>';return}
  for(const c of vis){
    const h=document.createElement('h2');h.textContent=c.name;box.appendChild(h);
    const g=document.createElement('div');g.className='grid';
    for(const it of c.items){
      const b=document.createElement('button');b.className='card';b.type='button';
      b.innerHTML=`<img src="badges/${vkind(it)}/${it.dir}/${it.id}.svg" alt="${it.label}"><span>${(vari==='with-icon' && !it.has_icon) ? 'Только с буквами' : 'Нажмите, чтобы скопировать'}</span>`;
      b.onclick=()=>copy(snip(it),`Скопировано: ${it.label}`);
      g.appendChild(b);
    }
    box.appendChild(g);
  }
}
function chips(){
  const w=$('#chips');
  const mk=(n,v)=>{const b=document.createElement('button');b.textContent=n;b.setAttribute('aria-pressed',cat===v);b.onclick=()=>{cat=v;chips();render()};w.appendChild(b)};
  w.innerHTML='';mk('Все','');DATA.categories.forEach(c=>mk(c.name,c.name));
}
$('#q').oninput=e=>{q=e.target.value;render()};
$('#vari').onclick=e=>{const v=e.target.dataset.v;if(!v)return;vari=v;[...$('#vari').children].forEach(b=>b.setAttribute('aria-pressed',b.dataset.v===v));render()};
$('#fmt').onclick=e=>{const f=e.target.dataset.f;if(!f)return;fmt=f;[...$('#fmt').children].forEach(b=>b.setAttribute('aria-pressed',b.dataset.f===f))};
$('#copyAll').onclick=()=>{const all=visible().flatMap(c=>c.items);copy(all.map(snip).join('\n'),`Скопировано бейджей: ${all.length}`)};
chips();render();
</script>
</body>
</html>
"""


def prepare(cfg):
    for cat in cfg["categories"]:
        for it in cat["items"]:
            it["dir"] = cat["slug"]
            it["has_icon"] = bool(it.get("svg")) or (ROOT / "icons" / f'{it["id"]}.svg').exists()
    return cfg


def build_all():
    cfg = prepare(json.loads(CFG.read_text(encoding="utf-8")))
    OUT.mkdir(exist_ok=True)
    keep = set()

    def write(variant, cat, it, use_icon):
        d = OUT / variant / cat["slug"]
        d.mkdir(parents=True, exist_ok=True)
        f = d / f'{it["id"]}.svg'
        f.write_text(make_svg(it, cfg["height"], use_icon), encoding="utf-8")
        keep.add(f)

    for cat in cfg["categories"]:
        for it in cat["items"]:
            write("letters", cat, it, False)
            if it["has_icon"]:
                write("with-icon", cat, it, True)
    for f in OUT.rglob("*.svg"):   # удаляем устаревшие (в т.ч. из старых структур)
        if f not in keep:
            f.unlink()
    for d in sorted((x for x in OUT.rglob("*") if x.is_dir()), key=lambda x: len(x.parts), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()
    (ROOT / "README.md").write_text(build_readme(cfg), encoding="utf-8")
    data = {k: cfg[k] for k in ("owner", "repo", "branch", "height", "categories")}
    (ROOT / "index.html").write_text(HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    n_icon = sum(1 for k in keep if k.parts[-3] == "with-icon")
    print(f"Готово: {len(keep)} SVG ({n_icon} с иконкой, {len(keep) - n_icon} с буквами), README.md и index.html обновлены.")


def add(argv):
    if len(argv) < 3:
        sys.exit('Использование: python build.py add "Название" ЦВЕТ ИК [Категория] [папка]')
    label, color, icon = argv[0], argv[1].lstrip("#"), argv[2]
    catname = argv[3] if len(argv) > 3 else "Другое"
    catslug = argv[4] if len(argv) > 4 else "other"
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    bid = "".join(ch if ch.isalnum() else "-" for ch in label.lower().replace("#", "sharp").replace("+", "p")).strip("-")
    cat = next((c for c in cfg["categories"] if c["name"] == catname), None)
    if not cat:
        cat = {"name": catname, "slug": catslug, "items": []}
        cfg["categories"].append(cat)
    cat["items"] = [i for i in cat["items"] if i["id"] != bid] + [{"id": bid, "label": label, "color": color.upper(), "icon": icon}]
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    build_all()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "add":
        add(sys.argv[2:])
    else:
        build_all()
