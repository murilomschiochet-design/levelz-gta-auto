"""Sobe e AGENDA os cards do dia no canal @LevelzIT (YouTube Data API, grátis).

  python subir.py login                 -> uma vez, no PC: abre o navegador, você escolhe a conta e o canal e clica em Permitir.
                                           Salva credenciais/token.json (fica só no PC; não mande pra ninguém).
  python subir.py segredos              -> mostra os NOMES das 3 variáveis que a rotina na nuvem precisa
                                           e grava os valores em credenciais/segredos-nuvem.txt (pra você colar nos Secrets do GitHub).
  python subir.py dia-XX [AAAA-MM-DD]   -> sobe os cards de saida/dia-XX agendados nos horários do roteiro, no fuso FUSO,
                                           na data do campo "data" do roteiro (sem ela: hoje, ou amanhã se o último horário já passou).
  --teste                                -> sobe só o primeiro short como PRIVADO e sem agendar (pra testar).

Na nuvem as credenciais vêm das variáveis YT_CLIENT_ID, YT_CLIENT_SECRET e YT_REFRESH_TOKEN.
Não sobe duas vezes: o que já foi enviado fica em saida/dia-XX/enviados.json.
"""
import datetime as dt
import json
import os
import sys
from zoneinfo import ZoneInfo

if os.name == "nt":                     # no PC: usa os certificados do Windows (o antivírus intercepta o SSL)
    try:
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass

BASE = os.path.dirname(os.path.abspath(__file__))
CRED = os.path.join(BASE, "credenciais")
FUSO = ZoneInfo(os.environ.get("YT_FUSO", "Europe/Rome"))
ESCOPOS = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]
CATEGORIA = "20"          # Gaming
CANAL_ESPERADO = "levelz"  # trava: só sobe se o canal autorizado tiver esse nome


def credenciais():
    from google.oauth2.credentials import Credentials
    if os.environ.get("YT_REFRESH_TOKEN"):
        return Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                           client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
                           token_uri="https://oauth2.googleapis.com/token", scopes=ESCOPOS)
    tok = os.path.join(CRED, "token.json")
    if not os.path.exists(tok):
        raise SystemExit("Sem login. Rode: python subir.py login")
    return Credentials.from_authorized_user_file(tok, ESCOPOS)


def login():
    from google_auth_oauthlib.flow import InstalledAppFlow
    segredo = os.path.join(CRED, "client_secret.json")
    if not os.path.exists(segredo):
        raise SystemExit("Falta credenciais\\client_secret.json (veja PASSO-A-PASSO-YOUTUBE.txt)")
    flow = InstalledAppFlow.from_client_secrets_file(segredo, ESCOPOS)
    cred = flow.run_local_server(port=0, prompt="select_account consent", access_type="offline")
    with open(os.path.join(CRED, "token.json"), "w", encoding="utf-8") as f:
        f.write(cred.to_json())
    canal = youtube(cred).channels().list(part="snippet", mine=True).execute()
    nomes = [c["snippet"]["title"] for c in canal.get("items", [])]
    print("Login ok. Canal autorizado:", ", ".join(nomes) or "(nenhum?)")
    if not any(CANAL_ESPERADO in n.lower() for n in nomes):
        os.remove(os.path.join(CRED, "token.json"))
        print("ATENÇÃO: não é o canal Levelz IT — apaguei esse login. Faça de novo escolhendo o Levelz IT.")


def segredos():
    t = json.load(open(os.path.join(CRED, "token.json"), encoding="utf-8"))
    linhas = [f"YT_CLIENT_ID={t['client_id']}", f"YT_CLIENT_SECRET={t['client_secret']}",
              f"YT_REFRESH_TOKEN={t['refresh_token']}"]
    arq = os.path.join(CRED, "segredos-nuvem.txt")
    with open(arq, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    print("Variáveis: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN")
    print("Valores gravados em", arq, "(não cole no chat; cole cada valor em GitHub > Settings > Secrets and variables > Actions)")


def youtube(cred=None):
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=cred or credenciais(), cache_discovery=False)


