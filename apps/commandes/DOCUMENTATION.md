# 📊 Module Ventes + Commandes - Documentation Complète

## 🎯 Vue d'ensemble

Le module **Ventes + Commandes** est le cœur métier de **AutoPieces Pro**. Il gère:
- ✅ Ventes directes au comptoir (HTMX + API)
- ✅ Commandes à distance
- ✅ Gestion des paiements (espèces, mobile money, virement)
- ✅ Workflow complet (Validation → Préparation → Expédition → Livraison)
- ✅ Génération automatique de factures PDF
- ✅ Calcul automatique des remises
- ✅ Gestion du stock en temps réel

---

## 📁 Architecture

```
backend/apps/commandes/
├── models.py              # Modèles: Commande, LigneCommande, Paiement
├── serializers.py         # Sérialiseurs DRF
├── views.py               # ViewSets API + endpoints HTMX
├── urls.py                # Routes API
├── pdf_utils.py           # Génération PDF factures
├── admin.py               # Interface admin Django
├── apps.py                
├── tests.py               
└── migrations/

backend/apps/web/
├── views_commandes.py     # Vues web (formulaires)
└── (URLs intégrées dans web/urls.py)

backend/templates/web/
├── vente_directe.html              # Formulaire vente directe (HTMX)
├── panier_list.html                # Panier dynamique
└── recherche_produit.html          # Résultats recherche
```

---

## 📊 Modèles de Données

### **Commande**
```python
class Commande:
    numero              # N° unique (BSG-YYYYMMDDHHMMSS)
    client              # FK Client (nullable pour vente comptoir)
    type_vente          # COMMANDE | VENTE_DIRECTE
    statut              # EN_ATTENTE | VALIDEE | EN_PREPARATION | PRETE | EXPEDIEE | LIVREE | ANNULEE
    statut_paiement     # NON_PAYE | PARTIEL | PAYE
    
    total_ht            # Montant HT
    type_remise         # POURCENT | FIXE
    remise              # Valeur remise
    total_ttc           # Montant TTC
    
    localisation        # FK Localisation (point de vente)
    photo_colis         # Image colis (optionnel)
    notes               # Notes commande
    
    date_creation       # Auto
    date_validation     # Date validation
    date_expedition     # Date expédition
    cree_par            # FK User
    prepare_par         # FK User (optionnel)
```

### **LigneCommande**
```python
class LigneCommande:
    commande            # FK Commande (CASCADE)
    produit             # FK Produit (PROTECT)
    quantite            # Nombre articles
    prix_unitaire       # Prix à la vente
    sous_total          # Auto calculé (quantite * prix_unitaire)
```

### **Paiement**
```python
class Paiement:
    numero              # N° unique (PAY-YYYYMM-XXXX)
    commande            # FK Commande (CASCADE)
    montant             # Montant payé
    date_paiement       # Auto
    mode_paiement       # CASH | MOBILE_MONEY | VIREMENT | DIVERS
    reference_transaction  # Pour mobile money
    preuve_paiement     # Justificatif (image)
    enregistre_par      # FK User
```

### **Facture**
```python
class Facture:
    numero              # N° unique
    commande            # OneToOne Commande (CASCADE)
    date_emission       # Auto
    date_echeance       # Date limite paiement
    total_ttc           # Montant facturé
    montant_regle       # Payé à ce jour
    reste_a_payer       # Auto calculé
    statut              # EN_ATTENTE | PARTIELLE | PAIEE | ANNULEE
    fichier_pdf         # PDF généré
```

---

## 🚀 APIs Disponibles

### **Gestion Commandes (REST)**

```bash
# Liste avec filtres
GET /api/commandes/?statut=VALIDEE&client=5&date_debut=2024-01-01

# Détail
GET /api/commandes/{id}/

# Créer
POST /api/commandes/
{
    "client": 1,
    "type_vente": "COMMANDE",
    "localisation": 1,
    "lignes": [
        {"produit": 5, "quantite": 2, "prix_unitaire": 15000}
    ]
}

# Actions workflow
POST /api/commandes/{id}/valider/
POST /api/commandes/{id}/preparer/
POST /api/commandes/{id}/expedier/
POST /api/commandes/{id}/livrer/
POST /api/commandes/{id}/annuler/

# Paiement
POST /api/commandes/{id}/paiement/
{
    "montant": 50000,
    "mode_paiement": "CASH",
    "reference_transaction": "MM123456"
}

# PDF Facture
GET /api/commandes/{id}/generer_facture/
```

