"""Manda os cards do dia pro TikTok (@LevelzIT) como RASCUNHO (caixa de entrada do app). Você abre o TikTok e toca em Publicar.

  python tiktok.py login            -> uma vez, no PC: abre o TikTok, você autoriza. Guarda o token em credenciais/.
  python tiktok.py dia-XX           -> envia os shorts de saida/dia-XX/ (os que ainda não foram) pra caixa de entrada.
  python tiktok.py legendas dia-XX  -> mostra as legendas prontas (título + hashtags) pra colar no app.

Chaves do app (developers.tiktok.com): credenciais/tiktok.txt (linha 1 = Client Key, linha 2 = Client Secret)
ou variáveis TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET.
Token: credenciais/tiktok_token.json no PC; na nuvem, tiktok_token.enc no repositório (cifrado com TIKTOK_CHAVE).
O TikTok troca o refresh_token às vezes, por isso o token novo é sempre salvo de volta.
"""
import base64
import hashlib
import http.server
import json
import os
import secrets
import ssl
import sys
import time
import urllib.parse
import urllib.request
import webbrowser

if os.name == "nt":
    try:
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass

BASE = os.path.dirname(os.path.abspath(__file__))
CRED = os.path.join(BASE, "credenciais")
TOKEN_PC = os.path.join(CRED, "tiktok_token.json")
TOKEN_NUVEM = os.path.join(BASE, "tiktok_token.enc")
REDIRECT = "https://area-pequena-fc.pages.dev/tiktok-callback.html"
ESCOPOS = "user.info.basic,video.upload"
API = "https://open.tiktokapis.com/v2"
UA = {"User-Agent": "AreaPequenaShorts/1.0"}


def chaves():
    k, s = os.environ.get("TIKTOK_CLIENT_KEY"), os.environ.get("TIKTOK_CLIENT_SECRET")
    if not k:
        linhas = [l.strip() for l in open(os.path.join(CRED, "tiktok.txt"), encoding="utf-8") if l.strip()]
        k, s = (l.split("=")[-1].split(":")[-1].strip().strip("()<>\"' ") for l in linhas[:2])
    return k, s


def _req(url, dados=None, cab=None, metodo=None, corpo=None):
    h = dict(UA, **(cab or {}))
    if dados is not None:
        corpo = urllib.parse.urlencode(dados).encode()
        h["Content-Type"] = "application/x-www-form-urlencoded"
    r = urllib.request.Request(url, data=corpo, headers=h, method=metodo)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            txt = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "replace")
        raise SystemExit(f"TikTok respondeu {e.code}: {txt[:500]}")
    return json.loads(txt) if txt.strip().startswith("{") else txt


# ------------------------------------------------------------------ token (guardar / cifrar)

def _fernet():
    from cryptography.fernet import Fernet
    chave = os.environ["TIKTOK_CHAVE"].encode()
    return Fernet(chave)


def ler_token():
    if os.environ.get("TIKTOK_CHAVE") and os.path.exists(TOKEN_NUVEM):
        return json.loads(_fernet().decrypt(open(TOKEN_NUVEM, "rb").read()))
    if os.path.exists(TOKEN_PC):
        return json.load(open(TOKEN_PC, encoding="utf-8"))
    raise SystemExit("Sem login do TikTok. Rode: python tiktok.py login")


def salvar_token(t):
    t["salvo_em"] = int(time.time())
    if os.environ.get("TIKTOK_CHAVE"):
        open(TOKEN_NUVEM, "wb").write(_fernet().encrypt(json.dumps(t).encode()))
    else:
        os.makedirs(CRED, exist_ok=True)
        json.dump(t, open(TOKEN_PC, "w", encoding="utf-8"), indent=1)


def token_valido():
    t = ler_token()
    if time.time() < t.get("salvo_em", 0) + t.get("expires_in", 0) - 300:
        return t["access_token"]
    k, s = chaves()
    novo = _req(f"{API}/oauth/token/", {"client_key": k, "client_secret": s, "grant_type": "refresh_token",
                                        "refresh_token": t["refresh_token"]})
    if "access_token" not in novo:
        raise SystemExit(f"Não renovou o token do TikTok: {novo}")
    salvar_token(novo)
    return novo["access_token"]


# ------------------------------------------------------------------ login (uma vez, no PC)

def login():
    k, s = chaves()
    estado = secrets.token_urlsafe(16)
    verificador = secrets.token_urlsafe(48)
    desafio = base64.urlsafe_b64encode(hashlib.sha256(verificador.encode()).digest()).decode().rstrip("=")
    url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
        "client_key": k, "scope": ESCOPOS, "response_type": "code", "redirect_uri": REDIRECT, "state": estado,
        "code_challenge": desafio, "code_challenge_method": "S256"})
    recebido = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            recebido.update({a: b[0] for a, b in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            ok = "code" in recebido
            self.wfile.write(("<h2 style='font-family:sans-serif'>" + ("TikTok conectado. Pode fechar esta aba."
                              if ok else "Não autorizado: " + recebido.get("error_description", recebido.get("error", "?")))
                              + "</h2>").encode())

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 8765), H)
    print("Abrindo o TikTok no navegador... autorize com a conta do canal.")
    webbrowser.open(url)
    while not recebido:
        srv.handle_request()
    if recebido.get("state") != estado or "code" not in recebido:
        raise SystemExit(f"Login cancelado ou inválido: {recebido.get('error_description') or recebido.get('error') or 'state diferente'}")
    t = _req(f"{API}/oauth/token/", {"client_key": k, "client_secret": s, "code": recebido["code"],
                                    "grant_type": "authorization_code", "redirect_uri": REDIRECT,
                                    "code_verifier": verificador})
    if "access_token" not in t:
        raise SystemExit(f"Token não veio: {t}")
    salvar_token(t)
    info = _req(f"{API}/user/info/?fields=display_name", cab={"Authorization": f"Bearer {t['access_token']}"})
    u = (info.get("data") or {}).get("user") or {}
    print(f"Login ok. Conta TikTok: {u.get('display_name')}")


