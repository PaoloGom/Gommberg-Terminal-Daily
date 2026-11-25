#!/usr/bin/env bash
# Il rilascio. Due rami di lavoro: "rilascio" porta solo ciò che può andare in linea la sera stessa; "con-prova" tiene
# ciò che cambia le regole di scrittura o un'edizione campione, finché l'edizione di prova del venerdì non è andata bene.
# Il ramo principale (quello che i lettori vedono: ogni push su main ripubblica gommberg.com) riceve UN solo merge, dal
# ramo rilascio, e solo a collaudo verde. Vale ogni sera per un rilascio e per un guasto: stessa strada, in piccolo.
# Mappa del sistema e regole: redazione/ARCHITETTURA.md §5.
#
#   bash redazione/rilascia.sh avvia [con-prova]   mette la sessione sul ramo rilascio (o con-prova), allineato al ramo
#                                         principale (lo crea se manca)
#   bash redazione/rilascia.sh collauda   sul ramo dove sei: porta dentro le novità del ramo principale, lancia il
#                                         collaudo, stampa il resoconto
#   bash redazione/rilascia.sh unisci <commit>   dopo la prova andata bene: porta nel ramo rilascio il lavoro di con-prova
#                                         fino al commit su cui è stata fatta la prova (dopo.prova.commit), non oltre
#   bash redazione/rilascia.sh pubblica [--ok-di-paolo] [--dopo-la-prova] [--senza-github] [--guasto]
#                                         collauda; se è verde qui e su GitHub, un solo merge sul ramo principale
#   bash redazione/rilascia.sh annulla    toglie dal ramo principale l'ultimo rilascio (revert del suo merge)
#
# I cancelli di "pubblica", nell'ordine: 1) niente modifiche non salvate; 2) il ramo contiene l'ultimo ramo principale;
# 3) redazione/collaudo.py esce con 0 (rete di non regressione compresa); 4) se il rilascio cambia ciò che il lettore
# vede (file pubblici del sito, testo del PDF o email dei campioni della rete, modello della newsletter) serve
# --ok-di-paolo, che chi guida il rilascio aggiunge solo dopo il sì di Paolo al resoconto; 5) il collaudo di GitHub
# (.github/workflows/collaudo.yml: stesso collaudo su un'altra macchina, più il sito aperto in un browser vero) è verde
# sullo stesso commit. --senza-github salta solo il 5, quando GitHub non si può leggere da questa sessione.
# Tra il 3 e il 4, la prova: se il rilascio cambia le regole di scrittura o un'edizione campione serve --dopo-la-prova,
# che chi guida il rilascio aggiunge solo quando l'edizione di prova del ramo con-prova è andata bene (dopo.prova ok).
# Prima dei cancelli, l'orario: dal lunedì al venerdì tra le 8:30 e le 10:30 di Roma l'edizione sta uscendo e il ramo
# principale non si tocca; --guasto lo permette solo per un guasto che blocca l'uscita dell'edizione.
# Il resoconto dice anche la FINESTRA del rilascio (ARCHITETTURA.md §5): ogni giorno, con prova, con Paolo.
# Il merge ha come contenuto esatto quello collaudato (stesso albero di file). Si può sempre tornare indietro: annulla.
# GTD_PROVA=1: pubblica e annulla fanno tutto tranne i push sul ramo principale, che stampano.
set -u
{   # tra graffe: bash legge tutto lo script prima di eseguirlo ("annulla" cambia i file del repository mentre gira)
REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "RILASCIO: FERMO - non sono dentro il repository"; exit 1; }
cd "$REPO" || exit 1
RAMO="rilascio"; ATTESA="con-prova"; PRINC="main"; PROVA="${GTD_PROVA:-0}"; FONDO=300
AZIONE="${1:-}"; shift 2>/dev/null || true
OK_PAOLO=0; SENZA_GITHUB=0; GUASTO=0; DOPO_PROVA=0; SU="$RAMO"; PROVATO=""
for a in "$@"; do
  # le opzioni valgono solo per l'azione che le usa: un'opzione fuori posto ferma, non passa in silenzio
  if [ "$AZIONE" = "avvia" ] && [ "$a" = "$ATTESA" ]; then SU="$ATTESA"; continue; fi
  if [ "$AZIONE" = "unisci" ] && echo "$a" | grep -qiE '^[0-9a-f]{7,40}$'; then
    [ -z "$PROVATO" ] || { echo "RILASCIO: FERMO - unisci vuole un solo commit, quello della prova"; exit 1; }
    PROVATO="$a"; continue
  fi
  [ "$AZIONE" = "pubblica" ] || { echo "RILASCIO: FERMO - opzione sconosciuta per '$AZIONE': $a"; exit 1; }
  case "$a" in --ok-di-paolo) OK_PAOLO=1;; --dopo-la-prova) DOPO_PROVA=1;; --senza-github) SENZA_GITHUB=1;; --guasto) GUASTO=1;; *) echo "RILASCIO: FERMO - opzione sconosciuta: $a"; exit 1;; esac
