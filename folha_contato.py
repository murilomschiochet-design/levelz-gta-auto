"""Monta uma imagem com um quadro de cada short do dia (pra conferir fotos de olho).
Uso: python folha_contato.py dia-XX [--longo]   -> saida/dia-XX/_contato.jpg (ou _contato_longo.jpg)"""
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
dia = sys.argv[1]
pasta = os.path.join(BASE, "saida", dia)
if "--longo" in sys.argv:
    mp4 = os.path.join(pasta, "longo.mp4")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                               capture_output=True, text=True).stdout)
    ent, n = [], 6
    for k in range(n):
        ent += ["-ss", f"{dur * (k + 0.5) / n:.1f}", "-i", mp4]
    lay = "|".join(f"{(k % 3) * 640}_{(k // 3) * 360}" for k in range(n))
    fil = "".join(f"[{k}:v]trim=end_frame=1,scale=640:360[v{k}];" for k in range(n))
    fil += "".join(f"[v{k}]" for k in range(n)) + f"xstack=inputs={n}:layout={lay}"
    destino = os.path.join(pasta, "_contato_longo.jpg")
else:
    vids = sorted(f for f in os.listdir(pasta) if f[:2].isdigit() and f.endswith(".mp4"))
    ent = []
    for v in vids:
        ent += ["-ss", "2", "-i", os.path.join(pasta, v)]
    n = len(vids)
    lay = "|".join(f"{(k % 3) * 360}_{(k // 3) * 640}" for k in range(n))
    fil = "".join(f"[{k}:v]trim=end_frame=1,scale=360:640[v{k}];" for k in range(n))
    fil = (fil + "".join(f"[v{k}]" for k in range(n)) + f"xstack=inputs={n}:layout={lay}:fill=black") if n > 1 else fil.rstrip(";").replace("[v0]", "")
    destino = os.path.join(pasta, "_contato.jpg")
subprocess.run(["ffmpeg", "-v", "error", "-y", *ent, "-filter_complex", fil, "-frames:v", "1", destino], check=True)
print(destino)
