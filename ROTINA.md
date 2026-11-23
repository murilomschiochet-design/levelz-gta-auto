# Rotina diária do Claude — @LevelzIT (GTA 6, em italiano) — 08:30, horário de Roma

**DESDE 24/11/2026 o canal é SÓ SHORTS DE CURIOSIDADE** (YouTube, Instagram e TikTok iguais; sem vídeo longo, sem cards, sem cortes de gameplay da fila).
Cada short: cenas da NOSSA gameplay trocando a cada 2–3 s + narração em italiano (voz de IA, rápida) contando **uma curiosidade, segredo, truque, "come fare" ou descoberta do GTA 6 que está rodando nas últimas 24–48 h** + legenda grande no meio da tela. 15–22 s.
Você escreve os textos e escolhe as cenas; depois do push, o GitHub Actions (`curiosita.py`) gera os vídeos e agenda tudo.

## Regras de conteúdo (as mais importantes)
- **Nunca invente nada.** Cada short precisa de uma fonte real que você abriu hoje (veículo grande: IGN, GameSpot, Eurogamer, Kotaku, VGC, PC Gamer, GamesRadar, Insider Gaming, Multiplayer.it, Everyeye.it, Spaziogames, IGN Italia, Fanpage, Tom's Hardware Italia, ou Rockstar/Take-Two).
- Coisa do Reddit/redes só entra se um veículo grande também noticiou ("secondo i giocatori…"). Rumor: no máximo 1 por dia, nunca no primeiro horário, sempre "si dice che…".
- **Proibido:** leaks de material roubado (2022, builds), **spoilers da história** (final, mortes, reviravoltas, missões avançadas — começo do jogo e mundo aberto pode), datas/preços não oficiais como certos.
- **Não repita** assunto/ângulo de `temas-usados.md`.
- **Mix do dia** (6 shorts): pelo menos 2 `Segreto` (easter egg, lugar escondido, referência), 2 `Trucco` (dica prática, como fazer, dinheiro, onde achar), 1 `Scoperta` (o que viralizou nas últimas 24–48 h); o resto `Curiosità` (realismo, mapa, números). O primeiro horário = o assunto mais forte/viral do dia.
- **Onde pesquisar:** WebSearch "GTA 6 secret", "GTA 6 easter egg", "GTA 6 players discovered", "GTA 6 tips", "GTA 6 trick", "GTA 6 segreti", "GTA 6 trucchi", "GTA 6 come fare", notícias das últimas 48 h. Abra as páginas e confirme.

## Passo 1 — já tem roteiro pra hoje?
Rode e obedeça (o número do `dia-NN` NÃO é a data):
`python -c "import json,glob,os,re,datetime,zoneinfo;h=str(datetime.datetime.now(zoneinfo.ZoneInfo('Europe/Rome')).date());fs=glob.glob('roteiros/dia-*.json')+glob.glob('roteiros/_antigos/dia-*.json');ja=[f for f in fs if json.load(open(f,encoding='utf-8')).get('data')==h];n=max([int(re.search(r'dia-(\d+)',f).group(1)) for f in fs] or [0])+1;print('HOJE',h,'JA_EXISTE',bool(ja),ja,'PROXIMO','dia-%02d'%n)"`
- `JA_EXISTE True` → **pare** e escreva no relatório "já existe roteiro para hoje".
- `JA_EXISTE False` → siga; o arquivo de hoje é o `PROXIMO`.

## Passo 2 — pesquisar (regras acima) e ler `temas-usados.md`

## Passo 3 — escrever os textos (em italiano)
Quantidade e horários: `config.json` → `curiosita_por_dia` e `horas_curiosita`.
- `texto`: **50 a 70 palavras** (a voz é rápida: dá 16–22 s). Começa com gancho forte na 1ª frase ("Lo sapevi che…", "In GTA 6 puoi…", "Nessuno ti dice che…", "Fermati: …"), frases curtas, linguagem falada, termina com pergunta curta pro comentário ("Tu lo sapevi?", "Lo proverai?"). Sem emojis, sem siglas difíceis, números que a voz lê bem.
- `gancho`: título que aparece em cima nos primeiros 3 s, MAIÚSCULAS, até ~28 caracteres (ex.: "TRUCCO SEGRETO: PRIMA PERSONA", "SOLDI FACILI SUBITO").
- `titulo_yt`: até 90 caracteres, termina com `#Shorts`. `descricao`: 1–2 frases + "Fonte: <veículo>." `hashtags`: 5–6, sempre `#gta6` e `#gta6italia`.
- `legenda` (TikTok/Instagram): 1 frase curta com pergunta + 5–6 hashtags (ex.: "Lo sapevi? 😱 #gta6 #gta6italia #gaming #videogiochi #gtavi").
- `tag`: `Segreto`, `Trucco`, `Scoperta`, `Curiosità`, `Record` ou `Rumor`. `fonte`: url.

## Passo 4 — escolher as cenas (o mais importante pro vídeo ficar bom)
As cenas são trechos de 3,5 s da NOSSA gameplay, já verticais. Lista: `gameplay/cenas.json` (id = `<sessao>-<NNN>`); folhas de contato em `gameplay/cenas/folhas/<sessao>-K.jpg` (miniaturas com o número NNN em amarelo).
1. Veja quantas vezes cada cena já foi usada: `python -c "import json,collections;b=json.load(open('gameplay/cenas.json',encoding='utf-8'))['itens'];c=collections.Counter((x['sessao'],len(x.get('usos',[]))) for x in b);print(len(b),'cenas');[print(k,v) for k,v in sorted(c.items())]"`
2. **Abra as folhas com a ferramenta Read** (são imagens; você enxerga) — comece pelas sessões mais novas e menos usadas.
3. Para cada short, divida o `texto` em pedaços de **5 a 9 palavras** (7 a 10 cenas por short) e escolha pra cada pedaço a cena que **mais combina com o que está sendo falado** (carro → cena de carro; dinheiro/loja → loja; segredo/lugar → paisagem/lugar; perigo/attenzione → tiroteio/fuga; menu/mapa/telefono → tela de mapa/menu; prima persona/telecamera → close). Se nada combinar, use AÇÃO (tiroteio, perseguição, explosão, helicóptero, barco). **A 1ª cena tem que ser a mais impactante.**
4. Não repita cena no mesmo dia; prefira cenas com 0 usos; evite cena escura/tela preta/loading.
5. `cenas`: lista em ordem, `{"de": "<as 2 a 4 PRIMEIRAS palavras exatas do pedaço, como estão no texto>", "cena": "<id>"}`. A 1ª entra no começo (`de` = início do texto).

## Passo 5 — `roteiros/dia-NN.json`
```json
{
 "dia": 14,
 "data": "AAAA-MM-DD",
 "formato": "curiosita",
 "shorts": [
  {
   "id": "c1",
   "hora": "10:00",
   "curiosita": true,
   "tag": "Trucco",
   "titulo": "Prima persona segreta",
   "gancho": "TRUCCO SEGRETO: PRIMA PERSONA",
   "texto": "Lo sapevi? In GTA 6 puoi giocare in prima persona, anche se il menu non te lo dice. I giocatori hanno scoperto un trucco: apri il telefono e chiudilo subito, e la telecamera resta bloccata in prima persona. Funziona su PS5 e su Xbox. Ma attenzione: fai prima un salvataggio manuale, perché per tornare in terza persona potresti dover ricaricare. Tu lo proverai?",
   "cenas": [
    {"de": "Lo sapevi", "cena": "20261123-000618-091"},
    {"de": "anche se il menu", "cena": "20261123-000618-152"},
    {"de": "I giocatori hanno scoperto", "cena": "20261123-000618-045"}
   ],
   "titulo_yt": "GTA 6: il trucco segreto per la PRIMA PERSONA 😱 #Shorts",
   "descricao": "Come attivare la prima persona in GTA 6 con il telefono. Fonte: Yahoo Tech.",
   "hashtags": ["#gta6", "#gta6italia", "#gtavi", "#gaming", "#videogiochi"],
   "legenda": "Lo sapevi? 😱 Tu lo proverai? #gta6 #gta6italia #gaming #videogiochi #gtavi",
   "fonte": "https://..."
  }
 ]
}
```
(ids `c1`…`c6`, horários de `horas_curiosita` em ordem.)

## Passo 6 — validar (tem que dar "ok")
```bash
python -c "import json,sys,re;d=json.load(open('roteiros/dia-NN.json',encoding='utf-8'));b={x['id'] for x in json.load(open('gameplay/cenas.json',encoding='utf-8'))['itens']};vistas=set()
for s in d['shorts']:
  w=len(s['texto'].split());cs=[c['cena'] for c in s['cenas']];tx=re.sub(r'[^\w ]','',s['texto'].lower())
  assert s.get('curiosita') and 45<=w<=75,(s['id'],w,'palavras')
  assert 6<=len(cs)<=12,(s['id'],len(cs),'cenas');assert all(c in b for c in cs),(s['id'],'cena inexistente')
  assert not (set(cs)&vistas),(s['id'],'cena repetida no dia');vistas|=set(cs)
  assert all(re.sub(r'[^\w ]','',c['de'].lower()) in tx for c in s['cenas']),(s['id'],'\"de\" que nao esta no texto')
  print(s['id'],s['hora'],w,'palavras',len(cs),'cenas')
print('ok')"
```

## Passo 7 — registrar e publicar
- Uma linha por short em `temas-usados.md`: `AAAA-MM-DD | dia-NN | tag | assunto curto | fonte`.
- `git add roteiros/dia-NN.json temas-usados.md && git commit -m "roteiro dia-NN (curiosita)" && git push origin main` (se falhar: `git pull --rebase` e push de novo).

## Passo 8 — relatório (português, curto)
Dia, data, os 6 ganchos com tag e fonte, e o que você pulou por falta de fonte. Se `gameplay/cenas.json` tiver poucas cenas com 0 usos (menos de 60), primeira linha: "⚠️ cenas acabando: mande gameplay nova pro painel".
