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
# Готовые цвета: каждый бейдж собирается в каждом из них (badges/colors/ЦВЕТ/...).
# Свой список можно задать в badges.json ключом "colors".
DEFAULT_COLORS = ["3A9B68", "2563EB", "7C3AED", "DB2777", "DC2626", "EA580C",
                  "CA8A04", "16A34A", "0891B2", "374151", "111827", "F3F4F6"]
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
    L.append('2. **Через этот README:** посмотрите бейджи в таблицах ниже и скопируйте код категории '
             '(у каждой категории есть раскрывающиеся блоки с кодом: бейдж на строку, кнопка копирования в углу блока). '
             'Лишние строки просто удалите после вставки.')
    L.append(f'3. **Напрямую:** ссылка на бейдж имеет вид `{raw}/ВИД/КАТЕГОРИЯ/ИМЯ.svg`, '
             f'где ВИД это `with-icon` или `letters`.\n')
    L.append('Чтобы бейджи стояли по центру в профиле, оберните их в:\n')
    L.append('```html\n<div align="center">\n\n  <!-- сюда вставьте бейджи -->\n\n</div>\n```\n')
    L.append('Если хотите, чтобы бейдж был ссылкой, оберните его так: `[![Python](ссылка-на-бейдж)](https://python.org)`.\n')
    L.append('## Галерея\n')
    for cat in cfg["categories"]:
        L.append(f'### {cat["name"]}\n')
        L.append('| Название | С иконкой | С буквами |')
        L.append('|---|---|---|')
        for it in cat["items"]:
            alt = html.escape(it["label"])
            let_img = f'<img src="badges/letters/{it["dir"]}/{it["id"]}.svg" alt="{alt}" height="{h}" />'
            ico_img = (f'<img src="badges/with-icon/{it["dir"]}/{it["id"]}.svg" alt="{alt}" height="{h}" />'
                       if it["has_icon"] else '—')
            L.append(f'| {alt} | {ico_img} | {let_img} |')
        L.append('')
        icon_items = [i for i in cat["items"] if i["has_icon"]]
        if icon_items:
            L.append('<details><summary><b>Код: с иконками</b> (по одному бейджу на строку)</summary>\n')
            L.append('```markdown')
            L += [snippets(cfg, i, "with-icon")["md"] for i in icon_items]
            L.append('```\n')
            L.append('</details>\n')
        L.append('<details><summary><b>Код: с буквами</b> (по одному бейджу на строку)</summary>\n')
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
    L.append('Каждый бейдж собран во всех готовых цветах: `badges/colors/ЦВЕТ/ВИД/категория/имя.svg`. На странице-галерее нажмите «Свой» и кружок с цветом, и код возьмёт ссылку на нужный файл. Любой другой цвет можно выбрать палитрой: страница нарисует бейдж, его нужно скачать кнопкой «↓ SVG» и положить в `badges/custom/` (`build.py` эту папку не трогает).\n')
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
.colorbar{padding:10px 12px;border:1px solid var(--line);border-radius:10px;background:var(--card)}
.colorbar .lbl{color:var(--mute);font-size:13px}
#cpick{width:38px;height:34px;padding:0;border:1px solid var(--line);border-radius:6px;background:none;cursor:pointer}
#chex{width:92px;padding:8px 10px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--fg);font:13px ui-monospace,Consolas,monospace;text-transform:uppercase}
.sw{display:flex;flex-wrap:wrap;gap:6px}
.sw button{width:22px;height:22px;border-radius:50%;border:2px solid var(--line);padding:0;cursor:pointer}
.sw button[aria-pressed=true]{border-color:var(--fg)}
.note{margin:-4px 0 14px;font-size:13px;color:var(--mute)}
.note code{background:var(--card);border:1px solid var(--line);border-radius:4px;padding:0 4px}
.wrap{position:relative;display:flex}
.wrap .card{width:100%}
.dl{position:absolute;right:8px;top:8px;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:2px 8px;font:12px system-ui;cursor:pointer}
.dl:hover{border-color:var(--acc)}
#dlAll{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:8px 12px;font:inherit;cursor:pointer}
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
  <div class="bar colorbar" id="colorbar">
    <span class="lbl">Цвет плашки</span>
    <div class="seg" id="cmode">
      <button data-c="orig" aria-pressed="true">Как в оригинале</button>
      <button data-c="custom" aria-pressed="false">Свой</button>
    </div>
    <input type="color" id="cpick" value="#3a9b68" aria-label="Выбрать цвет">
    <input type="text" id="chex" maxlength="7" value="#3A9B68" spellcheck="false" aria-label="Цвет в формате HEX">
    <div class="sw" id="sw"></div>
    <button id="dlAll" type="button" hidden>Скачать показанные (SVG)</button>
  </div>
  <p class="note" id="cnote" hidden>Этого цвета нет в готовых (кружки выше), он рисуется прямо здесь. Нажмите на бейдж, чтобы скопировать код со ссылкой, и скачайте файл кнопкой «↓ SVG»: положите его в папку <code>badges/custom/</code> репозитория, иначе ссылка не заработает.</p>
  <div class="chips" id="chips"></div>
  <div id="list"></div>
