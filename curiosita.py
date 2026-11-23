"""Shorts de CURIOSIDADE (formato desde 24/11/2026): cenas da nossa gameplay trocando a cada 2-3 s, narração em
italiano (edge-tts, rápida e sem pausas) e legenda grande no meio da tela, palavra por palavra.

  python curiosita.py dia-XX      -> gera saida/dia-XX/<id>.mp4 para cada short com "curiosita": true do roteiro

Cada short do roteiro (escrito pela rotina das 08:30, veja ROTINA.md):
  {"id": "c1", "hora": "10:00", "curiosita": true, "gancho": "TRUCCO SEGRETO: PRIMA PERSONA",
   "texto": "Lo sapevi? In GTA 6 ...", "cenas": [{"de": "Lo sapevi", "cena": "20261123-000618-041"}, ...],
   "titulo_yt": "... #Shorts", "descricao": "...", "hashtags": [...], "legenda": "...", "fonte": "..."}
"de" = primeiras palavras da frase onde a cena entra (a 1ª cena entra no começo). As cenas vêm do banco
gameplay/cenas.json (o painel de cortes do PC corta e publica; folhas de contato em gameplay/cenas/folhas/).
"""
import asyncio
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.request

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass
import edge_tts

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))
BANCO = os.path.join(BASE, "gameplay", "cenas.json")
VOZ = CONFIG.get("voz", "it-IT-GiuseppeMultilingualNeural")
VELOCIDADE = "+18%"
PAUSA_MAX = 0.08          # silêncio máximo entre palavras (s)
CENA_DUR = 3.4            # cada cena do banco tem 3,5 s
FONTE = "Anton"           # modelo/fonts/Anton-Regular.ttf (instalada no workflow)


def rodar(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-600:])
    return r.stdout


def duracao(arq):
    return float(rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arq]).strip())


def norm(w):
    w = unicodedata.normalize("NFKD", w.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in w if not unicodedata.combining(c)))


# ---------------------------------------------------------------- voz
async def _tts(texto, destino):
    com = edge_tts.Communicate(texto, VOZ, rate=VELOCIDADE, boundary="WordBoundary")
    palavras = []
    with open(destino, "wb") as f:
        async for c in com.stream():
            if c["type"] == "audio":
                f.write(c["data"])
            elif c["type"] == "WordBoundary":
                palavras.append({"t": c["offset"] / 1e7, "d": c["duration"] / 1e7, "w": c["text"]})
    return palavras


def narrar(texto, base):
    """Gera base.mp3 (rápido, sem pausas longas) e devolve as palavras com o tempo já corrigido."""
    for tentativa in range(3):
        try:
            palavras = asyncio.run(_tts(texto, base + "-bruto.mp3"))
            if palavras:
                break
        except Exception as e:
            print(f"   voz: tentativa {tentativa + 1} falhou ({e})")
    else:
        raise RuntimeError("edge-tts não respondeu")
    trechos, novo, corte, ini = [], [], 0.0, 0.0
    for i, p in enumerate(palavras):
        fim_p = p["t"] + p["d"]
        prox = palavras[i + 1]["t"] if i + 1 < len(palavras) else None
        novo.append({"t": p["t"] - corte, "d": p["d"], "w": p["w"]})
        if prox is not None and prox - fim_p > PAUSA_MAX:
            trechos.append((ini, fim_p + PAUSA_MAX / 2))
            ini = prox - PAUSA_MAX / 2
            corte += (prox - fim_p) - PAUSA_MAX
    trechos.append((ini, None))
    filtro = "".join(f"[0:a]atrim=start={a:.3f}{f':end={b:.3f}' if b is not None else ''},asetpts=PTS-STARTPTS[s{k}];"
                     for k, (a, b) in enumerate(trechos))
    filtro += "".join(f"[s{k}]" for k in range(len(trechos))) + f"concat=n={len(trechos)}:v=0:a=1[o]"
    rodar(["ffmpeg", "-y", "-v", "error", "-i", base + "-bruto.mp3", "-filter_complex", filtro, "-map", "[o]",
           "-c:a", "libmp3lame", "-q:a", "2", base + ".mp3"])
    os.remove(base + "-bruto.mp3")
    return novo