done

fermo() { echo "RILASCIO: FERMO - $1"; exit 1; }
pulito() { [ -z "$(git status --porcelain)" ] || fermo "ci sono modifiche non salvate (git status): prima commit, o scartale"; }
sul_ramo() {  # il ramo dove sono deve essere uno dei due di lavoro; QUI lo ricorda
  QUI="$(git rev-parse --abbrev-ref HEAD)"
  [ "$QUI" = "$RAMO" ] || [ "$QUI" = "$ATTESA" ] || fermo "non sono sul ramo $RAMO né su $ATTESA: lancia prima 'rilascia.sh avvia'"
}
solo_rilascio() { [ "$(git rev-parse --abbrev-ref HEAD)" = "$RAMO" ] || fermo "si fa solo dal ramo $RAMO: lancia prima 'rilascia.sh avvia' (il lavoro di $ATTESA ci arriva con 'unisci', dopo la prova)"; }
prendi() { git fetch -q --depth="$FONDO" origin "$@" 2>/dev/null || fermo "git fetch di $* non riuscito"; }
firma() { git config user.name >/dev/null || git config user.name "PaoloGom"; git config user.email >/dev/null || git config user.email "PaoloGom@users.noreply.github.com"; }
spingi() {  # spingi <cosa> <ramo>: push senza forzare, verificato con ls-remote (come pubblica.sh)
  local cosa="$1" ramo="$2" out
  out=$(git -c push.negotiate=true push origin "$cosa:refs/heads/$ramo" 2>&1)
  [ "$(git ls-remote origin "refs/heads/$ramo" 2>/dev/null | cut -f1)" = "$(git rev-parse "$cosa")" ] && return 0
  echo "$out" | grep -iE "error|rejected|denied|fatal" | head -2; return 1
}
dentro() {  # porta nel ramo dove sono le novità del ramo principale (edizioni uscite, file di stato, rilasci)
  prendi "$PRINC"
  git merge-base --is-ancestor "origin/$PRINC" HEAD 2>/dev/null && return 0
  firma
  if ! git merge -q --no-edit "origin/$PRINC" >/dev/null 2>&1; then
    local f; f=$(git diff --name-only --diff-filter=U | head -5 | tr '\n' ' ')
    git merge --abort >/dev/null 2>&1
    fermo "il ramo $(git rev-parse --abbrev-ref HEAD) non si unisce al ramo principale: conflitto in $f"
  fi
}

