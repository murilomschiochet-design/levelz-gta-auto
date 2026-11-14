"""Vídeo longo diário de GTA 6 (16:9, 1080p). Sem API paga: voz edge-tts (voz em config.json "voz").

  python longo/gerar_longo.py dia-NN    -> lê o campo "longo" de roteiros/dia-NN.json e gera em saida/dia-NN/:
                                           longo.mp4, longo-thumb.jpg e longo.json (descrição final com capítulos)
"longo": {hora, titulo_yt, descricao, tags, tags_desc, thumb:{foto, l1, l2, caixa, estilo, lado}, blocos:[{titulo, texto, fotos:[pastas]}]}
Monta: voz por frase -> legenda + título do bloco (Pillow) -> fotos do banco andando devagar (3 s cada, sem zoom)
       intercaladas com trechos curtos dos trailers oficiais -> música baixa -> video.mp4 + thumb.jpg + youtube.txt
"""
import asyncio
import glob
import json
import os
import random
import re
import subprocess
import sys

import edge_tts
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
LZ = os.path.dirname(AQUI)                       # raiz do repositório do canal
FOTOS = os.path.join(LZ, "fotos-oficiais")
MUSICAS = sorted(glob.glob(os.path.join(LZ, "musica", "*.mp3")))
CLIPES = sorted(glob.glob(os.path.join(LZ, "assets", "clipes", "*.mp4")))   # trechos de 3 s dos trailers oficiais (1080p)
F_TIT = os.path.join(LZ, "modelo", "fonts", "Anton-Regular.ttf")
F_TXT = os.path.join(LZ, "modelo", "fonts", "Inter.ttf")
CONFIG = json.load(open(os.path.join(LZ, "config.json"), encoding="utf-8"))
CANAL = re.search(r'CANAL = "([^"]+)"', open(os.path.join(LZ, "gerar.py"), encoding="utf-8").read()).group(1)
W, H, FPS, SLOT = 1920, 1080, 30, 3.0
PAUSA_FRASE, PAUSA_BLOCO = 0.30, 0.80
SEM_JANELA = 0x08000000 if os.name == "nt" else 0


def rodar(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", creationflags=SEM_JANELA)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[-1500:])
    return r


def duracao(arq):
    return float(rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arq]).stdout.strip())


def frases(txt):
    return [f.strip() for f in re.split(r"(?<=[.!?…])\s+", txt.strip()) if f.strip()]


async def falar(texto, voz, destino, sem):
    async with sem:
        for tentativa in range(4):
            try:
                await edge_tts.Communicate(texto, voz, rate="+0%").save(destino)
                return
            except Exception:
                await asyncio.sleep(2 + tentativa * 3)
        raise RuntimeError("TTS falhou: " + texto[:60])


def quebrar(draw, txt, fonte, larg):
    linhas, atual = [], ""
    for p in txt.split():
        t = (atual + " " + p).strip()
        if draw.textlength(t, font=fonte) <= larg:
            atual = t
        else:
            linhas.append(atual)
            atual = p
    return linhas + ([atual] if atual else [])


def tela_legenda(titulo, frase, canal, destino):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ft = ImageFont.truetype(F_TIT, 54)
    tw = d.textlength(titulo.upper(), font=ft)
    d.rounded_rectangle([60, 52, 60 + tw + 56, 52 + 84], 18, fill=(14, 10, 22, 210))
    d.rectangle([60, 52, 72, 136], fill=(255, 79, 163, 255))
    d.text((60 + 36, 52 + 42), titulo.upper(), font=ft, fill=(255, 179, 71, 255), anchor="lm")
    fs = ImageFont.truetype(F_TXT, 50)
    fs.set_variation_by_axes([700]) if hasattr(fs, "set_variation_by_axes") else None
    linhas = quebrar(d, frase, fs, 1560)
    alt = 64 * len(linhas) + 40
    y0 = H - 70 - alt
    d.rounded_rectangle([W / 2 - 840, y0, W / 2 + 840, y0 + alt], 22, fill=(0, 0, 0, 175))
    for i, l in enumerate(linhas):
        d.text((W / 2, y0 + 20 + 32 + i * 64), l, font=fs, fill=(255, 255, 255, 255), anchor="mm")
    fh = ImageFont.truetype(F_TIT, 34)
    d.text((W - 60, 94), canal, font=fh, fill=(255, 255, 255, 230), anchor="rm")
    im.save(destino)