# ---------------------------------------------------------------- legenda
def ts(s):
    h, r = divmod(max(0, s), 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def legenda_ass(palavras, texto, gancho, fim, destino):
    """Grupos de até 3 palavras no meio da tela (quebra na pontuação do texto); a palavra falada fica amarela."""
    tokens = texto.split()
    if len(tokens) == len(palavras):
        for p, tk in zip(palavras, tokens):
            if tk[-1] in ".?!,:;":
                p["quebra"] = True
    for i, p in enumerate(palavras[:-1]):
        if palavras[i + 1]["t"] - (p["t"] + p["d"]) > 0.3:
            p["quebra"] = True
    grupos, atual = [], []
    for p in palavras:
        atual.append(p)
        if len(atual) == 3 or p.get("quebra") or p is palavras[-1]:
            grupos.append(atual)
            atual = []
    esc = lambda s: s.replace("{", "(").replace("}", ")").upper()
    linhas = []
    if gancho:
        linhas.append(f"Dialogue: 1,{ts(0)},{ts(3.2)},Gancho,,0,0,0,,{{\\an5\\pos(540,330)\\fad(0,250)"
                      f"\\t(0,180,\\fscx110\\fscy110)\\t(180,320,\\fscx100\\fscy100)}}{esc(gancho)}")
    for gi, g in enumerate(grupos):
        for i, p in enumerate(g):
            prox = g[i + 1]["t"] if i + 1 < len(g) else (grupos[gi + 1][0]["t"] if gi + 1 < len(grupos) else fim)
            txt = " ".join(("{\\c&H00E5FF&}" + esc(q["w"]) + "{\\c&HFFFFFF&}") if q is p else esc(q["w"]) for q in g)
            pop = "\\t(0,90,\\fscx110\\fscy110)\\t(90,160,\\fscx100\\fscy100)" if i == 0 else ""
            linhas.append(f"Dialogue: 0,{ts(p['t'])},{ts(prox)},Legenda,,0,0,0,,{{\\an5\\pos(540,960){pop}}}{txt}")
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Legenda,{FONTE},138,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,2,0,1,10,4,5,50,50,0,1
Style: Gancho,{FONTE},124,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,10,0,5,50,50,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    open(destino, "w", encoding="utf-8-sig").write(cab + "\n".join(linhas) + "\n")


# ---------------------------------------------------------------- cenas
def achar_inicio(palavras, frase, depois):
    alvo = [norm(w) for w in frase.split() if norm(w)][:4]
    ws = [norm(p["w"]) for p in palavras]
    for i in range(depois, len(ws)):
        if ws[i:i + len(alvo)] == alvo:
            return i
    for i in range(depois, len(ws)):          # aceita só as 2 primeiras palavras
        if ws[i:i + 2] == alvo[:2]:
            return i
    return None


def baixar(url, destino):
    if os.path.exists(destino):
        return
    for tentativa in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "levelz-bot"})
            with urllib.request.urlopen(req, timeout=120) as r, open(destino + ".part", "wb") as f:
                f.write(r.read())
            os.replace(destino + ".part", destino)
            return
        except Exception as e:
            if tentativa == 2:
                raise RuntimeError(f"cena não baixou: {url} ({e})")


def plano_de_cenas(s, palavras, fim, banco):
    """Lista de (cena_id, duração). Cena mais longa que 3,4 s continua na cena seguinte do banco."""
    por_id = {c["id"]: c for c in banco}
    marcas, depois = [], 0
    for k, c in enumerate(s.get("cenas", [])):
        if c.get("cena") not in por_id:
            print(f"   cena desconhecida {c.get('cena')}: pulei")
            continue
        i = 0 if not marcas else achar_inicio(palavras, c.get("de", ""), depois)
        if i is None:
            print(f"   não achei \"{c.get('de')}\" na narração: pulei essa cena")
            continue
        t = 0.0 if not marcas else palavras[i]["t"]
        if marcas and t - marcas[-1][1] < 0.6:      # cena curta demais: troca a anterior
            marcas[-1] = (c["cena"], marcas[-1][1])
            continue
        marcas.append((c["cena"], t))
        depois = i + 1
    if not marcas:
        raise RuntimeError("nenhuma cena válida no roteiro")
    plano = []
    for k, (cid, t) in enumerate(marcas):
        d = (marcas[k + 1][1] if k + 1 < len(marcas) else fim) - t
        atual = cid
        while d > 0.05:
            pedaço = min(d, CENA_DUR)
            plano.append((atual, pedaço))
            d -= pedaço
            c = por_id[atual]
            prox = f"{c['sessao']}-{c['n'] + 1:03d}"
            atual = prox if prox in por_id else atual
    return plano