# Che cosa cambia rispetto al ramo principale, e per chi. Riempie PUBBLICI, CAMPIONI, MODELLO, SCRITTURA, SERVE_OK.
cambia() {
  local tutti; tutti=$(git diff --name-only "origin/$PRINC" HEAD)
  # pubblico = ciò che costruisci.py copia sul sito: tutto tranne redazione (salvo i quattro file letti dal sito),
  # file e cartelle nascosti, cartelle di lavoro con _ e README
  PUBBLICI=$(echo "$tutti" | grep -vE '^(redazione/|README)|(^|/)[._]' ; echo "$tutti" | grep -E '^redazione/(glossario|glossario_sito|meccanismi)\.json$|^redazione/scommessa/pagella\.json$')
  PUBBLICI=$(echo "$PUBBLICI" | sed '/^$/d')
  # solo l'atteso MODIFICATO: un campione nuovo non cambia nulla per il lettore, un campione che esce diverso sì
  CAMPIONI=$(git diff --no-renames --name-only --diff-filter=MD "origin/$PRINC" HEAD | grep -E '^redazione/rete/[^/]+/atteso/(pdf\.txt|email\.html)$')
  MODELLO=$(echo "$tutti" | grep -E '^redazione/newsletter_(modello|cornice)\.html$')
  # ciò che la redazione del mattino legge o che decide che cosa resta in pagina: regole, modello, lessico, l'avvio,
  # i controlli, il desk, il metodo della scommessa, il gancio della sessione
  SCRITTURA=$(echo "$tutti" | grep -E '^redazione/(ISTRUZIONI|APP_[A-Z]+|NOTA_DEL_GIORNO)\.md$|^redazione/edizione_modello_v[0-9]+\.py$|^redazione/(glossario|meccanismi|fonti)\.json$|^redazione/(prepara\.sh|controlli_tutti\.sh|scommessa_giorno\.sh|desk\.py|contesto\.py|gancio_token\.py|controlli[a-z_]*\.py)$|^redazione/scommessa/(metodo\.json|[a-z0-9_]+\.py)$|^\.claude/settings\.json$')
  SERVE_OK=0; [ -n "$PUBBLICI$CAMPIONI$MODELLO" ] && SERVE_OK=1
  TUTTI="$tutti"
}
# La finestra del rilascio (G-57): la decide questo resoconto, non la chat. Soldi, terzi e irreversibile lo script non li
# vede: li dichiara chi guida il rilascio, e anche quelli vogliono Paolo.
finestra() {
  local f=""
  [ -n "$SCRITTURA$CAMPIONI" ] && f="CON PROVA (prima un'edizione di prova dal ramo con-prova, PROVA.md)"
  [ "$SERVE_OK" = 1 ] && f="${f:+$f + }CON PAOLO (il suo ok, nel riassunto DOPO)"
  local d="OGNI GIORNO (in linea la sera stessa, dopo l'edizione e il controllo del mattino)"
  echo "${f:-$d}"
}
fuori_orario() {  # vero tra le 8:30 e le 10:30 di Roma dal lunedì al venerdì (GTD_ORA="u HHMM" solo per le prove)
  local o g h; o="${GTD_ORA:-$(TZ=Europe/Rome date '+%u %H%M')}"; g="${o%% *}"; h="${o##* }"; h=$((10#$h))
  [ "$g" -le 5 ] && [ "$h" -ge 830 ] && [ "$h" -lt 1030 ]
}
elenco() { echo "$1" | sed '/^$/d' | head -"${2:-12}" | sed 's/^/    /'; local n; n=$(echo "$1" | sed '/^$/d' | wc -l); [ "$n" -gt "${2:-12}" ] && echo "    ... e altri $((n - ${2:-12}))"; return 0; }

resoconto() {
  cambia
  local n; n=$(git rev-list --no-merges --count "origin/$PRINC..HEAD")
  echo "== RESOCONTO DEL RILASCIO - $(TZ=Europe/Rome date '+%d/%m/%Y %H:%M') =="
  echo "Commit: $n (commit $(git rev-parse --short HEAD) su $(git rev-parse --short "origin/$PRINC")); voci: $(git log --no-merges --format=%s "origin/$PRINC..HEAD" | grep -oE 'G-[0-9]+' | sort -u | tr '\n' ' ')"
  git log --no-merges --reverse --format='  - %h %s' "origin/$PRINC..HEAD" | cut -c1-150 | head -40
  echo "File cambiati: $(echo "$TUTTI" | sed '/^$/d' | wc -l)"
  echo "Per i lettori:"
  if [ -n "$PUBBLICI" ]; then echo "  Sito, $(echo "$PUBBLICI" | wc -l) file pubblici:"; elenco "$PUBBLICI"; else echo "  Sito: nessun file pubblico cambia"; fi
  if [ -n "$CAMPIONI" ]; then echo "  PDF o email: le stesse edizioni campione ora escono diverse (git diff origin/$PRINC HEAD -- redazione/rete):"; elenco "$CAMPIONI"
  else echo "  PDF ed email: le edizioni campione escono identiche a prima"; fi
  [ -n "$MODELLO" ] && echo "  Newsletter: cambia il modello (va ricaricato in Kit)"
  if [ -n "$SCRITTURA" ]; then echo "  Scrittura: cambiano regole o lessico della redazione, si vede solo su un'edizione di prova (PROVA.md):"; elenco "$SCRITTURA"; fi
  echo "Ok di Paolo: $([ "$SERVE_OK" = 1 ] && echo "SERVE (cambia ciò che il lettore vede)" || echo "non serve (niente di visibile ai lettori)")"
  echo "Finestra: $(finestra)"
  echo "Collaudo: $ESITO_COLLAUDO"
}

collauda() {
  sul_ramo; pulito; dentro
  [ -n "$(git diff --name-only "origin/$PRINC" HEAD)" ] || fermo "il ramo $QUI è uguale al ramo principale: niente da rilasciare"
  local out rc
  out=$(python3 redazione/collaudo.py 2>&1); rc=$?
  echo "$out"
  ESITO_COLLAUDO=$(echo "$out" | grep '^COLLAUDO:' | tail -1); ESITO_COLLAUDO="${ESITO_COLLAUDO:-COLLAUDO: nessun esito (rc $rc)}"
  [ -z "$(git status --porcelain)" ] || fermo "il collaudo ha lasciato file cambiati (git status): non doveva"
  echo; resoconto
  return $rc
}

github_verde() {  # il collaudo di GitHub sullo stesso commit: aspetta fino a 20 minuti
  local sha="$1" i riga stato esito
  command -v gh >/dev/null || fermo "non posso leggere GitHub da qui (manca gh): guarda tu la pagina Actions e rilancia con --senza-github"
  for i in $(seq 1 60); do
    riga=$(gh run list --workflow collaudo.yml --commit "$sha" -L 1 --json status,conclusion -q '.[0] | "\(.status) \(.conclusion)"' 2>/dev/null)
    stato="${riga%% *}"; esito="${riga##* }"
    if [ "$stato" = "completed" ]; then
      [ "$esito" = "success" ] && { echo "Collaudo di GitHub: verde su $(git rev-parse --short "$sha")"; return 0; }
      fermo "il collaudo di GitHub è $esito su $(git rev-parse --short "$sha"): gh run list --workflow collaudo.yml -L 1, poi gh run view <id> --log-failed"
    fi
    [ "$i" = 1 ] && echo "Aspetto il collaudo di GitHub su $(git rev-parse --short "$sha") (fino a 20 minuti)..."
    sleep 20
  done
  fermo "il collaudo di GitHub non ha finito in 20 minuti: riprova tra poco"
}

case "$AZIONE" in
avvia)
  pulito; prendi "$PRINC"
  # avvia non cancella mai lavoro: se il ramo locale ha commit che origin non ha, si ferma (o, se origin non ha ancora
  # il ramo, parte da quello locale)
  if git ls-remote --exit-code --heads origin "$SU" >/dev/null 2>&1; then
    git fetch -q --depth="$FONDO" origin "+refs/heads/$SU:refs/remotes/origin/$SU" 2>/dev/null || fermo "git fetch di $SU non riuscito"
    if git show-ref --verify --quiet "refs/heads/$SU" && [ "$(git rev-list --count "origin/$SU..$SU")" -gt 0 ]; then
      fermo "il ramo locale $SU ha $(git rev-list --count "origin/$SU..$SU") commit che origin non ha: prima 'git push origin $SU', poi rilancia (avvia non li cancella)"
    fi
    git checkout -q -B "$SU" "origin/$SU" || fermo "checkout del ramo $SU"
  elif git show-ref --verify --quiet "refs/heads/$SU" && [ "$(git rev-list --count "origin/$PRINC..$SU")" -gt 0 ]; then
    git checkout -q "$SU" || fermo "checkout del ramo $SU"
  else
    git checkout -q -B "$SU" "origin/$PRINC" || fermo "creazione del ramo $SU"
  fi
  dentro
  spingi HEAD "$SU" || fermo "push del ramo $SU rifiutato"
  echo "RILASCIO: ramo $SU pronto su $(git rev-parse --short "origin/$PRINC") del ramo principale, $(git rev-list --no-merges --count "origin/$PRINC..HEAD") commit avanti."
  echo "Da qui: lavoro e commit su questo ramo, python3 redazione/collaudo.py dopo ogni modifica, git push origin $SU."
  [ "$SU" = "$ATTESA" ] && echo "Questo ramo aspetta l'edizione di prova del venerdì: in linea ci va con 'avvia', 'unisci' e 'pubblica --dopo-la-prova'."
  ;;
collauda)
  collauda; rc=$?
  [ $rc -eq 0 ] && echo "RILASCIO: collaudo verde sul ramo $QUI, il ramo principale non è stato toccato." || echo "RILASCIO: FERMO - collaudo rosso."
  exit $rc
  ;;
