# Rotina diária do Claude — @LevelzIT (GTA 6, em italiano) — 08:30, horário de Roma

Você escreve os **cards do dia** do canal de YouTube @LevelzIT: curiosidades, novidades, rumores e fatos já conhecidos do **GTA 6**.
Os textos são em **italiano**. Depois do push, o GitHub Actions gera os vídeos e agenda tudo no YouTube sozinho.

## Regras de conteúdo (as mais importantes)
- **Nunca invente nada.** Cada card precisa de uma fonte real que você abriu hoje ou que já está no repositório (roteiros antigos).
- **Ufficiale** = confirmado pela Rockstar (rockstargames.com, Newswire, trailers, contas oficiais). Pode ser dito como fato.
- **Novità** = notícia dos últimos dias publicada por um veículo grande (IGN, GameSpot, Eurogamer, Kotaku, VGC, Insider Gaming, Bloomberg, Multiplayer.it, Everyeye.it, Spaziogames). Diga quem publicou se não for oficial.
- **Rumor** = boato de insider ou veículo conhecido. **Máximo 2 por dia.** Sempre com tag `Rumor` e com "secondo …" / "si dice che …" no texto. Nunca apresente boato como fato.
- **Proibido:** vazamentos de material roubado (ex.: o leak de 2022, builds vazadas, código), boatos de contas anônimas sem veículo, datas ou preços não oficiais apresentados como certos, spoilers da história depois do lançamento sem avisar ("SPOILER" no título).
- Se duas fontes discordarem, use a oficial; se não houver oficial, não use o assunto.
- **Não repita** um assunto/ângulo que já está em `temas-usados.md`. Mesmo personagem pode voltar com um fato **diferente**.
- Hoje e nos próximos dias o assunto é forte: lançamento em **19/11/2026**. Depois do lançamento, priorize descobertas e curiosidades do jogo que os grandes veículos estão publicando (easter eggs, segredos, recordes, detalhes do mapa).

## Passo 1 — já tem roteiro pra hoje?
- Data de hoje no fuso Europe/Rome: `TZ=Europe/Rome date +%F`.
- Se algum arquivo em `roteiros/` ou `roteiros/_antigos/` tiver `"data": "<hoje>"`, **pare** e só escreva no relatório "já existe roteiro para hoje".
- O próximo número é o maior `dia-NN` entre `roteiros/` e `roteiros/_antigos/` mais 1 (dois dígitos: dia-03, dia-04…).

## Passo 2 — pesquisar
- Use WebSearch/WebFetch: "GTA 6 news", "GTA 6 Rockstar Newswire", "GTA 6 novità", notícias das últimas 48 h, e abra as páginas para confirmar os fatos.
- Leia `temas-usados.md` para não repetir.
- Se faltar novidade, use fatos oficiais ainda não usados (site rockstargames.com/VI: personagens, lugares, trailers, data, plataformas) e curiosidades bem documentadas.

## Passo 3 — escrever `roteiros/dia-NN.json`
Quantidade e horários: `config.json` (`cards_por_dia`, `horas_cards`). Estrutura exata (veja `roteiros/_antigos/dia-02.json`):

```json
{
 "dia": 3,
 "data": "AAAA-MM-DD",
 "shorts": [
  {
   "id": "01",
   "hora": "10:00",
   "tag": "Novità",
   "titulo": "Texto curto com *destaque*",
   "texto": "2 ou 3 frases com **nomes** em destaque.",
   "foto": "People/Lucia Caminos",
   "titulo_yt": "Título chamativo em italiano 😱 #Shorts",
   "descricao": "1–2 frases em italiano. Fonte: <veículo>.",
   "hashtags": ["#gta6", "#gta6italia", "#gtavi", "#rockstar", "#gaming"],
   "fonte": "url ou nome da fonte"
  }
 ]
}
```
- `tag`: uma de `Ufficiale`, `Novità`, `Rumor`, `Curiosità`, `Personaggi`, `Mappa`, `Trailer`, `Uscita`.
- `titulo`: até ~40 caracteres, uma palavra-chave entre `*asteriscos*` (fica laranja).
- `texto`: até ~280 caracteres, 2–3 nomes/números entre `**`. Frases curtas, linguagem de YouTube Shorts, sem exagero falso.
- `titulo_yt`: até 90 caracteres, termina com `#Shorts`. `hashtags`: 5 ou 6, sempre `#gta6` e `#gta6italia`.
- `foto`: **pasta** dentro de `fotos-oficiais/` (o robô escolhe a imagem usada há mais tempo). Liste com `ls fotos-oficiais/*/ fotos-oficiais/Artwork/`. Escolha a que combina com o assunto (personagem → People/… ou Artwork/…; lugar → Places/…; geral → `Artwork/Official Cover Art`, `Places/Vice City`). Nunca invente pasta.
- Ordem do dia: o card mais forte às 10:00; rumores nunca no primeiro horário.

## Passo 4 — validar
```bash
python -c "import json,sys;d=json.load(open('roteiros/dia-NN.json',encoding='utf-8'));import os;assert len(d['shorts'])==json.load(open('config.json'))['cards_por_dia'];[os.path.isdir('fotos-oficiais/'+s['foto']) or sys.exit('pasta inexistente: '+s['foto']) for s in d['shorts']];print('ok')"
```

## Passo 5 — registrar e publicar
- Acrescente uma linha por card em `temas-usados.md`: `AAAA-MM-DD | dia-NN | tag | assunto curto | fonte`.
- `git add roteiros/dia-NN.json temas-usados.md && git commit -m "roteiro dia-NN" && git push origin main` (se o push falhar por causa de mudanças remotas: `git pull --rebase` e push de novo).

## Passo 6 — relatório (em português, curto)
Dia, data, os 6 títulos com tag e fonte, e qualquer assunto que você pulou por falta de fonte.
