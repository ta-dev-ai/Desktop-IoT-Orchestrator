# Frontend Backend Fonctionnalites V1

Projet: Desktop IoT Orchestrator
Application: MQTT Control Launcher + mqtt-dashboard
But: decrire ce qui se passe entre frontend et backend pour chaque action utilisateur.

## 1. Vue globale

Le projet V1 fonctionne comme ceci:

```text
Utilisateur
-> clique dans le dashboard
-> JavaScript runCommand(...)
-> fetch vers FastAPI
-> FastAPI execute la logique backend
-> reponse JSON
-> affichage dans les logs frontend
```

Le launcher desktop sert surtout a:

- ouvrir l'application;
- verifier les dependances en arriere-plan;
- demarrer FastAPI;
- afficher le dashboard;
- fournir la page Settings pour le diagnostic.

Le dashboard est la vraie interface principale utilisateur.

## 2. Fonction centrale du frontend

Fichier principal:

- `mqtt-dashboard/script.js`

Fonction principale:

```javascript
runCommand(commandName)
```

Quand l'utilisateur clique un bouton:

1. le frontend affiche immediatement une ligne dans les logs;
2. le frontend envoie un `fetch POST` vers FastAPI;
3. le frontend lit la reponse JSON;
4. le frontend affiche la reponse dans les logs;
5. si le backend renvoie une erreur, le frontend l'affiche dans les logs;
6. si l'action touche le broker, le statut visuel peut etre mis a jour.

## 3. Boutons Actions rapides

### 3.1 Demarrer Broker

Frontend:

- bouton: `Démarrer Broker`
- action JS: `runCommand("start-broker")`

Backend:

- route: `POST /api/commands/start-broker`
- fichier: `app/main.py`

Ce que fait le backend:

- verifie la presence de `mosquitto`;
- si un broker suivi est deja demarre, renvoie `déjà démarré`;
- sinon lance `mosquitto -v`;
- stocke le processus dans `BROKER_PROCESS`;
- renvoie `message`, `pid`, `command`.

Retour frontend:

- ajoute un log `Commande lancée : Démarrer Broker`
- affiche le JSON de succes ou d'erreur
- met `Statut Broker` a `Connecté`

### 3.2 Arreter Broker

Frontend:

- bouton: `Arrêter Broker`
- action JS: `runCommand("stop-broker")`

Backend:

- route: `POST /api/commands/stop-broker`

Ce que fait le backend:

- regarde si `BROKER_PROCESS` existe encore;
- si non, renvoie `Aucun broker démarré depuis ce launcher`;
- sinon appelle `terminate()` sur le processus;
- remet `BROKER_PROCESS = None`;
- renvoie `message` et `pid`.

Retour frontend:

- ajoute un log
- affiche la reponse JSON
- met `Statut Broker` a `Déconnecté`

### 3.3 Demarrer Subscriber

Frontend:

- bouton: `Démarrer Subscriber`
- action JS: `runCommand("start-subscriber")`

Backend:

- route: `POST /api/commands/start-subscriber`

Ce que fait le backend:

- verifie la presence de `mosquitto_sub`;
- si un subscriber suivi existe deja, renvoie `déjà démarré`;
- sinon lance:

```text
mosquitto_sub -h localhost -t temperature
```

- stocke le processus dans `SUBSCRIBER_PROCESS`;
- renvoie `message`, `pid`, `command`.

Retour frontend:

- ajoute un log local
- affiche la reponse JSON

### 3.4 Envoyer Message

Frontend:

- bouton: `Envoyer Message`
- action UI: ouverture d'une modal
- validation modal: `runCommand("publish-message")`

Backend:

- route dynamique: `POST /api/commands/publish-message`
- route statique historique: `POST /api/commands/publish-temperature`

Ce que fait le backend:

- verifie la presence de `mosquitto_pub`;
- lit `topic` et `message` depuis le frontend;
- lance:

```text
mosquitto_pub -h localhost -t <topic> -m "<message>"
```

- renvoie `message`, `pid`, `command`, `topic`, `payload`.

Retour frontend:

- ajoute un log local
- affiche le JSON de retour
- ajoute le message dans la liste `Envoyé`
- sauvegarde cet historique dans le navigateur

### 3.5 Redemarrer Broker

Frontend:

- bouton: `Redémarrer Broker`
- action JS: `runCommand("restart-broker")`

Backend:

- route: `POST /api/commands/restart-broker`

Ce que fait le backend:

- appelle `stop_broker()`
- puis appelle `start_broker()`

Retour frontend:

- ajoute un log local
- affiche la reponse JSON
- met `Statut Broker` a `Connecté`

### 3.6 Ouvrir Terminal

Frontend:

- bouton: `Ouvrir Terminal`
- action JS: `runCommand("open-terminal")`

