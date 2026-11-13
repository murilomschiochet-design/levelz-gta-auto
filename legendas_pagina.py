"""Página pro celular com as legendas do TikTok (botão copiar), publicada em lz-legendas.pages.dev.

Uso: python legendas_pagina.py dia-XX   -> gera site-legendas/index.html (dia mais recente + 2 anteriores)
O workflow publica a pasta com: npx wrangler pages deploy site-legendas --project-name lz-legendas
"""
import glob
import html
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, "site-legendas")


def legenda(s):
    extra = "#gta6 #gtavi #videogiochi".split()
    tags, vistos = [], set()
    for h in [h if h.startswith("#") else "#" + h for h in s.get("hashtags", [])] + extra:
        if h.lower() not in vistos:
            vistos.add(h.lower())
            tags.append(h)
    titulo = " ".join(w for w in s["titulo_yt"].split() if w.lower() != "#shorts")   # #Shorts é só do YouTube
    return f"{titulo} {' '.join(tags)}".strip()[:2200]


def bloco(dia):
    rot = json.load(open(os.path.join(BASE, "roteiros", f"{dia}.json"), encoding="utf-8"))
    itens = []
    for s in rot["shorts"]:
        txt = legenda(s)
        itens.append(f"""<article><div class="topo"><b>{html.escape(s['hora'])}</b><span>#{s['id']}</span></div>
<p>{html.escape(txt)}</p><button data-t="{html.escape(txt, quote=True)}">Copiar legenda</button></article>""")
    return f"<section><h2>{html.escape(rot.get('data', dia))} · {dia}</h2>{''.join(itens)}</section>"


def main():
    dias = sorted((os.path.basename(f)[:-5] for f in glob.glob(os.path.join(BASE, "roteiros", "dia-*.json"))),
                  key=lambda d: int(d.split("-")[1]))
    if len(sys.argv) > 1 and sys.argv[1] in dias:
        dias = dias[:dias.index(sys.argv[1]) + 1]
    secoes = "".join(bloco(d) for d in reversed(dias[-3:]))
    pagina = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Legendas TikTok — Levelz IT</title>
<style>
:root{{--bg:#110d17;--card:#1b1524;--line:#33293f;--tx:#f1eaf7;--mut:#a497b3;--ac:#ffb347}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--tx);font:16px/1.45 system-ui,sans-serif;padding:16px}}
h1{{font-size:20px;margin:0 0 4px}}.sub{{color:var(--mut);margin:0 0 18px;font-size:14px}}
h2{{font-size:15px;color:var(--ac);margin:22px 0 10px;text-transform:uppercase;letter-spacing:.05em}}
article{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:0 0 12px}}
.topo{{display:flex;justify-content:space-between;color:var(--mut);font-size:14px}}.topo b{{color:var(--tx);font-size:17px}}
p{{margin:8px 0 10px;font-size:15px;word-break:break-word}}
button{{width:100%;padding:14px;border:0;border-radius:10px;background:var(--ac);color:#0a0f0c;font:700 16px system-ui}}
button.ok{{background:#2ea043;color:#fff}}
</style></head><body>
<h1>Legendas do TikTok</h1><p class="sub">Abra o rascunho no TikTok, toque em copiar aqui e cole na legenda.</p>
{secoes}
<script>
document.querySelectorAll('button[data-t]').forEach(b => b.onclick = async () => {{
  try {{ await navigator.clipboard.writeText(b.dataset.t); }} catch (e) {{
    const t = document.createElement('textarea'); t.value = b.dataset.t; document.body.appendChild(t); t.select();
    document.execCommand('copy'); t.remove(); }}
  b.textContent = 'Copiada ✓'; b.classList.add('ok');
}});
</script></body></html>"""
    os.makedirs(SAIDA, exist_ok=True)
    with open(os.path.join(SAIDA, "index.html"), "w", encoding="utf-8") as f:
        f.write(pagina)
    print("página:", os.path.join(SAIDA, "index.html"))


if __name__ == "__main__":
    main()
