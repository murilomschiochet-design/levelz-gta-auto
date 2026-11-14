"""Página pro celular com as legendas do TikTok (botão copiar), publicada em lz-legendas.pages.dev.

Uso: python legendas_pagina.py dia-XX   -> gera site-legendas/index.html (só o dia: os cards de hoje; o que você copia some depois de alguns segundos)
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
        itens.append(f"""<article data-k="{dia}-{s['id']}"><div class="topo"><b>{html.escape(s['hora'])}</b><span>#{s['id']}</span></div>
<p>{html.escape(txt)}</p><button data-t="{html.escape(txt, quote=True)}">Copiar legenda</button></article>""")
    return f"<section><h2>{html.escape(rot.get('data', dia))} · {dia}</h2>{''.join(itens)}</section>"


def main():
    dias = sorted((os.path.basename(f)[:-5] for f in glob.glob(os.path.join(BASE, "roteiros", "dia-*.json"))),
                  key=lambda d: int(d.split("-")[1]))
    if len(sys.argv) > 1 and sys.argv[1] in dias:
        dias = dias[:dias.index(sys.argv[1]) + 1]
    secoes = bloco(dias[-1])
    pagina = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Legendas TikTok — Levelz IT</title>
<style>
:root{{--bg:#110d17;--card:#1b1524;--line:#33293f;--tx:#f1eaf7;--mut:#a497b3;--ac:#ffb347}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--tx);font:16px/1.45 system-ui,sans-serif;padding:16px}}
h1{{font-size:20px;margin:0 0 4px}}.sub{{color:var(--mut);margin:0 0 18px;font-size:14px}}
h2{{font-size:15px;color:var(--ac);margin:22px 0 10px;text-transform:uppercase;letter-spacing:.05em}}
article{{transition:opacity .6s,transform .6s;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:0 0 12px}}
.topo{{display:flex;justify-content:space-between;color:var(--mut);font-size:14px}}.topo b{{color:var(--tx);font-size:17px}}
p{{margin:8px 0 10px;font-size:15px;word-break:break-word}}
button{{width:100%;padding:14px;border:0;border-radius:10px;background:var(--ac);color:#0a0f0c;font:700 16px system-ui}}
button.ok{{background:#2ea043;color:#fff}}
article.saindo{{opacity:0;transform:translateX(40px)}}
.vazio{{display:none;text-align:center;color:var(--mut);padding:40px 10px;font-size:17px}}
.rodape{{text-align:center;margin-top:18px}}.rodape a{{color:var(--mut);font-size:13px}}
</style></head><body>
<h1>Legendas do TikTok</h1><p class="sub">Abra o rascunho no TikTok, toque em copiar aqui e cole na legenda. O que você copia sai da lista em alguns segundos.</p>
{secoes}
<div class="vazio" id="vazio">✅ Tudo postado hoje.<br>Os de amanhã aparecem aqui quando o robô terminar.</div>
<p class="rodape"><a href="#" id="mostrar">Mostrar de novo os que já copiei</a></p>
<script>
const CH = 'legendas-feitas';
let feitas = []; try {{ feitas = JSON.parse(localStorage.getItem(CH) || '[]'); }} catch (e) {{}}
const salvar = () => {{ try {{ localStorage.setItem(CH, JSON.stringify(feitas.slice(-60))); }} catch (e) {{}} }};
const conferir = () => {{ const v = [...document.querySelectorAll('article')].some(a => a.style.display !== 'none');
  document.getElementById('vazio').style.display = v ? 'none' : 'block'; }};
document.querySelectorAll('article').forEach(a => {{ if (feitas.includes(a.dataset.k)) a.style.display = 'none'; }});
conferir();
document.querySelectorAll('button[data-t]').forEach(b => b.onclick = async () => {{
  try {{ await navigator.clipboard.writeText(b.dataset.t); }} catch (e) {{
    const t = document.createElement('textarea'); t.value = b.dataset.t; document.body.appendChild(t); t.select();
    document.execCommand('copy'); t.remove(); }}
  b.textContent = 'Copiada ✓ (sai da lista em 5 s)'; b.classList.add('ok');
  const a = b.closest('article'); if (!feitas.includes(a.dataset.k)) {{ feitas.push(a.dataset.k); salvar(); }}
  setTimeout(() => {{ a.classList.add('saindo'); setTimeout(() => {{ a.style.display = 'none'; conferir(); }}, 650); }}, 5000);
}});
document.getElementById('mostrar').onclick = e => {{ e.preventDefault(); feitas = []; salvar();
  document.querySelectorAll('article').forEach(a => {{ a.style.display = ''; a.classList.remove('saindo');
    const b = a.querySelector('button'); b.textContent = 'Copiar legenda'; b.classList.remove('ok'); }}); conferir(); }};
</script></body></html>"""
    os.makedirs(SAIDA, exist_ok=True)
    with open(os.path.join(SAIDA, "index.html"), "w", encoding="utf-8") as f:
        f.write(pagina)
    print("página:", os.path.join(SAIDA, "index.html"))
    # agenda do Instagram pro relógio da Cloudflare (ig-relogio): só container + horário, sem token
    reg_arq = os.path.join(BASE, "saida", dias[-1], "instagram.json")
    reg = json.load(open(reg_arq, encoding="utf-8")) if os.path.exists(reg_arq) else {}
    itens = [{"id": k, "container": v["container"], "publicar": v["publicar"]} for k, v in reg.items()
             if v.get("container") and not v.get("publicado")]
    with open(os.path.join(SAIDA, "agenda-b959860fa121d428.json"), "w", encoding="utf-8") as f:
        json.dump({"dia": dias[-1], "itens": itens}, f)
    print("agenda do Instagram:", len(itens), "itens")


if __name__ == "__main__":
    main()