def enviar(yt, mp4, titulo, descricao, tags, publicar_em=None, privado=False):
    from googleapiclient.http import MediaFileUpload
    status = {"selfDeclaredMadeForKids": False}
    if publicar_em and not privado:
        status.update(privacyStatus="private", publishAt=publicar_em.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    else:
        status["privacyStatus"] = "private"
    corpo = {"snippet": {"title": titulo[:100], "description": descricao[:4900], "tags": tags[:15],
                         "categoryId": CATEGORIA, "defaultLanguage": "it", "defaultAudioLanguage": "it"},
             "status": status}
    req = yt.videos().insert(part="snippet,status", body=corpo,
                             media_body=MediaFileUpload(mp4, chunksize=8 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp["id"], resp.get("status", {})


def data_alvo(roteiro, arg):
    if arg:
        return dt.date.fromisoformat(arg)
    if roteiro.get("data"):
        return dt.date.fromisoformat(roteiro["data"])
    # sempre HOJE; só vai pra amanhã se o último horário do dia já passou (horário perdido vira "daqui a 20 min")
    agora = dt.datetime.now(FUSO)
    h, m = map(int, roteiro["shorts"][-1]["hora"].split(":"))
    ultimo = agora.replace(hour=h, minute=m, second=0, microsecond=0)
    return (agora + dt.timedelta(days=1)).date() if agora > ultimo - dt.timedelta(minutes=20) else agora.date()


def envios_locais_hoje():
    """Vídeos longos de gameplay que o PC já subiu direto (cortes-gta) contam na mesma cota do dia do YouTube
    (a cota zera à meia-noite do Pacífico)."""
    arq = os.path.join(BASE, "gameplay", "enviados_local.json")
    if not os.path.exists(arq):
        return 0
    pac = ZoneInfo("America/Los_Angeles")
    hoje = dt.datetime.now(pac).date()
    return sum(1 for e in json.load(open(arq, encoding="utf-8")) if dt.datetime.fromisoformat(e["enviado"]).astimezone(pac).date() == hoje)


def subir_dia(dia, data_txt=None, teste=False):
    roteiro = json.load(open(os.path.join(BASE, "roteiros", f"{dia}.json"), encoding="utf-8"))
    pasta = os.path.join(BASE, "saida", dia)
    reg_arq = os.path.join(pasta, "enviados.json")
    reg = json.load(open(reg_arq, encoding="utf-8")) if os.path.exists(reg_arq) else {}
    data = data_alvo(roteiro, data_txt)
    agora = dt.datetime.now(FUSO)
    yt = youtube()
    nomes = [c["snippet"]["title"] for c in yt.channels().list(part="snippet", mine=True).execute().get("items", [])]
    if not any(CANAL_ESPERADO in n.lower() for n in nomes):
        raise SystemExit(f"Canal autorizado errado: {nomes}. Não subi nada.")
    def item(s):
        return (s["id"], os.path.join(pasta, f"{s['id']}.mp4"), s["titulo_yt"],
                (s.get("descricao", "") + chr(10) * 2 + " ".join(s.get("hashtags", []))).strip(),
                [h.lstrip("#") for h in s.get("hashtags", [])], s["hora"])
    # cota do YouTube (≈6 envios/dia até a auditoria): longo + gameplay primeiro, os cards preenchem o resto.
    # O que não couber no YouTube continua indo pro TikTok e pro Instagram (so_social = só redes).
    cfg = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))
    limite = int(cfg.get("yt_max_envios", 6)) - envios_locais_hoje()
    longo = roteiro.get("longo")
    tem_longo = bool(longo and os.path.exists(os.path.join(pasta, "longo.mp4")))
    no_yt = [s for s in roteiro["shorts"] if not s.get("so_social")]
    gps = [s for s in no_yt if s.get("gameplay")]
    cards = [s for s in no_yt if not s.get("gameplay")]
    vagas = max(0, limite - (1 if tem_longo else 0))
    gps = gps[:vagas]
    cards = cards[:max(0, vagas - len(gps))]
    escolhidos = {s["id"] for s in gps + cards}
    fora = [s["id"] for s in no_yt if s["id"] not in escolhidos]
    if fora:
        print(" fora do YouTube hoje (cota):", ", ".join(fora), "— seguem no TikTok/Instagram")
    itens = [item(s) for s in roteiro["shorts"] if s["id"] in escolhidos]
    if tem_longo:
        extra = os.path.join(pasta, "longo.json")      # descrição final com os capítulos (gerada pelo longo/gerar_longo.py)
        desc_longo = json.load(open(extra, encoding="utf-8"))["descricao"] if os.path.exists(extra) else longo["descricao"]
        itens.insert(min(4, len(itens)), ("longo", os.path.join(pasta, "longo.mp4"), longo["titulo_yt"], desc_longo,
                                          longo.get("tags", []), longo["hora"]))
    proximo_atrasado = agora
    for sid, mp4, titulo, desc, tags, hora in itens:
        if sid in reg:
            print(f" {sid} já enviado ({reg[sid]['id']})")
            continue
        if not os.path.exists(mp4):
            print(f" {sid} sem vídeo, pulei")
            continue
        h, m = map(int, hora.split(":"))
        quando = dt.datetime.combine(data, dt.time(h, m), FUSO)
        if quando < agora + dt.timedelta(minutes=15):
            # horário já passou (robô rodou atrasado): espalha, 1 a cada 75 min a partir de daqui a 20 min
            quando = max(agora + dt.timedelta(minutes=20), proximo_atrasado)
            proximo_atrasado = quando + dt.timedelta(minutes=75)
        try:
            vid, st = enviar(yt, mp4, titulo, desc, tags, None if teste else quando, privado=teste)
        except Exception as e:
            if "quotaExceeded" in str(e) or "uploadLimitExceeded" in str(e):
                print(f" {sid}: cota diária do YouTube acabou — o resto fica pra depois (rode de novo amanhã)")
                break
            raise
        reg[sid] = {"id": vid, "publicar": None if teste else quando.isoformat(), "titulo": titulo}
        thumb = os.path.join(pasta, "longo-thumb.jpg")
        if sid == "longo" and os.path.exists(thumb):
            try:
                from googleapiclient.http import MediaFileUpload
                yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(thumb, mimetype="image/jpeg")).execute()
                print("  miniatura do longo aplicada")
            except Exception as e:      # canal sem verificação por telefone não aceita miniatura
                print(f"  miniatura não aplicada: {str(e)[:200]}")
        with open(reg_arq, "w", encoding="utf-8") as f:
            json.dump(reg, f, ensure_ascii=False, indent=1)
        print(f" {sid} enviado: https://youtu.be/{vid}  " + ("(privado, teste)" if teste else f"agendado {quando:%d/%m %H:%M}"))
        if teste:
            break


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    if cmd == "login":
        login()
    elif cmd == "segredos":
        segredos()
    else:
        args = [a for a in sys.argv[2:] if not a.startswith("--")]
        subir_dia(cmd, args[0] if args else None, teste="--teste" in sys.argv)


if __name__ == "__main__":
    main()