</main>
<div id="toast" role="status"></div>
<script>
const DATA = __DATA__;
let fmt = 'md', vari = 'with-icon', cat = '', q = '';
const $ = s => document.querySelector(s);
let cmode = 'orig', ccolor = '#3A9B68';
try{const st=JSON.parse(localStorage.getItem('badge-color')||'null');if(st&&/^#[0-9a-f]{6}$/i.test(st.c)){ccolor=st.c.toUpperCase();cmode=st.m==='custom'?'custom':'orig'}}catch(e){}
function saveColor(){try{localStorage.setItem('badge-color',JSON.stringify({m:cmode,c:ccolor}))}catch(e){}}
const FONT="Verdana,'DejaVu Sans',Geneva,sans-serif";
const esc=t=>String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#x27;');
function lum(hex){const c=[0,2,4].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4));return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]}
function pyround(x){const r=Math.round(x);return(Math.abs(x%1)===0.5&&r%2!==0)?r-1:r}
function mkSvg(it,color,withIcon){
  const hex=color.replace('#','').toUpperCase(), label=it.label.toUpperCase();
  const fg=lum(hex)>0.45?'#1F1F1F':'#FFFFFF';
  const tl=Math.round(label.length*7.7*10)/10, w=pyround(32+tl+12), h=DATA.height;
  let icon;
  if(withIcon&&it.ibody){
    const vb=it.ivb, sc=14/Math.max(vb[2],vb[3]);
    const tx=9+(14-vb[2]*sc)/2-vb[0]*sc, ty=7+(14-vb[3]*sc)/2-vb[1]*sc;
    icon=`<g transform="translate(${tx.toFixed(2)} ${ty.toFixed(2)}) scale(${sc.toFixed(4)})" fill="${fg}" color="${fg}">${it.ibody}</g>`;
  }else{
    icon=`<rect x="8" y="6" width="16" height="16" rx="3" fill="${fg}" fill-opacity="0.2"/><text x="16" y="17.3" fill="${fg}" font-family="${FONT}" font-size="8" font-weight="bold" text-anchor="middle">${esc(it.icon)}</text>`;
  }
  const name=esc(it.label);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${name}">\n  <title>${name}</title>\n  <rect width="${w}" height="${h}" rx="2" fill="#${hex}"/>\n  ${icon}\n  <text x="32" y="18" fill="${fg}" font-family="${FONT}" font-size="10" font-weight="bold" textLength="${tl.toFixed(1)}" lengthAdjust="spacing">${esc(label)}</text>\n</svg>\n`;
}
const dataUri=svg=>'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);
function useIcon(it){return vari==='with-icon'&&it.has_icon}
function vkind(it){return useIcon(it)?'with-icon':'letters'}
function fileName(it){return `${it.id}-${ccolor.slice(1)}${useIcon(it)?'':'-letters'}.svg`}
function download(it){
  const blob=new Blob([mkSvg(it,ccolor,useIcon(it))],{type:'image/svg+xml'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=fileName(it);
  document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
}
function inPalette(){return DATA.colors.includes(ccolor.slice(1))}
function snip(it){
  const base=`https://raw.githubusercontent.com/${DATA.owner}/${DATA.repo}/${DATA.branch}/badges/`;
  let u=`${base}${vkind(it)}/${it.dir}/${it.id}.svg`;
  if(cmode==='custom') u=inPalette()?`${base}colors/${ccolor.slice(1)}/${vkind(it)}/${it.dir}/${it.id}.svg`:`${base}custom/${fileName(it)}`;
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
  const vis=visible(), box=$('#list'), custom=cmode==='custom'; box.innerHTML='';
  if(!vis.length){box.innerHTML='<p class="empty">Ничего не найдено.</p>';return}
  for(const c of vis){
    const h=document.createElement('h2');h.textContent=c.name;box.appendChild(h);
    const g=document.createElement('div');g.className='grid';
    for(const it of c.items){
      const w=document.createElement('div');w.className='wrap';
      const b=document.createElement('button');b.className='card';b.type='button';
      const src=custom?dataUri(mkSvg(it,ccolor,useIcon(it))):`badges/${vkind(it)}/${it.dir}/${it.id}.svg`;
      const hint=(vari==='with-icon'&&!it.has_icon)?'Только с буквами':'Нажмите, чтобы скопировать';
      b.innerHTML=`<img src="${src}" alt="${esc(it.label)}"><span>${hint}</span>`;
      const own=custom&&!inPalette();
      b.onclick=()=>copy(snip(it),own?'Скопировано. Файл скачайте кнопкой ↓ SVG':`Скопировано: ${it.label}`);
      w.appendChild(b);
      if(own){const d=document.createElement('button');d.className='dl';d.type='button';d.textContent='↓ SVG';d.title='Скачать '+fileName(it);d.onclick=()=>download(it);w.appendChild(d)}
      g.appendChild(w);
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
let rq=0;
function later(){cancelAnimationFrame(rq);rq=requestAnimationFrame(render)}
function syncColorUI(){
  [...$('#cmode').children].forEach(b=>b.setAttribute('aria-pressed',b.dataset.c===cmode));
  $('#cpick').value=ccolor.toLowerCase();$('#chex').value=ccolor;
  const cu=cmode==='custom',own=cu&&!inPalette();$('#cnote').hidden=!own;$('#dlAll').hidden=!own;
  [...$('#sw').children].forEach(b=>b.setAttribute('aria-pressed',cu&&b.dataset.c===ccolor));
}
function setColor(c,mode){if(c)ccolor=c.toUpperCase();if(mode)cmode=mode;saveColor();syncColorUI();later()}
DATA.colors.map(c=>'#'+c).forEach(c=>{
  const b=document.createElement('button');b.type='button';b.style.background=c;b.dataset.c=c;b.title=c;b.setAttribute('aria-label',c);
  b.onclick=()=>setColor(c,'custom');$('#sw').appendChild(b);
});
$('#cmode').onclick=e=>{const c=e.target.dataset.c;if(c)setColor(null,c)};
$('#cpick').oninput=e=>setColor(e.target.value,'custom');
$('#chex').oninput=e=>{let v=e.target.value.trim();if(v[0]!=='#')v='#'+v;if(/^#[0-9a-f]{6}$/i.test(v))setColor(v,'custom')};
$('#dlAll').onclick=()=>{const all=visible().flatMap(c=>c.items);all.forEach((it,i)=>setTimeout(()=>download(it),i*200));toast(`Скачивается файлов: ${all.length}`)};
syncColorUI();
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
            inner = (it["svg"], [0, 0, 24, 24]) if it.get("svg") else load_icon(it["id"])
            if inner:   # нужна странице, чтобы рисовать бейдж в выбранном цвете
                it["ibody"], it["ivb"] = inner
    return cfg


def build_all():
    cfg = prepare(json.loads(CFG.read_text(encoding="utf-8")))
    OUT.mkdir(exist_ok=True)
    keep = set()

    main = set()

    def write(variant, cat, it, use_icon, color=None):
        d = (OUT / "colors" / color if color else OUT) / variant / cat["slug"]
        d.mkdir(parents=True, exist_ok=True)
        f = d / f'{it["id"]}.svg'
        item = dict(it, color=color) if color else it
        f.write_text(make_svg(item, cfg["height"], use_icon), encoding="utf-8")
        keep.add(f)
        if not color:
            main.add(f)

    colors = [c.lstrip("#").upper() for c in cfg.get("colors", DEFAULT_COLORS)]

    for cat in cfg["categories"]:
        for it in cat["items"]:
            write("letters", cat, it, False)
            if it["has_icon"]:
                write("with-icon", cat, it, True)
            for col in colors:
                write("letters", cat, it, False, col)
                if it["has_icon"]:
                    write("with-icon", cat, it, True, col)
    for f in OUT.rglob("*.svg"):   # удаляем устаревшие (в т.ч. из старых структур)
        if f not in keep and f.relative_to(OUT).parts[0] != "custom":   # custom: ваши файлы со своим цветом
            f.unlink()
    for d in sorted((x for x in OUT.rglob("*") if x.is_dir()), key=lambda x: len(x.parts), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()
    (ROOT / "README.md").write_text(build_readme(cfg), encoding="utf-8")
    data = {k: cfg[k] for k in ("owner", "repo", "branch", "height", "categories")}
    data["colors"] = colors
    (ROOT / "index.html").write_text(HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")), encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    n_icon = sum(1 for k in main if k.parts[-3] == "with-icon")
    print(f"Готово: {len(main)} SVG ({n_icon} с иконкой, {len(main) - n_icon} с буквами) "
          f"+ {len(keep) - len(main)} в {len(colors)} готовых цветах, README.md и index.html обновлены.")


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