unisci)
  [ -n "$PROVATO" ] || fermo "unisci vuole il commit su cui è stata fatta la prova (dopo.prova.commit nel Registro): rilascia.sh unisci <commit>"
  solo_rilascio; pulito; firma
  git fetch -q --depth="$FONDO" origin "+refs/heads/$ATTESA:refs/remotes/origin/$ATTESA" 2>/dev/null || fermo "git fetch di $ATTESA non riuscito"
  git cat-file -e "$PROVATO^{commit}" 2>/dev/null || fermo "il commit $PROVATO non esiste"
  git merge-base --is-ancestor "$PROVATO" "origin/$ATTESA" 2>/dev/null || fermo "il commit $PROVATO non sta sul ramo $ATTESA"
  if git merge-base --is-ancestor "$PROVATO" HEAD 2>/dev/null; then echo "RILASCIO: il ramo $RAMO contiene già $PROVATO: niente da unire."; exit 0; fi
  if ! git merge -q --no-edit "$PROVATO" >/dev/null 2>&1; then
    f=$(git diff --name-only --diff-filter=U | head -5 | tr '\n' ' ')
    git merge --abort >/dev/null 2>&1
    fermo "il ramo $ATTESA non si unisce al ramo $RAMO: conflitto in $f (prima si pubblica ciò che è su $RAMO; poi 'avvia $ATTESA' porta dentro il ramo principale e il conflitto si risolve lì, con una nuova prova se tocca la scrittura)"
  fi
  spingi HEAD "$RAMO" || fermo "push del ramo $RAMO rifiutato"
  echo "RILASCIO: il lavoro provato di $ATTESA ($(git rev-parse --short "$PROVATO")) è nel ramo $RAMO. Ora, subito: 'pubblica --dopo-la-prova' (si unisce solo al Rilascia di Paolo, mai prima)."
  ;;
