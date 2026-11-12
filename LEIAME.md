# @LevelzIT — cards automáticos do GTA 6

Todo dia, sozinho:
1. **08:30 (Roma)** — a rotina do Claude na nuvem pesquisa as notícias de GTA 6 e escreve `roteiros/dia-NN.json` (6 cards em italiano), seguindo `ROTINA.md`.
2. O push dispara o GitHub Actions (`.github/workflows/cards.yml`): gera os cards (`gerar.py`) e agenda no YouTube (`subir.py`) às 10, 12, 14, 16, 18 e 21h.

Arquivos:
- `config.json` — quantos cards e em que horários.
- `temas-usados.md` — tudo que já saiu (pra não repetir).
- `fotos-oficiais/` — screenshots e artes oficiais da Rockstar; `uso-fotos.json` lembra qual foi usada por último.
- `modelo/card.html`, `assets/fundo-gta-tramonto.mp4`, `musica/` — o visual do card.
- `credenciais/` — só no PC, nunca vai pro GitHub.

No PC: `python gerar.py dia-NN` gera um dia; `python subir.py login` faz o login do canal uma vez; `python subir.py segredos` grava os valores pros Secrets do GitHub.

Depois do lançamento (19/11): entra a fase 2 (gameplay do pendrive → 5 shorts + 1 longo + 3 cards).