### **Vente Directe (HTMX)**

```bash
# Recherche produit live
GET /api/commandes/recherche-produit/?q=moteur&localisation=1

# Ajouter au panier
POST /api/commandes/panier/
{
    "commande_id": 1,
    "produit_id": 5,
    "quantite": 2
}

# Retirer du panier
DELETE /api/commandes/panier/{ligne_id}/

# Calculer remise
POST /api/commandes/calcul-remise/
{
    "commande_id": 1,
    "type_remise": "POURCENT",
    "valeur_remise": 10
}
```

---

## 🎨 Interface Web (Templates)

### **Vente Directe (`/vente-directe/`)**

Page complète avec:
- 🔍 Recherche produit en temps réel (HTMX)
- 🛒 Panier dynamique (ajouter/retirer sans rechargement)
- 💰 Calcul automatique totaux + remise
- 💳 Enregistrement paiement (4 modes)
- 📄 Génération facture PDF
- ⚡ Rafraîchissement instantané HTMX

### **Liste Commandes (`/commandes/`)**

Avec filtres:
- Statut (EN_ATTENTE, VALIDEE, etc.)
- Type vente (COMMANDE, VENTE_DIRECTE)
- Client
- Période (date début/fin)
- Recherche (numéro, client, notes)

### **Détail Commande (`/commandes/{id}/`)**

Affiche:
- Articles avec quantités et prix
- Historique paiements
- Statut et workflow
- Actions (valider, expédier, etc.)
- Télécharger facture PDF

---

## 💼 Cas d'Usage

### **1️⃣ Créer une Vente Directe**

```
1. Accéder à /vente-directe/
2. Sélectionner client (optionnel pour comptoir)
3. Rechercher produit (min 2 caractères)
4. Ajouter quantité
5. Cliquer "Ajouter au panier"
6. Répéter pour autres articles
7. Appliquer remise si nécessaire
8. Sélectionner mode paiement
9. Enregistrer paiement
10. Imprimer facture PDF
```

### **2️⃣ Commande à Distance**

```
API Flow:
1. POST /api/commandes/ (crée commande EN_ATTENTE)
2. POST /api/commandes/{id}/valider/ (réserve stock)
3. POST /api/commandes/{id}/preparer/ (prepare)
4. POST /api/commandes/{id}/expedier/
5. POST /api/commandes/{id}/livrer/
6. POST /api/commandes/{id}/paiement/ (encaisser)
```

### **3️⃣ Annulation Commande**

```
POST /api/commandes/{id}/annuler/
→ Si stock était réservé → restaure le stock
→ Statut devient ANNULEE
```

---

## 📊 Filtres Avancés

**Paramètres GET sur `/api/commandes/`:**

```
?statut=VALIDEE              # Filtre par statut
&type_vente=COMMANDE         # Type vente
&client=5                    # ID client
&date_debut=2024-01-01       # De cette date
&date_fin=2024-12-31         # Jusqu'à cette date
&statut_paiement=PARTIEL     # Statut paiement
&search=BSG-240115           # Recherche texte
&ordering=-date_creation     # Tri (- = DESC)
```

**Exemple complet:**
```bash
GET /api/commandes/?statut=VALIDEE&date_debut=2024-01-01&ordering=-total_ttc
```

---

## 🧮 Calcul des Totaux

### **Remise Pourcentage**
```
Total HT = Σ(quantite × prix_unitaire)
Remise = Total HT × (pourcentage / 100)
Total TTC = Total HT - Remise
```

### **Remise Montant Fixe**
```
Total HT = Σ(quantite × prix_unitaire)
Remise = Montant fixe
Total TTC = Total HT - Remise
```

---

## 💳 Modes de Paiement

| Mode | Champ Référence | Usage |
|------|-----------------|-------|
| **CASH** | - | Espèces |
| **MOBILE_MONEY** | reference_transaction | Code transaction MM |
| **VIREMENT** | reference_transaction | N° compte/RIB |
| **DIVERS** | reference_transaction | Autre mode |

