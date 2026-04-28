# Plan UI Correction - Launcher Desktop

Date: 2026-04-28
Projet: Desktop IoT Orchestrator
Zone concernee: `launcher/ui.py`, `app/main.py`, `mqtt-dashboard/`

## 1. Objectif

Transformer le launcher actuel en vraie application desktop simple:

- l'utilisateur ouvre l'app;
- l'app verifie les dependances;
- l'app lance FastAPI;
- l'app affiche le dashboard MQTT en grand;
- les details techniques restent disponibles dans une page Settings.

Priorite: corriger l'experience utilisateur avant d'ajouter de nouvelles fonctionnalites MQTT.

## 2. Probleme observe

### 2.1 Dans le launcher PySide6

Le dashboard est affiche dans un panneau a droite, pendant que le rapport de dependances reste visible a gauche.

Problemes:

- l'interface principale est trop petite;
- le dashboard est coupe horizontalement;
- l'utilisateur voit d'abord un ecran de debug au lieu d'une app SaaS;
- l'experience ne ressemble pas encore a une vraie application desktop.

### 2.2 Dans Chrome

La page `http://127.0.0.1:8000` peut encore afficher une ancienne UI si un ancien serveur FastAPI tourne.

Ca peut arriver quand:

- un ancien processus Uvicorn est encore actif;
- le navigateur garde une version precedente en cache;
- le launcher ouvre le fichier HTML local pendant que Chrome ouvre l'URL FastAPI.

## 3. Decision UX

Le launcher ne doit plus etre une page de diagnostic permanente.

Nouvelle logique:

- Dashboard = vue principale en plein espace;
- Settings/System Status = vue technique;
- Logs = vue de suivi;
- boutons de diagnostic = dans Settings, pas dans la page principale;
- la sidebar du dashboard `mqtt-dashboard` sert de navigation stable pour acceder a Dashboard, Logs et Settings.

## 4. Architecture UI cible

```text
MQTT Control Desktop
|
|-- Launcher PySide6
|   |-- lance/verifie le projet
|   |-- embarque le dashboard web
|
|-- Dashboard web mqtt-dashboard
    |
    |-- Sidebar UI projet
    |   |-- Logo: MQTT Control
    |   |-- Dashboard
    |   |-- Commandes
    |   |-- Logs
    |   |-- Settings
    |   |-- statut broker compact
    |
    |-- Zone principale
        |-- Dashboard metriques/actions
        |-- ou Logs
        |-- ou Settings dependances/systeme
```

## 5. Plan fonctionnel etape par etape

### Etape 1 - Corriger l'affichage principal

Objectif:

- supprimer le split permanent gauche/droite;
- afficher le dashboard dans toute la zone centrale;
- garder le rapport de dependances dans un onglet Settings.

Actions:

- remplacer le `QSplitter` par un layout principal vertical;
- garder le dashboard web en pleine largeur dans le launcher;
- utiliser la sidebar existante de `mqtt-dashboard`;
- ajouter/ameliorer l'entree `Settings` dans cette sidebar;
- garder `Dashboard` comme vue par defaut;
- deplacer le rapport dependances dans la vue Settings du dashboard;
- conserver les boutons `Check dependencies`, `Launch project`, `Open dashboard`.

Critere de validation:

- au lancement, le dashboard occupe presque toute la fenetre;
- le rapport de dependances n'est plus visible par defaut;
- l'entree Settings de la sidebar UI projet affiche toujours le rapport complet.

### Detail page Settings

Objectif:

- centraliser tout ce qui est technique;
- eviter de melanger l'usage normal et le debug.

Contenu Settings:

- statut global: ready / attention needed;
- rapport complet des dependances;
- bouton `Check dependencies` si expose par le launcher/backend;
- bouton `Launch project` uniquement si utile dans le contexte desktop;
- bouton `Open dashboard` uniquement dans le launcher, pas obligatoire dans l'UI projet;
- plus tard: bouton `Restart backend`;
- plus tard: verification ports `8000` et `1883`.

Critere de validation:

- un debutant peut cliquer `Settings` pour comprendre ce qui manque;
- le dashboard reste propre et non encombre.

### Etape 2 - Lancement automatique propre

Objectif:

- rendre l'app plus proche d'un vrai `.exe`;
- l'utilisateur n'a pas besoin de cliquer partout.

Actions:

- au demarrage, lancer `refresh_report()`;
- si les dependances Python sont OK, lancer FastAPI automatiquement;
- charger `http://127.0.0.1:8000/dashboard` apres un delai court;
- si FastAPI echoue, afficher une alerte dans Settings/logs.

Critere de validation:

- ouvrir le launcher suffit pour demarrer le backend;
- le dashboard apparait automatiquement;
- les erreurs restent visibles dans Settings/logs.

### Etape 3 - Gestion des anciens serveurs

Objectif:

- eviter que Chrome ou le launcher affichent une ancienne version.

Actions:

- verifier si le port `8000` est deja utilise avant de lancer Uvicorn;
- si le port est occupe, afficher un message clair;
- ajouter une action `Restart backend`;
- documenter la regle: fermer l'ancien serveur avant test.

Critere de validation:

- si un backend tourne deja, l'app ne lance pas un deuxieme processus sans prevenir;
- l'utilisateur comprend quoi faire.

### Etape 4 - Feedback visuel dans le dashboard

Objectif:

- rendre les boutons plus rassurants pour debutant.

Actions:

- afficher `loading` sur le bouton clique;
- afficher succes/echec dans les logs;
- mettre a jour `Statut Broker`;
- afficher une petite notification dans l'UI.

Critere de validation:

- quand l'utilisateur clique, il voit immediatement une reaction;
- si Mosquitto manque, le message est clair.

### Etape 5 - Messages MQTT reels

Objectif:

- remplacer les messages simules par des donnees backend.

Actions:

- ajouter une route `GET /api/messages`;
- stocker les messages publies/recus dans le backend;
- rafraichir la liste cote JS avec `fetch`;
- plus tard: passer en WebSocket ou Server-Sent Events.

Critere de validation:

- cliquer `Envoyer Message` ajoute un message visible dans la liste;
- le log backend et l'UI racontent la meme chose.

## 6. Premiere fonctionnalite a developper maintenant

Fonctionnalite choisie: `Etape 1 - Corriger l'affichage principal`.

Pourquoi celle-ci d'abord:

- c'est le probleme visible dans la capture;
- elle ne depend pas de Mosquitto;
- elle rend l'app plus professionnelle tout de suite;
- elle prepare les prochaines fonctions sans complexifier le backend;
- elle valide la logique sidebar du dashboard: Dashboard propre, Settings technique.

## 7. Fichiers impactes prevus

```text
launcher/ui.py
```

Possibles fichiers plus tard:

```text
app/main.py
mqtt-dashboard/script.js
mqtt-dashboard/style.css
planning/functional_roadmap.md
```

## 8. Tests prevus apres implementation

Commandes:

```powershell
.\.venv\Scripts\python.exe -m py_compile launcher\ui.py app\main.py
npm run check
git status --short --branch
```

Test manuel:

```text
1. Ouvrir le launcher.
2. Verifier que Dashboard est visible par defaut.
3. Verifier que Settings contient le rapport dependances.
4. Cliquer Launch project.
5. Verifier que le dashboard charge depuis FastAPI.
6. Ouvrir http://127.0.0.1:8000/dashboard dans Chrome.
```

## 9. Regle de travail

On developpe une fonctionnalite a la fois:

```text
planifier -> coder -> tester -> corriger -> commit -> push
```

Pas de grosse refonte cachee.
Chaque etape doit rester comprensible pour un debutant.
