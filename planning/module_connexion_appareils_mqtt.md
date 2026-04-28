# Module connexion appareils MQTT

## Objectif

Compléter le prototype pour qu'il ne fasse pas seulement :

- démarrer FastAPI
- démarrer Mosquitto
- publier localement
- afficher une UI

mais aussi :

- enregistrer un appareil externe
- préparer ses informations de connexion MQTT
- l'aider à écouter la distribution du broker
- visualiser son état de connexion
- confirmer qu'il reçoit bien les messages

Ce module manque aujourd'hui pour rendre le prototype plus complet.

---

## Constat actuel

Le projet sait déjà gérer une partie importante :

- interface desktop
- backend FastAPI
- broker Mosquitto local
- publication MQTT locale
- subscriber local de test

Mais il manque une vraie couche "appareils externes".

Aujourd'hui, un autre appareil doit connaître manuellement :

- l'adresse du broker
- le port MQTT
- le topic

et se connecter seul.

Le projet n'aide pas encore assez cette étape.

---

## Ce que doit couvrir le nouveau module

Le module doit couvrir 4 besoins.

### 1. Déclarer un appareil

Le projet doit permettre d'ajouter un appareil cible avec au minimum :

- nom de l'appareil
- type d'appareil
- adresse IP ou hostname
- rôle : publisher, subscriber, ou les deux
- topic(s) à écouter
- topic(s) à publier

Exemple :

```text
Nom : ESP32 Salon
Type : capteur
IP : 192.168.1.25
Rôle : subscriber
Topic écoute : temperature
```

---

### 2. Générer les informations de connexion

Pour chaque appareil, le projet doit afficher clairement :

- broker host
- broker port
- topic
- exemple de commande ou exemple de configuration

Exemple :

```text
Broker : 192.168.1.10
Port : 1883
Topic : temperature
```

Exemple de commande :

```text
mosquitto_sub -h 192.168.1.10 -p 1883 -t temperature
```

---

### 3. Vérifier la connexion de l'appareil

Le projet doit proposer une vérification simple :

- appareil déclaré
- broker actif
- port ouvert
- appareil vu comme connecté ou non

Cette partie peut être progressive.

### MVP simple

Dans un premier temps, on peut afficher :

- broker prêt
- port MQTT ouvert
- dernier message reçu sur le topic

### Version améliorée

Plus tard, on pourra suivre :

- client ID MQTT
- timestamp de dernière activité
- statut en ligne/hors ligne

---

### 4. Voir si l'appareil reçoit réellement les messages

Le vrai besoin métier n'est pas seulement "publier".

Le vrai besoin est :

- envoyer un message
- savoir si l'appareil l'a reçu

Pour cela, il faut ajouter une boucle d'observation :

- publication depuis l'UI
- écoute via subscriber
- affichage des retours
- si possible topic retour ou ACK

---

## Architecture cible

```text
UI Dashboard
-> FastAPI
-> gestion broker Mosquitto
-> module appareils MQTT
-> appareils externes connectés au broker
```

Le module appareils MQTT doit devenir une vraie brique du projet.

---

## Contenu fonctionnel du module

### A. Registre des appareils

Créer une structure de stockage simple pour les appareils.

Format minimal :

```json
[
  {
    "id": "device-001",
    "name": "ESP32 Salon",
    "type": "sensor",
    "host": "192.168.1.25",
    "role": "subscriber",
    "topics_sub": ["temperature"],
    "topics_pub": [],
    "notes": "Capteur temperature salon"
  }
]
```

Stockage MVP recommandé :

- fichier JSON local

Pourquoi :

- simple
- lisible
- modifiable sans base de données

---

### B. API FastAPI pour les appareils

Ajouter des routes dédiées :

- `GET /api/devices`
- `POST /api/devices`
- `PUT /api/devices/{device_id}`
- `DELETE /api/devices/{device_id}`
- `GET /api/devices/{device_id}/mqtt-config`
- `GET /api/devices/{device_id}/status`

But :

- gérer les appareils
- préparer leur configuration MQTT
- afficher leur état dans l'UI

