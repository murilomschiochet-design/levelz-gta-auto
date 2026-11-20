"""Cortes de GAMEPLAY (vindos do painel cortes-gta pelo botão "Mandar pro Levelz") entrando no dia.

  python gameplay.py incluir dia-XX   -> pega os próximos cortes da fila (gameplay/fila.json), baixa os vídeos para
                                         saida/dia-XX/gN.mp4 e acrescenta no roteiro do dia como shorts com "gameplay": true.
Daí pra frente o resto do robô trata como qualquer short: subir.py (YouTube, dentro da cota), instagram.py e a página
de legendas do TikTok (só no canal italiano).

config.json:
  gameplay_por_dia        quantos cortes entram por dia (TikTok/Instagram recebem todos)
  gameplay_yt_por_dia     quantos desses vão também pro YouTube (o resto fica "so_social")
  horas_gameplay          horários (fuso do canal)
A fila é escrita pelo PC (cortes-gta/levelz.py). Cada item: {id, video, capa, titulo_yt, descricao, hashtags, legenda, criado}.
Longos: gameplay/longos.json (também do PC), 1 por dia: {id, partes[], sha256, tamanho, thumb, titulo_yt, descricao, tags}.
"""
import hashlib
import json
import os
import sys
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
FILA = os.path.join(BASE, "gameplay", "fila.json")
LONGOS = os.path.join(BASE, "gameplay", "longos.json")
CONFIG = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))