# ---------------------------------------------------------------- montagem
def gerar_short(s, pasta, banco):
    base = os.path.join(pasta, f"_{s['id']}-voz")
    palavras = narrar(s["texto"], base)
    fim = duracao(base + ".mp3") + 0.5
    ass = os.path.join(pasta, f"_{s['id']}.ass")
    legenda_ass([dict(p) for p in palavras], s["texto"], s.get("gancho", ""), fim, ass)
    plano = plano_de_cenas(s, palavras, fim, banco)
    pasta_cenas = os.path.join(BASE, "saida", "_cenas")
    os.makedirs(pasta_cenas, exist_ok=True)
    por_id = {c["id"]: c for c in banco}
    entradas, partes = [], []
    for i, (cid, d) in enumerate(plano):
        arq = os.path.join(pasta_cenas, cid + ".mp4")
        baixar(por_id[cid]["url"], arq)
        entradas += ["-t", f"{d:.3f}", "-i", arq]
        partes.append(f"[{i}:v]scale=1080:1920,setsar=1,fps=30,trim=duration={d:.3f},setpts=PTS-STARTPTS[v{i}];"
                      f"[{i}:a]aresample=48000,apad,atrim=duration={d:.3f},asetpts=PTS-STARTPTS,volume=0.10[a{i}];")
    n = len(plano)
    entradas += ["-i", base + ".mp3"]
    filtro = "".join(partes) + "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac];"
    filtro += f"[vc]subtitles='{os.path.basename(ass)}':fontsdir='../../modelo/fonts'[vf];"   # cwd = saida/dia-XX
    filtro += f"[{n}:a]volume=1.6,apad[vz];[ac][vz]amix=inputs=2:duration=first:normalize=0[af]"
    saida = os.path.join(pasta, f"{s['id']}.mp4")
    r = subprocess.run(["ffmpeg", "-y", "-v", "error"] + entradas + ["-filter_complex", filtro, "-map", "[vf]", "-map", "[af]",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-maxrate", "3500k", "-bufsize", "7M",   # < 10 MB (TikTok)
                        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", saida],
                       cwd=pasta, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-600:])
    for a in (base + ".mp3", ass):
        os.remove(a)
    return saida, [cid for cid, _ in plano], duracao(saida)


def main(dia):
    rot = json.load(open(os.path.join(BASE, "roteiros", f"{dia}.json"), encoding="utf-8"))
    shorts = [s for s in rot.get("shorts", []) if s.get("curiosita")]
    if not shorts:
        print(f"{dia}: sem shorts de curiosidade")
        return
    banco_doc = json.load(open(BANCO, encoding="utf-8"))
    banco = banco_doc["itens"]
    pasta = os.path.join(BASE, "saida", dia)
    os.makedirs(pasta, exist_ok=True)
    usadas = {}
    for s in shorts:
        mp4 = os.path.join(pasta, f"{s['id']}.mp4")
        if os.path.exists(mp4):
            print(f" {s['id']} já existe")
            continue
        print(f" {s['id']} {s.get('hora', '')} {s.get('gancho', '')[:50]}")
        try:
            _, cenas, dur = gerar_short(s, pasta, banco)
            for c in cenas:
                usadas.setdefault(c, set()).add(dia)
            print(f"    ok: {dur:.1f} s, {len(cenas)} cenas")
        except Exception as e:
            print(f"    ERRO: {e}")
    for c in banco:
        if c["id"] in usadas:
            c["usos"] = sorted(set(c.get("usos", [])) | usadas[c["id"]])
    json.dump(banco_doc, open(BANCO, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
    else:
        main(sys.argv[1])
