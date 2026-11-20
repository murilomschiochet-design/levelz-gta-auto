"""Reels no Instagram, publicados SOZINHOS no horário de cada short (API oficial da Meta, token que não expira).

O Instagram não tem agendamento pela API, então são 2 etapas:
  python instagram.py preparar dia-XX   -> (no Robô 2, logo depois de gerar os vídeos) sobe cada vídeo pro Instagram
                                           SEM publicar e guarda os "containers" em saida/dia-XX/instagram.json
  python instagram.py publicar          -> (workflow de hora em hora) publica os containers cujo horário já chegou
  python instagram.py teste <mp4>       -> só sobe 1 vídeo e confere se o Instagram aceitou (não publica)

Credenciais: IG_TOKEN e IG_USER_ID (variáveis/Secrets) ou, no PC, credenciais/instagram-<conta>.txt + IG_CONTA.
Os containers valem 24 h: tudo é preparado e publicado no mesmo dia.
"""
import datetime as dt
import glob
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

if os.name == "nt":
    try:
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass

BASE = os.path.dirname(os.path.abspath(__file__))
FUSO = ZoneInfo("Europe/Rome")
GRAPH = "https://graph.facebook.com/v23.0"
UA = {"User-Agent": "AreaPequenaShorts/1.0"}
CONFIG = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8")).get("instagram", {})
EXTRA_TAGS = CONFIG.get("hashtags_extra", [])


def credencial():
    tok, uid = os.environ.get("IG_TOKEN"), os.environ.get("IG_USER_ID")
    if not tok:
        conta = os.environ.get("IG_CONTA") or CONFIG.get("conta_pc")
        tok = open(os.path.join(BASE, "credenciais", f"instagram-{conta}.txt"), encoding="utf-8").read().strip().strip("()<>\"' ")
        uid = uid or CONFIG.get("user_id")
    return tok, uid


def api(metodo, caminho, tok, **params):
    url = caminho if caminho.startswith("http") else f"{GRAPH}/{caminho}"
    corpo = None
    if metodo == "GET":
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(dict(params, access_token=tok))
    else:
        corpo = urllib.parse.urlencode(dict(params, access_token=tok)).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=corpo, headers=UA, method=metodo), timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Instagram {e.code}: {e.read().decode('utf-8', 'replace')[:400]}")


def legenda(s):
    tags, vistos = [], set()
    for h in [h if h.startswith("#") else "#" + h for h in s.get("hashtags", [])] + EXTRA_TAGS:
        if h.lower() not in vistos and h.lower() != "#shorts":
            vistos.add(h.lower())
            tags.append(h)
    titulo = " ".join(w for w in s["titulo_yt"].split() if w.lower() != "#shorts")
    if s.get("legenda"):          # cortes de gameplay: legenda própria das redes (já vem com as hashtags)
        ja = {w.lower() for w in s["legenda"].split() if w.startswith("#")}
        extra = [t for t in tags if t.lower() not in ja][:3]
        return f"{s['legenda']} {' '.join(extra)}".strip()[:2200]
    desc = (s.get("descricao") or "").strip()
    return f"{titulo}\n\n{desc}\n\n{' '.join(tags[:25])}".strip()[:2200]


def subir(tok, uid, mp4, texto, story=False, tentativas=3):
    """Cria o container e manda o arquivo; o Instagram às vezes recusa um upload bom (ProcessingFailedError),
    então tenta de novo com um container novo, esperando um pouco entre as tentativas."""
    for i in range(tentativas):
        try:
            return _subir_uma(tok, uid, mp4, texto, story)
        except RuntimeError as e:
            if i == tentativas - 1:
                raise
            print(f"   tentativa {i + 1} falhou ({str(e)[:80]}); tentando de novo em {30 * (i + 1)} s")
            time.sleep(30 * (i + 1))


def _subir_uma(tok, uid, mp4, texto, story=False):
    """Cria o container (Reel ou story) e manda o arquivo (upload resumível). Devolve o id do container."""
    if story:
        c = api("POST", f"{uid}/media", tok, media_type="STORIES", upload_type="resumable")
    else:
        c = api("POST", f"{uid}/media", tok, media_type="REELS", upload_type="resumable", caption=texto,
                share_to_feed="true")
    tam = os.path.getsize(mp4)
    req = urllib.request.Request(c["uri"], data=open(mp4, "rb").read(), method="POST",
                                 headers=dict(UA, Authorization=f"OAuth {tok}", offset="0", file_size=str(tam)))
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"upload {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
    return c["id"]


def esperar(tok, cid, limite=600):
    fim = time.time() + limite
    while time.time() < fim:
        st = api("GET", cid, tok, fields="status_code,status").get("status_code")
        if st in ("FINISHED", "ERROR", "EXPIRED"):
            return st
        time.sleep(10)
    return "IN_PROGRESS"