def seg_foto(img, destino, direcao):
    # sem zoom: a foto preenche a tela com 12% de sobra e anda devagar (pra cima ou pro lado)
    if direcao == "cima":
        cr = f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*(1-t/{SLOT})"
    else:
        cr = f"crop={W}:{H}:(iw-{W})*t/{SLOT}:(ih-{H})/2"
    vf = f"scale={int(W * 1.12)}:{int(H * 1.12)}:force_original_aspect_ratio=increase,{cr},fps={FPS},format=yuv420p"
    rodar(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(SLOT), "-i", img, "-vf", vf, "-r", str(FPS),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", destino])


def seg_clipe(clipe, destino):
    rodar(["ffmpeg", "-v", "error", "-y", "-i", clipe, "-t", str(SLOT), "-vf", f"fps={FPS},format=yuv420p", "-r", str(FPS),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", destino])


def main():
    dia = sys.argv[1]
    rot = json.load(open(os.path.join(LZ, "roteiros", f"{dia}.json"), encoding="utf-8")).get("longo")
    if not rot:
        print("roteiro sem vídeo longo")
        return
    rot = dict(rot, voz=CONFIG["voz"], canal=CANAL)
    nome = dia
    out = os.path.join(LZ, "saida", dia)
    tmp = os.path.join(out, "_longo_tmp")
    os.makedirs(tmp, exist_ok=True)
    rnd = random.Random(nome)

    # 1) voz, frase por frase
    itens = []
    for b, bl in enumerate(rot["blocos"]):
        fr = frases(bl["texto"])
        for i, f in enumerate(fr):
            itens.append(dict(b=b, i=i, ultimo=i == len(fr) - 1, frase=f, mp3=os.path.join(tmp, f"v{b:02d}_{i:02d}.mp3")))

    async def tudo():
        sem = asyncio.Semaphore(4)
        await asyncio.gather(*[falar(x["frase"], rot["voz"], x["mp3"], sem) for x in itens if not os.path.exists(x["mp3"])])
    asyncio.run(tudo())

    # 2) áudio da voz com pausas + linha do tempo das legendas
    lista_a, lista_s, t = [], [], 0.0
    for x in itens:
        pausa = PAUSA_BLOCO if x["ultimo"] else PAUSA_FRASE
        wav = x["mp3"][:-4] + ".wav"
        if not os.path.exists(wav):
            rodar(["ffmpeg", "-v", "error", "-y", "-i", x["mp3"], "-af", f"apad=pad_dur={pausa}", "-ar", "44100", "-ac", "2", wav])
        dur = duracao(wav)
        png = os.path.join(tmp, f"s{x['b']:02d}_{x['i']:02d}.png")
        tela_legenda(rot["blocos"][x["b"]]["titulo"], x["frase"], rot["canal"], png)
        lista_a.append(f"file '{wav}'")
        lista_s.append((png, dur))
        x["ini"], t = t, t + dur
    total = t
    open(os.path.join(tmp, "voz.txt"), "w", encoding="utf-8").write("\n".join(lista_a).replace("\\", "/"))
    rodar(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "voz.txt"), "-c", "copy", os.path.join(tmp, "voz.wav")])
    with open(os.path.join(tmp, "leg.txt"), "w", encoding="utf-8") as f:
        f.write("ffconcat version 1.0\n")
        for png, dur in lista_s:
            f.write(f"file '{png.replace(chr(92), '/')}'\nduration {dur:.3f}\n")
        f.write(f"file '{lista_s[-1][0].replace(chr(92), '/')}'\n")

    # 3) imagens: 3 s cada, fotos do bloco + 1 trecho de trailer a cada 4
    fins = [x["ini"] for x in itens if x["i"] == 0][1:] + [total]
    usados, segs, n, clipes = {}, [], 0, CLIPES[:]
    rnd.shuffle(clipes)
    tempo = 0.0
    for b, bl in enumerate(rot["blocos"]):
        fotos = [f for p in bl["fotos"] for f in sorted(glob.glob(os.path.join(FOTOS, p, "*.jpg")))]
        rnd.shuffle(fotos)
        while tempo < fins[b] - 0.5:
            s = os.path.join(tmp, f"g{n:03d}.mp4")
            if n % 4 == 3:
                if not os.path.exists(s):
                    seg_clipe(clipes[(n // 4) % len(clipes)], s)
            else:
                cand = [f for f in fotos if usados.get(f, 0) == min(usados.get(g, 0) for g in fotos)] or fotos
                foto = cand[0]
                usados[foto] = usados.get(foto, 0) + 1
                if not os.path.exists(s):
                    seg_foto(foto, s, "cima" if n % 2 else "lado")
            segs.append(f"file '{s}'")
            tempo += SLOT
            n += 1
    open(os.path.join(tmp, "img.txt"), "w", encoding="utf-8").write("\n".join(segs).replace("\\", "/"))
    base = os.path.join(tmp, "base.mp4")
    rodar(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "img.txt"), "-c", "copy", base])

    # 4) junta tudo: base + legendas + voz + música baixa
    musica = MUSICAS[len(nome) % len(MUSICAS)]
    video = os.path.join(out, "longo.mp4")
    filtro = ("[1:v]format=rgba[lg];[0:v][lg]overlay=0:0:format=auto,format=yuv420p[v];"
              "[3:a]volume=0.10,afade=t=in:d=2[m];[2:a][m]amix=inputs=2:duration=first:dropout_transition=0,"
              f"afade=t=out:st={total - 2.5:.2f}:d=2.5[a]")
    rodar(["ffmpeg", "-v", "error", "-y", "-i", base, "-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "leg.txt"),
           "-i", os.path.join(tmp, "voz.wav"), "-stream_loop", "-1", "-i", musica, "-filter_complex", filtro,
           "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "21",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", video])

    # 5) miniatura e textos do YouTube
    sys.path.insert(0, LZ)
    import thumb_longo  # noqa: E402
    th = dict(rot["thumb"])
    th["foto"] = os.path.join(FOTOS, th["foto"])
    if os.path.isdir(th["foto"]):
        th["foto"] = max(glob.glob(os.path.join(th["foto"], "*.jpg")), key=os.path.getsize)
    th.setdefault("seta", False)
    thumb_longo.gerar(th, os.path.join(out, "longo-thumb.jpg"))
    caps, desc = [], rot["descricao"].strip()
    for x in itens:
        if x["i"] == 0:
            m, s = divmod(int(x["ini"]), 60)
            caps.append(f"{m}:{s:02d} {rot['blocos'][x['b']]['titulo']}")
    caps[0] = "0:00 " + caps[0].split(" ", 1)[1]
    NL = chr(10)
    final = desc + NL * 2 + NL.join(caps) + NL * 2 + " ".join(rot.get("tags_desc", []))
    json.dump({"descricao": final.strip()}, open(os.path.join(out, "longo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{nome}: {total / 60:.1f} min -> {video}")


if __name__ == "__main__":
    main()
