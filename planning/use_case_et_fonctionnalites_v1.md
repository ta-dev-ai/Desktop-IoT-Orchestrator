# Use Case Et Fonctionnalites V1

Projet: Desktop IoT Orchestrator
Application: MQTT Control Launcher + mqtt-dashboard
Version cible: V1 MVP

## 1. Objectif utilisateur

L'application permet a un utilisateur de piloter un environnement local MQTT depuis une interface desktop simple.

L'utilisateur ne doit pas avoir besoin de lancer plusieurs commandes manuellement pour commencer.

Le but de la V1 est:

- ouvrir l'application;
- verifier l'environnement;
- lancer le backend;
- afficher le dashboard;
- executer des actions MQTT simples;
- voir les logs et erreurs;
- diagnostiquer les problemes dans Settings.

## 2. Use Case Principal

### Scenario standard

1. L'utilisateur ouvre `MQTT Control Launcher`.
2. Le launcher verifie les dependances en arriere-plan.
3. Le launcher tente de lancer FastAPI.
4. Le launcher affiche le dashboard du projet.
5. L'utilisateur utilise les boutons du dashboard pour agir sur MQTT.
6. Si un probleme arrive, l'utilisateur ouvre `Settings`.

### Resultat attendu

- le dashboard est la vue principale;
- les details techniques ne bloquent pas l'usage;
- les erreurs restent visibles et compréhensibles;
- la fermeture du launcher doit stopper le backend.

## 3. Architecture Fonctionnelle V1

```text
Utilisateur
-> Launcher desktop
-> Dashboard projet
-> FastAPI backend
-> Commandes systeme / Mosquitto
```

## 4. Rôle de chaque composant

### Launcher desktop

Responsabilites:

- ouvrir l'application;
- verifier les dependances;
- lancer le backend FastAPI;
- afficher le dashboard dans une fenetre desktop;
- fournir les pages `Commandes`, `Logs`, `Settings`;
- arreter le backend a la fermeture.

### Dashboard projet

Responsabilites:

- afficher l'interface principale;
- proposer les actions rapides;
- montrer les statistiques et messages;
- permettre d'ouvrir `Settings` cote UI;
- appeler FastAPI avec `fetch`.

### FastAPI

Responsabilites:

- recevoir les appels venant du dashboard;
- executer les commandes backend;
- renvoyer des reponses JSON claires;
- exposer les routes systeme et commandes.

### Mosquitto

Responsabilites:

- jouer le role de broker MQTT local;
- recevoir publications et abonnements;
- permettre les tests de messages.

## 5. Fonctionnalites V1

### 5.1 Boot automatique

Description:

- au demarrage, l'application lance automatiquement:
  - check dependencies
  - launch FastAPI
  - open dashboard

Statut attendu:

- visible pour l'utilisateur sans manipulation complexe.

### 5.2 Dashboard principal

Description:

- le dashboard est la vue principale;
- il occupe la plus grande partie de la fenetre;
- l'utilisateur y voit les cartes KPI, actions rapides, commandes, logs, messages.

Statut attendu:

- interface lisible et centrée sur l'usage.

### 5.3 Sidebar du projet

Description:

- la sidebar principale est celle du dashboard projet;
- elle contient `Dashboard`, `Commandes`, `Logs`, `Settings`.

Statut attendu:

- une seule navigation principale visible dans la partie projet.

### 5.4 Settings / System Status

Description:

- page reservee au diagnostic;
- affiche:
  - dependency check
  - backend status
  - ports
  - logs techniques
  - boutons `recheck dependencies`, `restart backend`, `open dashboard`

Statut attendu:

- l'utilisateur peut comprendre ce qui manque sans casser l'experience principale.

### 5.5 Actions MQTT

Description:

- boutons dashboard relies a FastAPI:
  - start broker
  - stop broker
  - start subscriber
  - publish temperature
  - restart broker
  - open terminal

Statut attendu:

- chaque action appelle une route backend;
- chaque action ecrit dans les logs;
- chaque erreur est lisible.

### 5.6 Logs

Description:

- logs dashboard pour les actions utilisateur;
- logs techniques launcher/backend pour le diagnostic.

Statut attendu:

- separer usage normal et debug.

### 5.7 Fermeture propre

Description:

- fermer le launcher doit arreter le backend FastAPI.

Statut attendu:

- pas de vieux serveur qui reste actif sur le port 8000.

## 6. Routes backend attendues

### Routes UI/Systeme

- `GET /`
- `GET /dashboard`
- `GET /dashboard/`
- `GET /style.css`
- `GET /script.js`
- `GET /health`
- `GET /logs`
- `GET /api/system/status`

### Routes commandes

- `POST /api/commands/start-broker`
- `POST /api/commands/stop-broker`
- `POST /api/commands/start-subscriber`
- `POST /api/commands/publish-temperature`
- `POST /api/commands/restart-broker`
- `POST /api/commands/open-terminal`

## 7. Parcours utilisateur simple

### Parcours 1 - Utilisateur debutant

1. Ouvre l'application.
2. Attend l'ouverture automatique du dashboard.
3. Clique `Démarrer Broker`.
4. Regarde les logs.
5. Va dans `Settings` si une erreur apparait.

### Parcours 2 - Diagnostic

1. Ouvre `Settings`.
2. Lit le rapport de dependances.
3. Verifie le statut du backend.
4. Verifie les ports.
5. Relance le backend si necessaire.

## 8. Limites actuelles V1

- Mosquitto peut manquer sur la machine;
- les messages MQTT affiches peuvent encore etre partiellement simules;
- le launcher est encore en stabilisation UX;
- la version V2 UI SaaS plus ambitieuse est separee du MVP.

## 9. Definition de V1 validee

La V1 est consideree comme validee si:

- le launcher s'ouvre;
- le backend demarre;
- le dashboard s'affiche;
- Settings fonctionne;
- les boutons appellent FastAPI;
- les erreurs sont lisibles;
- fermer l'application arrete le backend.