def preparar(dia):
    tok, uid = credencial()
    rot = json.load(open(os.path.join(BASE, "roteiros", f"{dia}.json"), encoding="utf-8"))
    pasta = os.path.join(BASE, "saida", dia)
    reg_arq = os.path.join(pasta, "instagram.json")
    reg = json.load(open(reg_arq, encoding="utf-8")) if os.path.exists(reg_arq) else {}
    data = rot.get("data") or dt.datetime.now(FUSO).date().isoformat()
    n = len(rot["shorts"])
    com_story = {rot["shorts"][i]["id"] for i in sorted({0, n // 2, n - 1}) if n} if CONFIG.get("stories", True) else set()
    for s in rot["shorts"]:
        sk = f"story-{s['id']}"
        mp4 = os.path.join(pasta, f"{s['id']}.mp4")
        if s["id"] in com_story and sk not in reg and os.path.exists(mp4):
            try:
                cid = subir(tok, uid, mp4, "", story=True)
                st = esperar(tok, cid)
                base = reg[s["id"]]["publicar"] if s["id"] in reg else None   # o Reel pode ter sido remarcado
                quando = (dt.datetime.fromisoformat(base) if base else dt.datetime.combine(
                    dt.date.fromisoformat(data), dt.time(*map(int, s["hora"].split(":"))), FUSO)) + dt.timedelta(minutes=5)
                reg[sk] = {"container": cid, "status": st, "publicar": quando.isoformat(), "publicado": None}
                json.dump(reg, open(reg_arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print(f" {sk}: preparado ({st}), publica {quando:%d/%m %H:%M}")
            except Exception as e:
                print(f" {sk}: erro ao subir: {e}")
        mp4 = os.path.join(pasta, f"{s['id']}.mp4")
        if s["id"] in reg or not os.path.exists(mp4):
            continue
        try:
            cid = subir(tok, uid, mp4, legenda(s))
        except Exception as e:
            if not s.get("video_url"):
                print(f" {s['id']}: erro ao subir: {e}")
                continue
            # plano B (cortes de gameplay): o Instagram busca o vídeo no endereço dele em vez de receber o arquivo
            try:
                cid = api("POST", f"{uid}/media", tok, media_type="REELS", video_url=s["video_url"],
                          caption=legenda(s), share_to_feed="true")["id"]
                print(f" {s['id']}: upload direto falhou, foi pelo endereço do vídeo")
            except Exception as e2:
                print(f" {s['id']}: erro ao subir: {e} / pelo endereço: {e2}")
                continue
        st = esperar(tok, cid)
        quando = dt.datetime.combine(dt.date.fromisoformat(data), dt.time(*map(int, s["hora"].split(":"))), FUSO)
        reg[s["id"]] = {"container": cid, "status": st, "publicar": quando.isoformat(), "publicado": None}
        json.dump(reg, open(reg_arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f" {s['id']}: preparado ({st}), publica {quando:%d/%m %H:%M}")


def publicar():
    tok, uid = credencial()
    agora = dt.datetime.now(FUSO)
    for reg_arq in sorted(glob.glob(os.path.join(BASE, "saida", "dia-*", "instagram.json")))[-3:]:
        reg = json.load(open(reg_arq, encoding="utf-8"))
        mudou = False
        for sid, r in reg.items():
            if r.get("publicado") or r.get("status") not in ("FINISHED", "IN_PROGRESS"):
                continue
            quando = dt.datetime.fromisoformat(r["publicar"])
            if quando > agora or agora - quando > dt.timedelta(hours=20):
                continue
            if api("GET", r["container"], tok, fields="status_code").get("status_code") == "PUBLISHED":
                r["publicado"] = agora.isoformat(timespec="minutes")   # o relógio da Cloudflare já publicou
                print(f" {sid}: já publicado (relógio)")
                mudou = True
                continue
            if r["status"] != "FINISHED":
                r["status"] = esperar(tok, r["container"], 120)
                if r["status"] != "FINISHED":
                    print(f" {sid}: container {r['status']}, pulei")
                    mudou = True
                    continue
            try:
                p = api("POST", f"{uid}/media_publish", tok, creation_id=r["container"])
                r["publicado"], r["media_id"] = agora.isoformat(timespec="minutes"), p.get("id")
                print(f" {os.path.basename(os.path.dirname(reg_arq))} {sid}: publicado no Instagram ({p.get('id')})")
            except Exception as e:
                r["erro"] = str(e)[:300]
                print(f" {sid}: erro ao publicar: {e}")
            mudou = True
        if mudou:
            json.dump(reg, open(reg_arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "preparar":
        preparar(sys.argv[2])
    elif sys.argv[1] == "publicar":
        publicar()
    elif sys.argv[1] == "teste":
        tok, uid = credencial()
        cid = subir(tok, uid, sys.argv[2], "teste")
        print("container", cid, "->", esperar(tok, cid), "(não publicado)")


if __name__ == "__main__":
    main()
