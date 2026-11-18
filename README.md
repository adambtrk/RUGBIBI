# RugbyVision AI

Application Django d’analyse vidéo de rugby amateur, développée progressivement.

## Lancer en local (PowerShell)

Depuis le dossier contenant `manage.py` :

```powershell
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py runserver
```

Accueil : http://127.0.0.1:8000/ — Administration : http://127.0.0.1:8000/admin/

## Clubs et rôles

Dans l’administration, créer une division, puis un club, puis une adhésion
associant un utilisateur à ce club. Choisir Joueur ou Entraîneur / Analyste.
Un utilisateur peut avoir des rôles différents dans plusieurs clubs.
Désactiver une adhésion conserve son enregistrement et retire son accès au club.

Le rôle entraîneur ne donne pas accès à l’administration Django. Celle-ci utilise
les permissions Django ; le superutilisateur existant peut gérer les données.
Les contrôles `can_access_club` et `can_manage_club` devront être utilisés dans
les futures vues des matchs. Ils refusent les utilisateurs et adhésions inactifs.
Le statut `is_staff` seul ne donne aucun droit sur les clubs.

## Vérifier

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py test
```

Les tests utilisent une base temporaire et des données fictives.

## Avancement

- Fait : utilisateur personnalisé, connexion/déconnexion, accueil et style commun.
- Fait : divisions, clubs, adhésions, rôles par club, administration et tests.
- À venir : matchs et joueurs, vidéos protégées, timeline et annotation manuelle.
- Ensuite : statistiques, dataset, modèle de vision et validation humaine.

Configuration actuelle destinée au développement local.

La division (ex. Régionale 1, Fédérale 3) est renseignée sur le club.
Le joueur la retrouve par son adhésion au club. Ce premier modèle suppose
une division par club ; les équipes réserve et les changements par saison
seront à gérer lors de la création des équipes et saisons.
