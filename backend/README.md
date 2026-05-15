# BSG Dashboard Web

Application de gestion commerciale — Django + Bootstrap 5 + HTMX

## Démarrage rapide (développement)

```bash
# 1. Cloner et installer
pip install -r requirements.txt

# 2. Variables d'environnement (copier .env.example)
cp .env.example .env

# 3. Migrations (réutilise les modèles existants)
python manage.py migrate

# 4. Créer le premier admin
python manage.py createsuperuser

# 5. Lancer
python manage.py runserver
```

## Structure du projet

```
bsg_web/
├── config/
│   ├── settings.py       # Config principale
│   ├── urls.py           # Routes globales
│   └── wsgi.py
├── apps/
│   ├── web/              # ← App principale (vues HTML)
│   │   ├── views_auth.py
│   │   ├── views_dashboard.py
│   │   ├── views_commandes.py
│   │   ├── views_stock.py
│   │   ├── views_finances.py
│   │   ├── views_clients.py
│   │   ├── views_admin.py
│   │   ├── middleware.py      # Guards de rôle
│   │   ├── context_processors.py
│   │   └── urls.py
│   ├── auth_users/       # Modèle utilisateur (existant)
│   ├── commandes/        # Modèle commandes (existant)
│   ├── stock/            # Modèle stock (existant)
│   ├── finances/         # Journal financier (existant)
│   ├── clients/          # Clients (existant)
│   └── produits/         # Produits (existant)
├── templates/
│   └── web/
│       ├── base.html              # Layout principal
│       ├── auth/login.html
│       ├── dashboard/dashboard.html
│       ├── commandes/
│       ├── stock/
│       ├── finances/
│       └── admin/
├── static/
├── requirements.txt
└── render.yaml           # Déploiement Render.com
```

## Déploiement Render.com (Jour 7)

1. Pousser sur GitHub
2. Créer un nouveau Web Service sur render.com
3. Connecter le repo GitHub
4. Render détecte `render.yaml` automatiquement
5. Ajouter `SECRET_KEY` dans les variables d'environnement
6. Déployer → URL live en 5 minutes

## Rôles

| Rôle | Accès |
|------|-------|
| ADMIN | Tout : ventes, stock, finances, audit, utilisateurs |
| EMPLOYE | Ventes, clients, dépenses |
| MAGASINIER | Stock, transferts, fournisseurs |
