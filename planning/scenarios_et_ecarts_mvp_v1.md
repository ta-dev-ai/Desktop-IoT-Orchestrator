# Scenarios Et Ecarts MVP V1

Projet: Desktop IoT Orchestrator
Version: V1 MVP
But: documenter les scenarios utilisateur, ce qui est deja implemente, et ce qui manque encore avant de declarer la V1 fonctionnelle.

## 1. Scenario global utilisateur

1. L'utilisateur ouvre le launcher desktop.
2. Le launcher verifie automatiquement les dependances.
3. Le launcher tente de demarrer FastAPI en arriere-plan.
4. Le dashboard projet s'affiche.
5. L'utilisateur clique sur une action.
6. L'UI montre immediatement un retour visible.
7. FastAPI execute la logique backend.
8. L'utilisateur voit le resultat, l'erreur, ou le message envoye/recu.
9. Si besoin, l'utilisateur ouvre `Settings` pour diagnostiquer.

## 2. Regle UX importante

Apres chaque clic, l'utilisateur doit voir:

- ce qu'il a demande;
- si c'est en cours;
- si c'est reussi ou en erreur;
- ce qui a ete envoye ou recu.

## 3. Scenarios fonctionnels V1

### 3.1 Demarrer Broker

Parcours:

1. clic sur `Demarrer Broker`
2. log immediat `demarrage en cours`
3. appel API backend
4. succes ou erreur visible
5. statut broker mis a jour

### 3.2 Arreter Broker

Parcours:

1. clic sur `Arreter Broker`
2. log immediat
3. appel backend
4. succes ou erreur visible
5. statut broker passe a `Deconnecte`

### 3.3 Demarrer Subscriber

Parcours:

1. clic sur `Demarrer Subscriber`
2. log immediat
3. appel backend
4. succes ou erreur visible

### 3.4 Envoyer Message

Parcours attendu:

1. clic sur `Envoyer Message`
2. ouverture d'une petite modal
3. saisie du `topic`
4. saisie du `message`
5. validation
6. log immediat
7. appel backend avec les vraies donnees
8. ajout du message dans la liste `Envoye`
9. reponse backend visible dans les logs

### 3.5 Redemarrer Broker

Parcours:

1. clic sur `Redemarrer Broker`
2. log immediat
3. backend arrete puis relance
4. succes ou erreur visible

### 3.6 Ouvrir Terminal

Parcours:

1. clic sur `Ouvrir Terminal`
2. ouverture d'une vraie fenetre `cmd`
3. log de confirmation

### 3.7 Settings

Parcours:

1. clic sur `Settings`
2. affichage du rapport dependances
3. affichage statut backend
4. affichage ports
5. affichage logs techniques
6. bouton de retour au projet

## 4. Ce qui est deja implemente

- launcher desktop
- boot automatique de base
- dashboard embarque
- page `Settings`
- check dependances
- boutons relies a FastAPI
- start/stop/restart broker
- start subscriber
- ouverture terminal cote backend

## 5. Ce qui manque encore ou reste incomplet

### Priorite haute

- affichage clair de ce qui a ete recu

### Priorite moyenne

- vraie fonction pour la ligne 4 du tableau `verifier port 1883`
- meilleure synchronisation des logs backend
- historique des messages plus realiste

### Priorite basse

- polissage UI compact
- petits ajustements d'ergonomie

## 6. Decision implementation immediate

La prochaine fonctionnalite a implementer maintenant est:

```text
Affichage clair des messages recus
```

Pourquoi:

- c'est une vraie fonctionnalite coeur du projet;
- l'etat actuel est trop statique;
- sans cela, l'utilisateur ne comprend pas clairement ce qu'il a envoye;
- cela rend la V1 plus proche d'une vraie MVP.

## 7. Definition de validation pour cette fonctionnalite

La fonctionnalite `Envoyer Message` est maintenant consideree validee si:

1. le clic sur `Envoyer Message` ouvre une modal;
2. l'utilisateur peut saisir `topic` et `message`;
3. le backend recoit ces valeurs;
4. le frontend affiche un log immediat;
5. le frontend affiche une reponse de succes ou d'erreur;
6. le message apparait dans la liste `Envoye`.
