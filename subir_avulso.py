"""Sobe UM vídeo (o longo de gameplay vindo do painel de cortes) direto do PC, agendado, com miniatura.

  python subir_avulso.py dados.json
dados.json: {"video": "...mp4", "thumb": "...jpg", "titulo": "...", "descricao": "...", "tags": [...],
             "publicar": "AAAA-MM-DDTHH:MM" (fuso do canal), "origem": "id do corte"}
Registra em gameplay/enviados_local.json (o subir.py da nuvem desconta da cota do dia).
Sai com código 3 se a cota diária do YouTube acabou.
"""
import datetime as dt
import json
import os
import sys

import subir

BASE = os.path.dirname(os.path.abspath(__file__))
REG = os.path.join(BASE, "gameplay", "enviados_local.json")


def main():
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    yt = subir.youtube()
    nomes = [c["snippet"]["title"] for c in yt.channels().list(part="snippet", mine=True).execute().get("items", [])]
    if not any(subir.CANAL_ESPERADO in n.lower() for n in nomes):
        raise SystemExit(f"Canal autorizado errado: {nomes}. Não subi nada.")
    quando = dt.datetime.fromisoformat(d["publicar"]).replace(tzinfo=subir.FUSO)
    agora = dt.datetime.now(subir.FUSO)
    if quando < agora + dt.timedelta(minutes=30):
        quando = agora + dt.timedelta(minutes=40)
    try:
        vid, _ = subir.enviar(yt, d["video"], d["titulo"], d["descricao"], d.get("tags", []), quando)
    except Exception as e:
        if "quotaExceeded" in str(e) or "uploadLimitExceeded" in str(e):
            print("COTA: a cota diária do YouTube acabou")
            sys.exit(3)
        raise
    if d.get("thumb") and os.path.exists(d["thumb"]):
        try:
            from googleapiclient.http import MediaFileUpload
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(d["thumb"], mimetype="image/jpeg")).execute()
        except Exception as e:
            print("miniatura não aplicada:", str(e)[:200])
    os.makedirs(os.path.dirname(REG), exist_ok=True)
    reg = json.load(open(REG, encoding="utf-8")) if os.path.exists(REG) else []
    reg.append({"id": vid, "origem": d.get("origem", ""), "titulo": d["titulo"], "publicar": quando.isoformat(),
                "enviado": dt.datetime.now(dt.timezone.utc).isoformat()})
    json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"OK https://youtu.be/{vid} agendado {quando:%d/%m %H:%M}")


if __name__ == "__main__":
    main()