---

### C. Vue UI "Appareils"

Ajouter une nouvelle vue ou section dans le dashboard :

- liste des appareils
- bouton `Ajouter appareil`
- statut de connexion
- topics associés
- bouton `Voir configuration`

Affichage minimal recommandé :

- nom
- type
- host
- topic principal
- état

---

### D. Générateur de configuration

Le projet doit pouvoir produire une fiche simple par appareil :

- host broker
- port
- topic
- exemple publish
- exemple subscribe

Exemple de fiche :

```text
Appareil : ESP32 Salon
Broker : 192.168.1.10
Port : 1883
Subscribe topic : temperature
```

Exemple de code ou commande :

```text
mosquitto_sub -h 192.168.1.10 -p 1883 -t temperature
```

---

### E. Validation de réception

Pour rendre le prototype vraiment utile, il faut prévoir un mécanisme de validation.

Deux options.

### Option 1. Observation simple

Le projet affiche :

- message publié
- message observé par le subscriber local

Cela prouve que le broker distribue bien le message.

Limite :

- cela ne prouve pas qu'un appareil externe précis l'a traité

### Option 2. Topic de retour / ACK

L'appareil externe renvoie une confirmation sur un topic retour.

Exemple :

- publish sur `temperature`
- appareil répond sur `temperature/ack`

Le projet peut alors afficher :

- message envoyé
- accusé reçu
- date et heure

Cette option est la meilleure pour un vrai prototype démonstrable.

---

## Recommandation MVP

Pour ne pas compliquer trop tôt, on recommande un développement en 3 étapes.

### Étape 1. Registre des appareils

Ajouter :

- fichier JSON local
- API CRUD simple
- UI liste des appareils

Résultat :

- on peut déclarer les appareils

---

### Étape 2. Fiche de connexion MQTT

Ajouter :

- broker host
- port
- topics
- exemples de commande/configuration

Résultat :

- le projet aide réellement à connecter un appareil externe

---

### Étape 3. Validation des messages

Ajouter :

- affichage des messages envoyés
- affichage des messages reçus
- option ACK par topic retour

Résultat :

- on démontre qu'un appareil reçoit bien la distribution MQTT

---

## Plan d'implémentation proposé

### Phase 1. Backend

Créer :

- `app/devices.py` ou bloc équivalent
- modèle appareil
- lecture/écriture JSON
- routes `/api/devices`

---

### Phase 2. Frontend dashboard

Créer une nouvelle section :

- `Appareils`
- formulaire ajout appareil
- liste des appareils
- panneau détail appareil

---

### Phase 3. Intégration MQTT

Ajouter :

- génération des paramètres de connexion
- test de port broker
- suivi du subscriber local
- association topic -> appareil

---

### Phase 4. Validation de distribution

Ajouter :

- timestamp des messages
- message envoyé
- message reçu
- si possible ACK appareil

---

## Cas d'usage final visé

### Cas d'usage 1

L'utilisateur ouvre l'application.

Il voit :

- FastAPI actif
- Mosquitto actif
- port MQTT ouvert

---

### Cas d'usage 2

Il ajoute un appareil :

- nom
- IP
- topic

Le projet lui montre immédiatement :

- comment connecter l'appareil
- quelles commandes utiliser

---

### Cas d'usage 3

Il envoie un message depuis le dashboard.

Le projet affiche :

- message publié
- heure/date
- message reçu côté écoute
- si disponible, confirmation de l'appareil

---

## Définition de "prototype complet"

Le prototype pourra être considéré comme plus complet quand il saura :

- gérer le backend FastAPI
- gérer Mosquitto
- publier
- écouter
- déclarer des appareils externes
- fournir leur configuration MQTT
- afficher la circulation du message
- prouver la réception via observation ou ACK

---

## Décision recommandée

La prochaine brique à ajouter est :

**module appareils MQTT**

avec priorité :

1. registre des appareils
2. configuration de connexion
3. validation de réception

Cela complète la logique du projet sans casser la MVP actuelle.
