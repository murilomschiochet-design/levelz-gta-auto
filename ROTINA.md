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
- Ordem do dia: o card mais forte no primeiro horário; rumores nunca no primeiro horário.


## Passo 3b — vídeo longo do dia (campo `"longo"` no mesmo `roteiros/dia-NN.json`)
Além dos 5 cards, escreva um vídeo longo de **5 a 6 minutos**, narrado por voz de IA em **italiano**: as notícias do dia explicadas com contexto (pode aprofundar os fatos dos cards e de dias anteriores, sempre com fonte). Mesmas regras: nunca inventar, rumor sempre dito como rumor, nada de leak.
```json
"longo": {
  "hora": "18:00",
  "titulo_yt": "Título forte, até 90 caracteres, SEM #Shorts",
  "descricao": "2–3 frases sobre o vídeo.

Fontes: veículo 1, veículo 2.
Imagens e vídeos: material oficial da Rockstar Games. Canal não afiliado à Rockstar Games ou à Take-Two. (na língua do canal)",
  "tags": ["8 a 10 tags, sem #"],
  "tags_desc": ["4 hashtags, como nos cards"],
  "thumb": {"foto": "Artwork/Jason and Lucia 01", "l1": "GTA 6", "l2": "TRA 5 GIORNI", "caixa": "TUTTO QUELLO CHE SAPPIAMO", "estilo": "vice", "lado": "esq"},
  "blocos": [{"titulo": "Título curto do capítulo", "texto": "45 a 75 palavras, frases curtas, como se falasse.", "fotos": ["Places/Vice City", "People/Lucia Caminos"]}]
}
```
- **11 ou 12 blocos**, total de **650 a 800 palavras**. O primeiro bloco é o gancho (o fato mais forte do dia); o último pergunta algo nos comentários e termina com "Iscriviti a Levelz IT…".
- `titulo` do bloco: até 22 caracteres (vira o capítulo da descrição e o selo na tela).
- `fotos`: 1 a 3 **pastas** de `fotos-oficiais/` que combinem com o bloco (mesma lista dos cards). Nunca invente pasta.
- `thumb`: `l2` até ~14 caracteres em maiúsculas (é o texto grande), `caixa` até ~26; `estilo` = `vice`, `metal` ou `pincel` (varie de um dia para o outro); `lado` = `esq` ou `dir`; `foto` = uma pasta de `Artwork/` ou `People/`.
- Escreva para ouvir: números por extenso quando a voz puder ler errado, sem siglas difíceis, sem emojis no `texto`.

## Passo 4 — validar
```bash
python -c "import json,sys;d=json.load(open('roteiros/dia-NN.json',encoding='utf-8'));import os;assert len(d['shorts'])==json.load(open('config.json'))['cards_por_dia'];[os.path.isdir('fotos-oficiais/'+s['foto']) or sys.exit('pasta inexistente: '+s['foto']) for s in d['shorts']];print('ok')"
```

## Passo 5 — registrar e publicar
- Acrescente uma linha por card em `temas-usados.md`: `AAAA-MM-DD | dia-NN | tag | assunto curto | fonte`.
- `git add roteiros/dia-NN.json temas-usados.md && git commit -m "roteiro dia-NN" && git push origin main` (se o push falhar por causa de mudanças remotas: `git pull --rebase` e push de novo).

## Passo 6 — relatório (em português, curto)
Dia, data, os 5 títulos com tag e fonte, e qualquer assunto que você pulou por falta de fonte.

Validação do longo (rode também):
```bash
python -c "import json,os,sys;d=json.load(open('roteiros/dia-NN.json',encoding='utf-8'))['longo'];w=sum(len(b['texto'].split()) for b in d['blocos']);print(w,'palavras');assert 600<=w<=850 and 10<=len(d['blocos'])<=13;[os.path.isdir('fotos-oficiais/'+f) or sys.exit('pasta inexistente: '+f) for b in d['blocos'] for f in b['fotos']];print('ok')"
```

No relatório, inclua também o título do vídeo longo e quantas palavras ele tem.