---

## 📄 Génération PDF Facture

**Endpoint:** `GET /api/commandes/{id}/generer_facture/`

**Contenu PDF:**
- En-tête avec N° et date
- Infos client
- Tableau articles (produit, qté, prix)
- Calcul remise et TTC
- Historique paiements
- Reste à payer

**Librairie:** ReportLab (léger, pas besoin de wkhtmltopdf)

---

## 🔐 Permissions

| Action | Rôle Min. |
|--------|-----------|
| Voir commandes | Employé |
| Créer commande | Employé |
| Valider | Magasinier |
| Expédier | Logisticien |
| Enregistrer paiement | Employé |
| Générer PDF | Employé |

---

## 📱 Recherche Produit (HTMX)

**En temps réel avec:**
```html
<input 
    hx-get="/api/commandes/recherche-produit/"
    hx-trigger="keyup changed delay:300ms"
    hx-target="#results"
/>
```

**Retour:**
```json
{
    "results": [
        {
            "id": 5,
            "nom": "Moteur 1.5L",
            "reference": "MOT-015",
            "prix_unitaire": 450000,
            "quantite_dispo": 12,
            "unite": "pièce"
        }
    ]
}
```

---

## 🔄 Workflow Complet

```
EN_ATTENTE
    ↓ [valider]
VALIDEE → [Stock réservé]
    ↓ [preparer]
EN_PREPARATION
    ↓ [expedier]
EXPEDIEE
    ↓ [livrer]
LIVREE ← [paiement optionnel à tout moment]

[annuler] → ANNULEE (à tout moment si pas livrée)
                    ↓ Stock restauré
```

---

## 📊 Rapports Disponibles

### Via API:
```bash
# Total ventes du mois
GET /api/commandes/?date_debut=2024-01-01&date_fin=2024-01-31&statut_paiement=PAYE

# Commandes en attente paiement
GET /api/commandes/?statut_paiement=PARTIEL

# Ventes directes du jour
GET /api/commandes/?type_vente=VENTE_DIRECTE&date_debut=2024-01-15
```

---

## ⚙️ Configuration Requise

**Packages Python:**
```bash
pip install reportlab>=3.6.0  # PDF
pip install django-filter    # Filtres avancés
```

**Autres:**
- Localisation (point de vente) doit exister
- Client peut être vide (vente comptoir)
- Stock validé avant création commande

---

## 🚀 Déploiement & Utilisation

### **Backend Django**
```bash
python manage.py migrate
python manage.py collectstatic
```

### **Mobile (Flutter)**
```dart
// Utiliser les endpoints REST API
final response = await http.get(
    Uri.parse('http://api.autopieces.local/api/commandes/'),
    headers: {'Authorization': 'Bearer $token'}
);
```

### **Web (HTML/HTMX)**
```html
<script src="https://unpkg.com/htmx.org"></script>
<!-- Formulaire vente_directe.html inclus -->
```

---

## 🎓 Exemples d'Intégration

### **Créer commande et payer (cURL)**
```bash
# 1. Créer commande
curl -X POST http://localhost:8000/api/commandes/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client": 1,
    "type_vente": "COMMANDE",
    "lignes": [{"produit": 5, "quantite": 2, "prix_unitaire": 50000}]
  }'
# → Retour: {"id": 123, "numero": "BSG-240115120000", ...}

# 2. Valider
curl -X POST http://localhost:8000/api/commandes/123/valider/ \
  -H "Authorization: Bearer TOKEN"

# 3. Payer
curl -X POST http://localhost:8000/api/commandes/123/paiement/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"montant": 100000, "mode_paiement": "CASH"}'
```

---

## 🐛 Débogage

**Logs:**
```python
# Dans models.py ou views.py
import logging
logger = logging.getLogger(__name__)
logger.info(f"Commande créée: {commande.numero}")
```

**Tests API:**
```bash
# Utiliser Postman ou similaire
# Exemple: GET /api/commandes/?search=moteur
```

---

## 📞 Support & Assistance

Pour questions sur:
- **Modèles:** Voir `commandes/models.py`
- **APIs:** Voir `commandes/views.py` et `commandes/urls.py`
- **Templates:** Voir `templates/web/`

---

**✅ Module complètement implémenté et opérationnel!**
