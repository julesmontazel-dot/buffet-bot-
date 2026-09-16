# Screener Buffett automatisé — Guide de mise en route

Cette application analyse chaque jour un lot d'entreprises cotées et compare
leur **capitalisation boursière** à leur **valeur nette comptable**
(capitaux propres). Si la capitalisation est inférieure à la valeur nette,
c'est une **analyse positive** (marge de sécurité, méthode Graham/Buffett).

Tu reçois un résumé sur **Telegram** chaque matin à 8h, sur ton iPhone et
ton Mac simultanément. Le détail de toutes les entreprises suivies est
consultable dans un **Google Sheet**, triable par colonne "Résultat".

Aucune compétence en code n'est nécessaire pour la suite : suis simplement
les 4 étapes ci-dessous (environ 20-30 minutes au total).

---

## Étape 1 — Créer ton bot Telegram (5 min)

1. Installe l'app Telegram sur ton iPhone et sur ton Mac si ce n'est pas
   déjà fait, connecte-toi avec ton numéro de téléphone.
2. Dans Telegram, cherche le contact **@BotFather** et ouvre une
   conversation.
3. Envoie la commande `/newbot`, choisis un nom (ex: "Mon Screener Buffett")
   puis un identifiant unique se terminant par "bot" (ex: `buffett_screener_bot`).
4. BotFather te donne un **token** du type `123456789:AAExxxxxxx...` —
   copie-le, tu en auras besoin à l'étape 4.
5. Envoie n'importe quel message à ton nouveau bot (cherche-le par son nom
   dans Telegram et écris "bonjour").
6. Ouvre cette page dans ton navigateur (remplace TOKEN par le tien) :
   `https://api.telegram.org/botTOKEN/getUpdates`
   Tu y trouveras un champ `"chat":{"id":123456789,...}` — ce nombre est
   ton **chat_id**, note-le aussi.

## Étape 2 — Créer le Google Sheet et l'accès technique (10 min)

1. Va sur [Google Sheets](https://sheets.new) et crée une feuille vide,
   nomme-la par exemple "Suivi Entreprises Buffett".
2. Récupère son **ID** dans l'URL :
   `https://docs.google.com/spreadsheets/d/CET-ID-ICI/edit`
3. Va sur [Google Cloud Console], crée
   un nouveau projet (nom libre).
4. Dans "APIs & Services" → "Library", active **Google Sheets API** et
   **Google Drive API**.
5. Dans "APIs & Services" → "Credentials" → "Create Credentials" →
   "Service Account". Donne-lui un nom, valide les écrans suivants.
6. Ouvre le compte de service créé → onglet "Keys" → "Add Key" → "JSON".
   Un fichier `.json` se télécharge : garde-le, tu en auras besoin à
   l'étape 4.
7. Dans ce fichier JSON, copie l'adresse email du champ `client_email`
   (ressemble à `xxx@xxx.iam.gserviceaccount.com`).
8. Retourne sur ton Google Sheet → bouton "Partager" → colle cet email
   avec le rôle **Éditeur**.

## Étape 3 — Créer ton compte GitHub et déposer le projet (5 min)

1. Crée un compte gratuit sur [github.com](https://github.com) si tu n'en
   as pas.
2. Crée un nouveau **repository privé** (bouton vert "New").
3. Dépose tous les fichiers de ce projet dedans (glisser-déposer possible
   depuis l'interface web GitHub, "Add file" → "Upload files").

## Étape 4 — Renseigner les secrets (5 min)

Dans ton repository GitHub : "Settings" → "Secrets and variables" →
"Actions" → "New repository secret". Crée ces 4 secrets :

| Nom du secret | Valeur |
|---|---|
| `TELEGRAM_BOT_TOKEN` | le token obtenu à l'étape 1 |
| `TELEGRAM_CHAT_ID` | le chat_id obtenu à l'étape 1 |
| `GOOGLE_SHEET_ID` | l'ID du Sheet obtenu à l'étape 2 |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | le **contenu complet** du fichier `.json` téléchargé à l'étape 2 (ouvre-le avec un éditeur de texte et colle tout) |

## Étape 5 — Lancer un premier test

Dans ton repository GitHub → onglet "Actions" → sélectionne le workflow
"Analyse quotidienne Buffett" → bouton "Run workflow" (fonctionne grâce à
`workflow_dispatch` dans le fichier `.github/workflows/daily.yml`).

Si tout est bien configuré, tu reçois une notification Telegram après
quelques minutes, et ton Google Sheet se remplit.

Ensuite, plus rien à faire : le workflow se relance automatiquement
**chaque jour à 8h**, 24h/24, sans que ton ordinateur ait besoin d'être
allumé (tout tourne sur les serveurs gratuits de GitHub).

---

## Comment ça fonctionne (résumé technique)

- `fetch_universe.py` télécharge la liste publique des entreprises cotées
  au Nasdaq et au NYSE (~6000-8000 sociétés).
- `analyze.py` traite un lot de 300 entreprises par jour (pour rester
  dans les limites gratuites), calcule capitalisation vs valeur nette,
  et écrit le résultat dans le Google Sheet. Une entreprise déjà
  analysée n'est recontrôlée que 30 jours plus tard (ou si un changement
  du nombre d'actions émises est détecté), pour ne pas la ré-analyser
  inutilement.
- `notify.py` envoie le résumé du jour sur Telegram.
- Le fichier `.github/workflows/daily.yml` déclenche tout ça
  automatiquement chaque jour.

## Limites actuelles et évolutions possibles

- **Couverture** : Nasdaq + NYSE au démarrage (marché US). On peut
  ajouter Euronext Paris, le London Stock Exchange, etc. en étendant
  `fetch_universe.py` avec d'autres sources publiques gratuites.
- **Fiabilité des données** : `yfinance` interroge Yahoo Finance de façon
  non-officielle ; les données de bilan (capitaux propres) manquent
  parfois pour certaines petites capitalisations — ces entreprises sont
  ignorées proprement plutôt que de fausser l'analyse.
- **Horaire d'été/hiver** : le cron GitHub Actions est en UTC fixe, donc
  la notification peut arriver à 7h ou 8h selon la saison (voir
  commentaire dans `daily.yml`).