# ------------------------------------------------------------------ envio pra caixa de entrada

def enviar_video(token, mp4):
    tam = os.path.getsize(mp4)
    ini = _req(f"{API}/post/publish/inbox/video/init/", cab={"Authorization": f"Bearer {token}",
                                                            "Content-Type": "application/json; charset=UTF-8"},
               corpo=json.dumps({"source_info": {"source": "FILE_UPLOAD", "video_size": tam,
                                                 "chunk_size": tam, "total_chunk_count": 1}}).encode(), metodo="POST")
    if (ini.get("error") or {}).get("code") not in (None, "ok"):
        raise SystemExit(f"TikTok recusou: {ini['error']}")
    d = ini["data"]
    _req(d["upload_url"], cab={"Content-Type": "video/mp4", "Content-Length": str(tam),
                               "Content-Range": f"bytes 0-{tam - 1}/{tam}"},
         corpo=open(mp4, "rb").read(), metodo="PUT")
    return d["publish_id"]


def status(token, pid):
    r = _req(f"{API}/post/publish/status/fetch/", cab={"Authorization": f"Bearer {token}",
                                                        "Content-Type": "application/json; charset=UTF-8"},
             corpo=json.dumps({"publish_id": pid}).encode(), metodo="POST")
    return (r.get("data") or {}).get("status", "?"), (r.get("data") or {}).get("fail_reason", "")


def conferir(token, reg, pasta, tentar_de_novo=True):
    """Espera o TikTok processar (até ~8 min). O que travar em PROCESSING_UPLOAD é reenviado 1 vez."""
    pend = {k: v for k, v in reg.items() if v.get("status") not in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE")}
    for _ in range(16):
        if not pend:
            break
        time.sleep(30)
        for k in list(pend):
            st, motivo = status(token, pend[k]["publish_id"])
            reg[k]["status"] = st
            if st != "PROCESSING_UPLOAD":
                print(f" {k}: {st} {motivo}")
                pend.pop(k)
    for k in pend:
        print(f" {k}: travado em PROCESSING_UPLOAD" + (" — reenviando" if tentar_de_novo else ""))
        if tentar_de_novo:
            reg[k]["publish_id"] = enviar_video(token, os.path.join(pasta, f"{k}.mp4"))
            reg[k]["status"] = "reenviado"
    return reg


def legenda(s):
    extra = "#gta6 #gtavi #videogiochi".split()
    tags, vistos = [], set()
    for h in [h if h.startswith("#") else "#" + h for h in s.get("hashtags", [])] + extra:
        if h.lower() not in vistos:
            vistos.add(h.lower())
            tags.append(h)
    titulo = " ".join(w for w in s["titulo_yt"].split() if w.lower() != "#shorts")   # #Shorts é só do YouTube
    return f"{titulo} {' '.join(tags)}".strip()[:2200]


def enviar_dia(dia):
    rot = json.load(open(os.path.join(BASE, "roteiros", f"{dia}.json"), encoding="utf-8"))
    pasta = os.path.join(BASE, "saida", dia)
    reg_arq = os.path.join(pasta, "tiktok.json")
    reg = json.load(open(reg_arq, encoding="utf-8")) if os.path.exists(reg_arq) else {}
    token = token_valido()
    for s in rot["shorts"]:
        mp4 = os.path.join(pasta, f"{s['id']}.mp4")
        if s["id"] in reg or not os.path.exists(mp4):
            continue
        print(f" {s['id']}: {os.path.getsize(mp4)} bytes")
        pid = enviar_video(token, mp4)
        reg[s["id"]] = {"publish_id": pid, "legenda": legenda(s), "hora": s["hora"]}
        json.dump(reg, open(reg_arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f" {s['id']} na caixa de entrada do TikTok  ({s['hora']})  legenda: {legenda(s)}")
        time.sleep(3)
    if any(v.get("status") is None for v in reg.values()):
        reg = conferir(token, reg, pasta, tentar_de_novo=False)   # reenviar duplicava rascunhos e ativava o anti-spam
        json.dump(reg, open(reg_arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(pasta, "legendas-tiktok.txt"), "w", encoding="utf-8") as f:
        f.write("LEGENDAS DO TIKTOK - " + dia + " (copie ao publicar cada rascunho)\n\n")
        for s in rot["shorts"]:
            f.write(f"{s['hora']}  {legenda(s)}\n\n")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "login":
        login()
    elif sys.argv[1] == "legendas":
        rot = json.load(open(os.path.join(BASE, "roteiros", f"{sys.argv[2]}.json"), encoding="utf-8"))
        for s in rot["shorts"]:
            print(f"{s['hora']}  {legenda(s)}\n")
    else:
        enviar_dia(sys.argv[1])


if __name__ == "__main__":
    main()
