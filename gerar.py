"""Cards de 5 s do GTA 6 para o canal @LevelzIT (roda no PC ou no GitHub Actions).

Para cada short em roteiros/dia-XX.json:
  1. foto: screenshot oficial (campo "foto" = arquivo OU pasta dentro de VideosGTA6-oficial/GTAVI_Screenshots;
     pasta = pega a foto usada há mais tempo; caminhos relativos a fotos-oficiais/) — ou fotos/dia-XX/<id>.jpg
  2. card (modelo/card.html) renderizado pelo Edge
  3. fundo em loop (pôr do sol do Trailer 1, câmera lenta, 5,1 s sem emenda) + vidro + card + música
  4. saida/dia-XX/<id>.mp4 + painel.html com horário, título e descrição

Só gera o que falta. Para refazer: apague o .mp4.  Uso: python gerar.py [dia-XX]
"""
import glob
import html
import json
import os
import subprocess
import sys
import time
import urllib.parse

import navegador

BASE = os.path.dirname(os.path.abspath(__file__))
SCREENS = os.path.join(BASE, "fotos-oficiais")
FUNDO = os.path.join(BASE, "assets", "fundo-gta-tramonto.mp4")
MUSICAS = sorted(glob.glob(os.path.join(BASE, "musica", "*.mp3")))
CARD = os.path.join(BASE, "modelo", "card.html")
USO = os.path.join(BASE, "uso-fotos.json")
CANAL = "@LevelzIT"     # aparece no rodapé do card
QUADROS = 154         # 30 fps → 5,13 s; o loop fecha sem emenda
DURACAO = QUADROS / 30
VOLUME = 0.7
EXT_FOTO = (".jpg", ".jpeg", ".png", ".webp")
SEM_JANELA = 0x08000000 if os.name == "nt" else 0


def log(*a):
    print(*a, flush=True)


def rodar(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=SEM_JANELA)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[-1500:])
    return r