def baixar(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": "levelz-bot"})
    with urllib.request.urlopen(req, timeout=300) as r, open(destino + ".part", "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    os.replace(destino + ".part", destino)


def incluir(dia):
    """Monta o dia com a biblioteca: até `gameplay_por_dia` shorts + 1 vídeo longo de gameplay."""
    arq_rot = os.path.join(BASE, "roteiros", f"{dia}.json")
    rot = json.load(open(arq_rot, encoding="utf-8"))
    incluir_shorts(dia, rot)
    incluir_longo(dia, rot)
    json.dump(rot, open(arq_rot, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def incluir_shorts(dia, rot):
    if not os.path.exists(FILA):
        print("sem fila de gameplay")
        return
    fila = json.load(open(FILA, encoding="utf-8"))
    ja = [s for s in rot["shorts"] if s.get("gameplay")]
    if ja:
        print(f"{dia} já tem {len(ja)} cortes de gameplay")
        return
    n_dia = int(CONFIG.get("gameplay_por_dia", 0))
    n_yt = int(CONFIG.get("gameplay_yt_por_dia", 0))
    horas = CONFIG.get("horas_gameplay", [])
    livres = [it for it in fila["itens"] if not it.get("usado_em")][:min(n_dia, len(horas))]
    if not livres:
        print("fila de gameplay vazia")
        return
    pasta = os.path.join(BASE, "saida", dia)
    os.makedirs(pasta, exist_ok=True)
    novos = []
    for i, it in enumerate(livres):
        sid = f"g{i + 1}"
        mp4 = os.path.join(pasta, f"{sid}.mp4")
        try:
            baixar(it["video"], mp4)
            if it.get("capa"):
                baixar(it["capa"], os.path.join(pasta, f"{sid}-capa.jpg"))
        except Exception as e:
            print(f" {it['id']}: não baixou ({e}); fica pra amanhã")
            continue
        s = {"id": sid, "hora": horas[i], "tag": "Gameplay", "titulo": it["titulo_yt"][:60],
             "titulo_yt": it["titulo_yt"], "descricao": it.get("descricao", ""), "hashtags": it.get("hashtags", []),
             "legenda": it.get("legenda", ""), "gameplay": True, "origem": it["id"], "video_url": it["video"]}
        if len(novos) >= n_yt:
            s["so_social"] = True
        novos.append(s)
        it["usado_em"] = dia
        print(f" {sid} {horas[i]} {'YouTube+social' if not s.get('so_social') else 'só social'}: {it['titulo_yt'][:70]}")
    rot["shorts"] = sorted(rot["shorts"] + novos, key=lambda s: s["hora"])
    json.dump(fila, open(FILA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(novos)} cortes de gameplay no {dia}; {sum(1 for x in fila['itens'] if not x.get('usado_em'))} ainda na fila")


def incluir_longo(dia, rot):
    """O vídeo longo do dia vem da biblioteca (gameplay/longos.json): o PC deixa o vídeo em partes de até 24 MB no
    Cloudflare; aqui as partes são baixadas, juntadas e conferidas (sha256) em saida/dia-XX/longo.mp4."""
    if not os.path.exists(LONGOS):
        print("sem biblioteca de vídeos longos")
        return
    if (rot.get("longo") or {}).get("gameplay"):
        print(f"{dia} já tem o longo de gameplay")
        return
    bib = json.load(open(LONGOS, encoding="utf-8"))
    livres = [it for it in bib["itens"] if not it.get("usado_em")]
    if not livres:
        print("biblioteca de longos vazia")
        return
    it = livres[0]
    pasta = os.path.join(BASE, "saida", dia)
    os.makedirs(pasta, exist_ok=True)
    mp4 = os.path.join(pasta, "longo.mp4")
    try:
        h = hashlib.sha256()
        with open(mp4 + ".part", "wb") as f:
            for url in it["partes"]:
                req = urllib.request.Request(url, headers={"User-Agent": "levelz-bot"})
                with urllib.request.urlopen(req, timeout=300) as r:
                    while True:
                        b = r.read(1 << 20)
                        if not b:
                            break
                        h.update(b)
                        f.write(b)
        if h.hexdigest() != it["sha256"]:
            raise RuntimeError("o vídeo juntado não confere (sha256)")
        os.replace(mp4 + ".part", mp4)
        if it.get("thumb"):
            baixar(it["thumb"], os.path.join(pasta, "longo-thumb.jpg"))
    except Exception as e:
        print(f" longo {it['id']}: não baixou ({e}); fica pra amanhã")
        for a in (mp4, mp4 + ".part"):
            if os.path.exists(a):
                os.remove(a)
        return
    desc = it.get("descricao", "")
    json.dump({"descricao": desc}, open(os.path.join(pasta, "longo.json"), "w", encoding="utf-8"), ensure_ascii=False)
    rot["longo"] = {"hora": CONFIG.get("hora_longo", "18:00"), "titulo_yt": it["titulo_yt"], "descricao": desc,
                    "tags": it.get("tags", []), "gameplay": True, "origem": it["id"]}
    it["usado_em"] = dia
    json.dump(bib, open(LONGOS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f" longo {rot['longo']['hora']}: {it['titulo_yt'][:70]} ({os.path.getsize(mp4) / 1e6:.0f} MB); "
          f"{sum(1 for x in bib['itens'] if not x.get('usado_em'))} longos ainda na biblioteca")


def conferir(dia):
    """Depois do envio: o longo de gameplay que não chegou ao YouTube volta pra biblioteca."""
    reg = os.path.join(BASE, "saida", dia, "enviados.json")
    if os.path.exists(reg) and "longo" in json.load(open(reg, encoding="utf-8")):
        return
    devolver_longo(dia)


def devolver_longo(dia):
    """O longo não subiu no YouTube: volta pra biblioteca e sai num dos próximos dias."""
    arq_rot = os.path.join(BASE, "roteiros", f"{dia}.json")
    origem = (json.load(open(arq_rot, encoding="utf-8")).get("longo") or {}).get("origem")
    if not origem or not os.path.exists(LONGOS):
        return
    bib = json.load(open(LONGOS, encoding="utf-8"))
    for it in bib["itens"]:
        if it["id"] == origem and it.get("usado_em") == dia:
            it.pop("usado_em")
            print(f" longo {origem} voltou pra biblioteca")
    json.dump(bib, open(LONGOS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "incluir":
        incluir(sys.argv[2])
    elif len(sys.argv) >= 3 and sys.argv[1] == "conferir":
        conferir(sys.argv[2])
    else:
        print(__doc__)