Backend:

- route: `POST /api/commands/open-terminal`

Ce que fait le backend actuellement:

- n'ouvre pas encore une vraie console systeme;
- ajoute juste un log backend;
- renvoie une note JSON.

Conclusion:

- cette fonction est encore partiellement simulatee en V1.

## 4. Tableau des commandes

Le tableau `Commandes disponibles` ne lance pas une logique differente.

Chaque bouton `Exécuter` reutilise les memes routes backend que les actions rapides.

Correspondances:

- `mosquitto -v` -> `start-broker`
- `mosquitto_sub ...` -> `start-subscriber`
- `mosquitto_pub ...` -> `publish-temperature`
- `netstat -an | findstr :1883` -> `open-terminal`

Conclusion:

- le tableau est une autre entree UI vers les memes actions backend.

## 5. Settings frontend

Le dashboard a une vue `Settings`.

Frontend:

- menu sidebar `Settings`
- action JS: `showView("settings")`

Ce que fait le frontend:

- masque la vue dashboard;
- affiche la vue settings;
- appelle `loadSystemStatus()`.

Route backend:

- `GET /api/system/status`

Ce que fait le backend:

- utilise `build_dependency_report()` dans `launcher/checker.py`
- renvoie:
  - `ok`
  - `missing_count`
  - `items`
  - `summary`

Ce que voit l'utilisateur:

- statut global
- nombre d'elements manquants
- rapport texte des dependances

## 6. Logs frontend

Zone frontend:

- `Logs en direct`

Source:

- logs locaux JS
- reponses JSON du backend

Ce que le frontend ajoute:

- `Commande lancée : ...`
- erreurs `Impossible de contacter FastAPI`
- confirmation de chargement du rapport systeme

Important:

- ce panneau ne lit pas encore le buffer `LOGS` backend via polling;
- il affiche surtout les evenements frontend + reponses API.

## 7. Logs backend

Cote backend:

- `app/main.py`
- stockage dans `LOGS`

Routes liees:

- `GET /logs`

Utilisation actuelle:

- prevue pour suivi backend;
- pas encore branchee dans le dashboard principal par polling automatique.

## 8. Ce qui se passe quand une dependance manque

Exemple:

- `mosquitto` absent
- `mosquitto_sub` absent
- `mosquitto_pub` absent

Effet:

1. le dashboard reste accessible;
2. `Settings` montre les dependances manquantes;
3. un clic sur une action MQTT appelle quand meme FastAPI;
4. FastAPI renvoie une erreur claire:

```text
Commande introuvable: mosquitto...
```

5. le frontend affiche cette erreur dans les logs.

## 9. Ce qui est deja fonctionnel en V1

- launcher desktop
- affichage du dashboard
- check de dependances
- route systeme `GET /api/system/status`
- boutons frontend relies a FastAPI
- start/stop/restart broker cote logique backend
- start subscriber
- publish temperature
- fermeture launcher avec tentative d'arret backend

## 10. Ce qui est encore partiellement incomplet

- `Open terminal` ne lance pas encore une vraie fenetre systeme
- les messages MQTT dans la liste peuvent rester simules
- les logs backend ne sont pas encore synchronises en temps reel dans le dashboard
- la verification port 1883 cote UI reste surtout informative
- il faut encore tester chaque bouton en situation reelle avec Mosquitto installe

## 11. Parcours de verification recommande

### Test 1 - Dashboard s'affiche

1. ouvrir le launcher
2. verifier que le dashboard charge
3. verifier que la sidebar projet est visible

### Test 2 - Settings

1. ouvrir `Settings`
2. verifier le rapport de dependances
3. verifier le statut backend
4. verifier les ports

### Test 3 - Action sans Mosquitto

1. cliquer `Démarrer Broker`
2. verifier que le frontend affiche une erreur propre

### Test 4 - Action avec Mosquitto installe

1. cliquer `Démarrer Broker`
2. verifier la reponse JSON
3. verifier que le statut passe a `Connecté`
4. cliquer `Arrêter Broker`
5. verifier le retour a `Déconnecté`

### Test 5 - Subscriber et publication

1. cliquer `Démarrer Subscriber`
2. cliquer `Envoyer Message`
3. verifier les logs frontend
4. verifier les logs Mosquitto si disponibles

## 12. Conclusion

La V1 repose deja sur un vrai lien frontend -> backend.

Le role de chaque partie est clair:

- launcher = coque desktop + diagnostic
- dashboard = interface utilisateur principale
- FastAPI = pont entre UI et commandes
- Mosquitto = execution MQTT locale

La prochaine etape logique est de verifier chaque fonctionnalite une par une selon le use case utilisateur, puis corriger les points encore simules ou incomplets.
