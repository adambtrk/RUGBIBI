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
- Fait : import de matchs MP4, liste privée, lecteur avec navigation temporelle.
- À venir : timeline collective, annotation des intervalles et export du dataset.
- Ensuite : statistiques, dataset, modèle de vision et validation humaine.

Configuration actuelle destinée au développement local.

La division (ex. Régionale 1, Fédérale 3) est renseignée sur le club.
Le joueur la retrouve par son adhésion au club. Ce premier modèle suppose
une division par club ; les équipes réserve et les changements par saison
seront à gérer lors de la création des équipes et saisons.

## Import et lecture vidéo

Après connexion, ouvrir `/matches/`, renseigner le titre et la date, puis importer
un MP4 (limite actuelle : 8 Go). Les fichiers restent dans `private_media/`,
exclu de Git. Ne pas configurer de route publique MEDIA en développement.
Le propriétaire et les superutilisateurs peuvent consulter un match. Le partage
au club sera ajouté ultérieurement ; les comptes existants servent à protéger
les fichiers, sans développer de nouveaux parcours de connexion.

Le serveur vérifie l'extension, la taille, les boîtes du conteneur MP4 et la
présence d'une piste vidéo. Il ne décode pas le fichier et ne certifie donc ni
son intégrité complète ni la compatibilité de son codec. Privilégier H.264/AAC.
Les tests utilisent des conteneurs synthétiques non lisibles ; la lecture réelle
doit être vérifiée avec un MP4 Veo.

Le lecteur utilise une route protégée acceptant les requêtes HTTP Range pour
naviguer sans charger le match entier en mémoire. Les boutons permettent de
reculer/avancer de 10 secondes, changer la vitesse et saisir un temps vidéo en
minutes:secondes. Aucun événement n'est encore détecté automatiquement.

Pour un match complet, vérifier l'espace disque disponible (fichier temporaire
d'import et copie finale). Cette première version est destinée au serveur local ;
les imports reprenables et le service vidéo en production restent à concevoir.