def foto_do_short(pasta_fotos, s):
    for ext in EXT_FOTO:
        p = os.path.join(pasta_fotos, s["id"] + ext)
        if os.path.exists(p):
            return p
    alvo = os.path.join(SCREENS, s.get("foto", ""))
    if not os.path.exists(alvo):                 # tolera "People/Jason Duval" escrito com _ ou sem a pasta-mãe
        cand = [d for d in glob.glob(os.path.join(SCREENS, "**", "*"), recursive=True)
                if os.path.basename(d).lower().replace("_", " ") == os.path.basename(alvo).lower().replace("_", " ")]
        alvo = cand[0] if cand else alvo
    if os.path.isfile(alvo):
        return alvo
    if os.path.isdir(alvo):
        uso = json.load(open(USO, encoding="utf-8")) if os.path.exists(USO) else {}
        opcoes = sorted(f for f in glob.glob(os.path.join(alvo, "*")) if f.lower().endswith(EXT_FOTO))
        if opcoes:
            escolha = min(opcoes, key=lambda f: uso.get(os.path.relpath(f, SCREENS).replace("\\", "/"), 0))
            uso[os.path.relpath(escolha, SCREENS).replace("\\", "/")] = time.time()
            json.dump(uso, open(USO, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
            return escolha
    log(f"   ! foto não encontrada: {s.get('foto')}")
    return None


def renderizar_card(s, foto, destino):
    dados = {
        "foto": navegador.url_arquivo(foto) if foto else "",
        "posicao": s.get("posicao", ""), "credito": s.get("credito", "Rockstar Games"),
        "tag": s.get("tag", "Curiosità GTA 6"), "titulo": s["titulo"], "texto": s["texto"], "canal": CANAL,
    }
    navegador.print_pagina(navegador.url_arquivo(CARD, urllib.parse.quote(json.dumps(dados, ensure_ascii=False))),
                           destino, 1080, 1920)


def montar_video(card_png, destino, n):
    musica = MUSICAS[n % len(MUSICAS)]
    inicio = (20 + n * 23) % 120
    filtro = (
        f"[0:v]trim=end_frame={QUADROS},setpts=PTS-STARTPTS,setsar=1,split[a][b];"
        "[b]gblur=sigma=28,eq=brightness=-0.08[bl];"
        "[1:v]format=rgba,split[c1][c2];[c1]alphaextract[m];[bl][m]alphamerge[g];"
        "[a][g]overlay=shortest=1[t];[t][c2]overlay=shortest=1,format=yuv420p[v];"
        f"[2:a]afade=t=in:d=0.15,afade=t=out:st={DURACAO - 0.2:.3f}:d=0.2,volume={VOLUME}[au]"
    )
    rodar(["ffmpeg", "-v", "error", "-y", "-i", FUNDO, "-loop", "1", "-i", card_png,
           "-ss", str(inicio), "-i", musica, "-filter_complex", filtro,
           "-map", "[v]", "-map", "[au]", "-t", f"{DURACAO:.4f}",
           "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "160k",
           "-movflags", "+faststart", destino])


def textos_yt(s):
    tags = " ".join(s.get("hashtags", []))
    return s["titulo_yt"], f"{s.get('descricao', '').strip()}\n\n{tags}".strip()


def painel(pasta_saida, dia, shorts):
    itens = []
    for s in shorts:
        titulo, desc = textos_yt(s)
        mp4 = f"{s['id']}.mp4"
        existe = os.path.exists(os.path.join(pasta_saida, mp4))
        itens.append(f"""
<article>
  <div class="hora">{html.escape(s.get('hora', ''))}<small>#{s['id']}</small></div>
  {'<video src="' + mp4 + '" autoplay loop muted playsinline></video>' if existe else '<div class="falta">não gerado</div>'}
  <label>Título <button data-c="t{s['id']}">copiar</button></label>
  <textarea id="t{s['id']}" rows="2" readonly>{html.escape(titulo)}</textarea>
  <label>Descrição <button data-c="d{s['id']}">copiar</button></label>
  <textarea id="d{s['id']}" rows="5" readonly>{html.escape(desc)}</textarea>
  <small class="fonte">fonte: {html.escape(s.get('fonte', ''))}</small>
</article>""")
    pagina = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>GTA 6 cards — {dia}</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{--bg:#110d17;--card:#1b1524;--line:#33293f;--tx:#f1eaf7;--mut:#a497b3;--ac:#ffb347;--pk:#ff4fa3}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--tx);font:15px/1.4 system-ui,Segoe UI,sans-serif;padding:24px}}
h1{{margin:0 0 4px;font-size:22px}}p.sub{{margin:0 0 22px;color:var(--mut)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:18px}}
article{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px;display:flex;flex-direction:column;gap:6px}}
.hora{{font-weight:800;font-size:20px;color:var(--ac);display:flex;justify-content:space-between;align-items:baseline}}.hora small{{color:var(--mut);font-size:13px}}
video,.falta{{width:100%;aspect-ratio:9/16;border-radius:10px;background:#000;object-fit:cover}}.falta{{display:grid;place-items:center;color:var(--mut)}}
label{{display:flex;justify-content:space-between;align-items:center;color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.06em;margin-top:4px}}
textarea{{width:100%;resize:vertical;background:var(--bg);color:var(--tx);border:1px solid var(--line);border-radius:8px;padding:8px;font:13px/1.4 system-ui,sans-serif}}
.fonte{{color:var(--mut);font-size:11px}}
button{{background:var(--pk);color:#fff;border:0;border-radius:999px;padding:4px 12px;font-weight:700;cursor:pointer;font-size:12px}}button.ok{{background:#2ea043}}
</style></head><body>
<h1>GTA 6 — cards — {dia}</h1>
<p class="sub">{len(shorts)} shorts · agende cada um no horário marcado</p>
<div class="grid">{''.join(itens)}</div>
<script>
document.querySelectorAll('button[data-c]').forEach(b=>b.onclick=async()=>{{
  const t=document.getElementById(b.dataset.c);try{{await navigator.clipboard.writeText(t.value)}}catch(e){{t.select();document.execCommand('copy')}}
  b.textContent='copiado';b.classList.add('ok');setTimeout(()=>{{b.textContent='copiar';b.classList.remove('ok')}},1200)}});
</script></body></html>"""
    with open(os.path.join(pasta_saida, "painel.html"), "w", encoding="utf-8") as f:
        f.write(pagina)


def gerar_dia(arq):
    dia = os.path.splitext(os.path.basename(arq))[0]
    shorts = json.load(open(arq, encoding="utf-8"))["shorts"]
    pasta_fotos = os.path.join(BASE, "fotos", dia)
    pasta_saida = os.path.join(BASE, "saida", dia)
    pasta_cards = os.path.join(pasta_saida, "_cards")
    for p in (pasta_fotos, pasta_cards):
        os.makedirs(p, exist_ok=True)
    log(f"\n== {dia}: {len(shorts)} shorts")
    for n, s in enumerate(shorts):
        mp4 = os.path.join(pasta_saida, f"{s['id']}.mp4")
        if s.get("curiosita") or s.get("gameplay"):     # já vêm prontos (curiosita.py / biblioteca do painel)
            log(f" {s['id']} {'curiosità' if s.get('curiosita') else 'gameplay'}: {'ok' if os.path.exists(mp4) else 'NÃO GERADO'}")
            continue
        if os.path.exists(mp4):
            log(f" {s['id']} já existe")
            continue
        log(f" {s['id']} {s['titulo'][:60]}")
        try:
            foto = foto_do_short(pasta_fotos, s)
            card = os.path.join(pasta_cards, f"{s['id']}.png")
            renderizar_card(s, foto, card)
            montar_video(card, mp4, n)
            titulo, desc = textos_yt(s)
            with open(os.path.join(pasta_saida, f"{s['id']}-textos.txt"), "w", encoding="utf-8") as f:
                f.write(f"HORÁRIO: {s.get('hora', '')}\n\nTÍTULO:\n{titulo}\n\nDESCRIÇÃO:\n{desc}\n")
            log(f"    ok  ({os.path.relpath(foto, SCREENS) if foto else 'sem foto'})")
        except Exception as e:
            log(f"    ERRO: {e}")
    painel(pasta_saida, dia, shorts)
    log(f" painel: {os.path.join(pasta_saida, 'painel.html')}")


def main():
    alvo = sys.argv[1] if len(sys.argv) > 1 else None
    arquivos = sorted(glob.glob(os.path.join(BASE, "roteiros", "dia-*.json")))
    if alvo:
        arquivos = [a for a in arquivos if os.path.basename(a).startswith(alvo)]
    if not arquivos:
        raise SystemExit("Nenhum roteiro em roteiros\\dia-XX.json")
    for a in arquivos:
        gerar_dia(a)


if __name__ == "__main__":
    main()