pubblica)
  if fuori_orario && [ "$GUASTO" != 1 ]; then
    fermo "tra le 8:30 e le 10:30 dei giorni di edizione il ramo principale non si tocca: riprova dopo le 10:30 (--guasto solo per un guasto che blocca l'uscita)"
  fi
  solo_rilascio
  collauda || fermo "collaudo rosso: il ramo principale non si tocca"
  if [ -n "$SCRITTURA$CAMPIONI" ] && [ "$DOPO_PROVA" != 1 ]; then
    fermo "questo rilascio cambia le regole di scrittura o un'edizione campione: vuole l'edizione di prova. Il lavoro sta sul ramo $ATTESA fino alla prova; dopo la prova andata bene rilancia con --dopo-la-prova"
  fi
  if [ "$SERVE_OK" = 1 ] && [ "$OK_PAOLO" != 1 ]; then
    fermo "questo rilascio cambia ciò che il lettore vede: mostra a Paolo il resoconto qui sopra e, dopo il suo sì, rilancia con --ok-di-paolo"
  fi
  firma
  spingi HEAD "$RAMO" || fermo "push del ramo $RAMO rifiutato"
  [ "$SENZA_GITHUB" = 1 ] && echo "Collaudo di GitHub: saltato (--senza-github)" || github_verde "$(git rev-parse HEAD)"
  # il merge: un commit sul ramo principale con ESATTAMENTE l'albero collaudato (il ramo contiene già il ramo principale)
  VOCI=$(git log --no-merges --format=%s "origin/$PRINC..HEAD" | grep -oE 'G-[0-9]+' | sort -u | tr '\n' ' ' | sed 's/ $//')
  N=$(git rev-list --no-merges --count "origin/$PRINC..HEAD")
  M=$(git commit-tree "HEAD^{tree}" -p "origin/$PRINC" -p HEAD -m "Rilascio $(TZ=Europe/Rome date +%F): $N commit${VOCI:+ ($VOCI)}

$(git log --no-merges --reverse --format='- %s' "origin/$PRINC..HEAD" | cut -c1-140 | head -40)") || fermo "commit del merge"
  if [ "$PROVA" = "1" ]; then
    echo "[prova] git push origin $M:refs/heads/$PRINC   (merge \"$(git log -1 --format=%s "$M")\")"
    echo "RILASCIO: PROVA - tutto verde, nessun push sul ramo principale."; exit 0
  fi
  # l'orario di nuovo, subito prima del merge: collaudo e attesa di GitHub possono averlo portato dentro la fascia
  if fuori_orario && [ "$GUASTO" != 1 ]; then fermo "nel frattempo sono le 8:30 passate: il ramo principale non si tocca fino alle 10:30, rilancia dopo (nulla è stato pubblicato)"; fi
  spingi "$M" "$PRINC" || fermo "push sul ramo principale rifiutato (è cambiato nel frattempo? rilancia: nulla è stato pubblicato)"
  git merge -q --ff-only "$M" && spingi HEAD "$RAMO" || echo "AVVISO: ramo $RAMO non riallineato al ramo principale (lo farà il prossimo 'avvia')"
  echo "RILASCIO: PUBBLICATO - merge $(git rev-parse --short "$M") sul ramo principale ($N commit${VOCI:+, $VOCI})."
  echo "Ora GitHub ripubblica gommberg.com e lo verifica dal vivo: gh run list --workflow sito.yml -L 1"
  echo "Per tornare indietro: bash redazione/rilascia.sh annulla"
  ;;
annulla)
  pulito; prendi "$PRINC"; firma
  M=$(git log "origin/$PRINC" --merges --grep='^Rilascio ' -1 --format=%H)
  [ -n "$M" ] || fermo "nessun rilascio da annullare negli ultimi $FONDO commit del ramo principale"
  PRIMA=$(git rev-parse --abbrev-ref HEAD)
  git checkout -q --detach "origin/$PRINC" || fermo "checkout del ramo principale"
  if ! git revert -m 1 --no-edit "$M" >/dev/null 2>&1; then
    git revert --abort >/dev/null 2>&1; git checkout -q "$PRIMA"
    fermo "il rilascio $(git rev-parse --short "$M") non si toglie da solo: dopo sono cambiati gli stessi file (conflitto). Va corretto a mano sul ramo $RAMO"
  fi
  # le pagine del sito si rigenerano dall'indice di adesso: se dopo il rilascio è uscita un'edizione, resta al suo posto
  python3 redazione/pagine.py "$REPO" >/dev/null 2>&1; git add -A e dati ultima feed.xml sitemap.xml 2>/dev/null
  git diff --cached --quiet || git commit -q --amend --no-edit
  out=$(python3 redazione/collaudo.py 2>&1); rc=$?; echo "$out" | tail -4
  if [ $rc -ne 0 ]; then git checkout -q "$PRIMA"; fermo "senza il rilascio il collaudo è rosso: non tolgo nulla, va guardato a mano"; fi
  R=$(git rev-parse HEAD)
  if [ "$PROVA" = "1" ]; then echo "[prova] git push origin $R:refs/heads/$PRINC   (\"$(git log -1 --format=%s "$R")\")"; git checkout -q "$PRIMA"; echo "RILASCIO: PROVA - annullamento pronto, nessun push."; exit 0; fi
  spingi "$R" "$PRINC" || { git checkout -q "$PRIMA"; fermo "push dell'annullamento rifiutato: nulla è cambiato"; }
  git checkout -q "$PRIMA"
  echo "RILASCIO: ANNULLATO - il ramo principale è tornato a prima del rilascio $(git rev-parse --short "$M") (commit $(git rev-parse --short "$R"))."
  echo "Il lavoro resta sul ramo $RAMO. Per riproporlo dopo la correzione: 'avvia', poi git revert $(git rev-parse --short "$R") sul ramo $RAMO (riporta dentro il lavoro), correzione, 'pubblica'."
  ;;
*) echo "uso: rilascia.sh avvia [con-prova] | collauda | unisci <commit provato> | pubblica [--ok-di-paolo] [--dopo-la-prova] [--senza-github] [--guasto] | annulla"; exit 1;;
esac
exit 0
}
