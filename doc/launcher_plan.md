# Plan du launcher PySide6

## Objectif

Créer une application desktop unique qui démarre le projet `MQTT Control` via un exécutable Windows.

L'utilisateur final ne doit pas lancer plusieurs outils à la main. Il ouvre seulement le `.exe` du launcher, et celui-ci:

1. vérifie les dépendances,
2. répare ou installe ce qui manque quand c'est possible,
3. démarre le backend FastAPI,
4. affiche l'interface du dashboard,
5. montre les logs et l'état du projet dans une fenêtre PySide6.

## Expérience utilisateur visée

- L'utilisateur double-clique sur `Launcher.exe`
- Le launcher fait un contrôle rapide de l'environnement
- Si tout est prêt, le projet démarre automatiquement
- Si une dépendance manque, le launcher affiche une erreur claire ou lance l'installation
- L'interface reste simple, lisible et orientée débutant

## Dépendances à vérifier

### Python

- Python installé
- `pip` disponible

### Packages Python

- `PySide6`
- `fastapi`
- `uvicorn`

### Outils système

- `mosquitto`
- `mosquitto_sub`
- `mosquitto_pub`

## Comportement attendu au lancement

### 1. Vérification

Le launcher vérifie:

- la présence des commandes système,
- la présence des modules Python,
- la capacité à lancer le backend.

### 2. Réparation

Si un paquet Python manque:

- le launcher peut exécuter une installation via `pip`

Si Mosquitto manque:

- le launcher doit prévenir clairement l'utilisateur
- si une installation automatique n'est pas possible, il doit expliquer quoi faire

### 3. Démarrage

Quand tout est prêt:

- le backend FastAPI démarre
- le dashboard est affiché dans la fenêtre PySide6
- les logs restent visibles dans l'interface

## Structure recommandée

```text
smart_controlle_mosquitto/
├── app/
│   └── main.py
├── mqtt-dashboard/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── launcher/
│   ├── main.py
│   ├── checker.py
│   └── ui.py
├── doc/
│   └── launcher_plan.md
└── requirements.txt
```

## Fichiers du launcher

### `launcher/main.py`

- point d'entrée de l'application desktop
- initialise la fenêtre PySide6
- lance les vérifications au démarrage

### `launcher/checker.py`

- vérifie les dépendances
- lance les commandes de diagnostic
- retourne un état lisible par l'interface

### `launcher/ui.py`

- construit la fenêtre principale
- affiche les boutons, les logs et le dashboard
- gère l'interaction utilisateur

## Flux recommandé

```text
Utilisateur -> Launcher.exe -> Check dépendances -> Démarrage FastAPI -> Affichage dashboard
```

## Recommandation technique

Pour afficher le dashboard dans la fenêtre PySide6:

- utiliser `QWebEngineView` si on veut intégrer la page HTML dans l'application desktop
- garder le dashboard HTML actuel pour limiter la réécriture

## Points de vigilance

- Mosquitto peut nécessiter des droits particuliers sur Windows
- l'installation automatique complète n'est pas toujours garantie
- il faut éviter de redémarrer ou réinstaller inutilement à chaque ouverture
- il est préférable de faire un check rapide au lancement, puis un mode réparation si nécessaire

## Conclusion

Le meilleur compromis est:

- un launcher PySide6 unique
- une vérification automatique au démarrage
- un backend FastAPI conservé séparément
- un dashboard HTML réutilisé dans l'application desktop

Cette approche permet de garder une UX simple pour l'utilisateur et une base technique facile à maintenir.

