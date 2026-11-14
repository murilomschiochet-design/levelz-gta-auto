"""Thumbnail 1280x720 do vídeo longo (estilos: pincel, metal, vice). Uso: python thumb_longo.py dados.json destino.jpg"""
import json, os, sys, urllib.parse
import navegador
BASE = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(BASE, "modelo", "thumb-longo.html")
LOGO = os.path.join(BASE, "modelo", "logo-gta6.png")

def gerar(dados, destino):
    d = dict(dados)
    d["foto"] = navegador.url_arquivo(d["foto"])
    if d.get("logo", True) is not False and os.path.exists(LOGO):
        d["logo"] = navegador.url_arquivo(LOGO)
    png = os.path.splitext(destino)[0] + ".png"
    navegador.print_pagina(navegador.url_arquivo(MODELO, urllib.parse.quote(json.dumps(d, ensure_ascii=False))), png, 1280, 720)
    from PIL import Image
    Image.open(png).convert("RGB").save(destino, "JPEG", quality=92)
    os.remove(png)

if __name__ == "__main__":
    gerar(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
