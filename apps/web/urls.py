from django.urls import path
from django.shortcuts import redirect
from web import (
    views_auth, views_dashboard,
    views_commandes, views_stock,
    views_finances, views_clients, views_admin,
)

app_name = 'web'

urlpatterns = [
    path('login/',   views_auth.login_view,    name='login'),
    path('logout/',  views_auth.logout_view,   name='logout'),
    path('utilisateurs/nouveau/', views_auth.create_user_view, name='create_user'),
    path('dashboard/', views_dashboard.dashboard_view, name='dashboard'),
    path('commandes/',                    views_commandes.commandes_liste,   name='commandes_liste'),
    path('commandes/<int:pk>/',           views_commandes.commande_detail,   name='commande_detail'),
    path('commandes/<int:pk>/action/<str:action>/', views_commandes.commande_action, name='commande_action'),
    path('commandes/<int:pk>/paiement/',  views_commandes.commande_paiement, name='commande_paiement'),
    path('vente-directe/',                views_commandes.vente_directe,     name='vente_directe'),
    path('htmx/produits/search/',         views_commandes.produit_search_htmx, name='produit_search'),
    path('stock/',                        views_stock.stock_liste,       name='stock_liste'),
    path('stock/entree/',                 views_stock.stock_entree,      name='stock_entree'),
    path('stock/transferts/',             views_stock.transferts_liste,  name='transferts_liste'),
    path('stock/transferts/nouveau/',     views_stock.transfert_nouveau, name='transfert_nouveau'),
    path('stock/transferts/<int:pk>/expedier/', views_stock.transfert_expedier, name='transfert_expedier'),
    path('stock/transferts/<int:pk>/recevoir/', views_stock.transfert_recevoir, name='transfert_recevoir'),
    path('produits/',                     views_admin.produits_liste,    name='produits_liste'),
    path('produits/nouveau/',             views_admin.produit_nouveau,   name='produit_nouveau'),
    path('finances/',                     views_finances.finances_liste,    name='finances_liste'),
    path('finances/depenses/',            views_finances.depenses_liste,    name='depenses_liste'),
    path('finances/depenses/nouvelle/',   views_finances.depense_nouvelle,  name='depenses_nouvelle'),
    path('finances/export/excel/',        views_finances.export_journal_excel, name='export_journal'),
    path('clients/',                      views_clients.clients_liste,   name='clients_liste'),
    path('clients/<int:pk>/',             views_clients.client_detail,   name='client_detail'),
    path('clients/nouveau/',              views_clients.client_nouveau,  name='client_nouveau'),

    path('administration/utilisateurs/',           views_admin.gestion_acces,       name='gestion_acces'),
    path('administration/utilisateurs/<int:pk>/toggle/', views_admin.user_toggle_actif,  name='user_toggle'),
    path('administration/utilisateurs/<int:pk>/role/',   views_admin.user_change_role,   name='user_role'),
    path('administration/audit/',                  views_admin.audit_liste,         name='audit_liste'),
]

# ── Employés / Accès ──────────────────────────────────────────────────────────
from web import views_employes
urlpatterns += [
    path('employes/',                          views_employes.employes_liste,          name='employes_liste'),
    path('employes/nouveau/',                  views_employes.employe_nouveau,          name='employe_nouveau'),
    path('employes/<int:pk>/toggle/',          views_employes.employe_toggle_actif,     name='employe_toggle'),
    path('employes/<int:pk>/role/',            views_employes.employe_change_role,      name='employe_role'),
    path('employes/<int:pk>/reset-password/',  views_employes.employe_reset_password,   name='employe_reset_password'),
    path('employes/export/pdf/',               views_employes.employes_export_pdf,      name='employes_pdf'),
]

# ── Finances supplémentaires ───────────────────────────────────────────────────
from web import views_finances as vf
urlpatterns += [
    path('finances/rapport/',             vf.rapport_financier,     name='rapport_financier'),
    path('finances/solde/',               vf.solde_caisse_json,     name='solde_caisse_json'),
]

# ── Rapport dettes clients ─────────────────────────────────────────────────
from web import views_dettes
urlpatterns += [
    path('clients/rapport-dettes/',            views_dettes.rapport_dettes,       name='rapport_dettes'),
    path('clients/<int:pk>/impayes/',          views_dettes.client_impayes,        name='client_impayes'),
    path('clients/<int:pk>/whatsapp/',         views_dettes.client_whatsapp,       name='client_whatsapp'),
    path('clients/export/dettes/',             views_dettes.export_dettes_excel,   name='export_dettes_excel'),
]

# ── Achats fournisseur ─────────────────────────────────────────────────────
from web import views_achats
urlpatterns += [
    path('achats/',                       views_achats.achats_liste,        name='achats_liste'),
    path('achats/nouveau/',               views_achats.achat_nouveau,        name='achat_nouveau'),
    path('achats/<int:pk>/',              views_achats.achat_detail,         name='achat_detail'),
    path('achats/<int:pk>/envoyer/',      views_achats.achat_envoyer,        name='achat_envoyer'),
    path('achats/<int:pk>/recevoir/',     views_achats.achat_recevoir,       name='achat_recevoir'),
    path('fournisseurs/',                 views_achats.fournisseurs_liste,   name='fournisseurs_liste'),
    path('fournisseurs/nouveau/',         views_achats.fournisseur_nouveau,  name='fournisseur_nouveau'),
]

# ── Intelligence Artificielle ──────────────────────────────────────────────
from web import views_ia
urlpatterns += [
    path('ia/',                   views_ia.dashboard_ia,        name='dashboard_ia'),
    path('ia/ventes/',            views_ia.ia_ventes,           name='ia_ventes'),
    path('ia/anomalies/',         views_ia.ia_anomalies,        name='ia_anomalies'),
    path('ia/recommandations/',   views_ia.ia_recommandations,  name='ia_recommandations'),
    path('ia/rentabilite/',       views_ia.ia_rentabilite,      name='ia_rentabilite'),
    path('ia/alertes.json',       views_ia.ia_alertes_json,     name='ia_alertes_json'),
]



# ── Facture PDF ───────────────────────────────────────────────────────────────
from web import views_facture
urlpatterns += [
    path('commandes/<int:pk>/facture/', views_facture.facture_pdf, name='facture_pdf'),
]

# ── Reset mot de passe ────────────────────────────────────────────────────────
from web import views_password_reset
urlpatterns += [
    path('mot-de-passe-oublie/', views_password_reset.password_reset_request, name='password_reset_request'),
    path('reset-password/<str:token>/', views_password_reset.password_reset_confirm, name='password_reset_confirm'),
]

# ── Objectifs de vente ───────────────────────────────────────────────────────
from web import views_objectifs
urlpatterns += [
    path('objectifs/',         views_objectifs.objectifs_view,  name='objectifs'),
    path('objectifs/update/',  views_objectifs.objectif_update, name='objectif_update'),
]

# ── Logs de connexion ────────────────────────────────────────────────────────
from web import views_securite
urlpatterns += [
    path('administration/logs-connexion/', views_securite.logs_connexion, name='logs_connexion'),
]

# ── PWA ───────────────────────────────────────────────────────────────────────
from django.views.generic import TemplateView
from django.views.static import serve
from django.conf import settings
urlpatterns += [
    path('offline/',    TemplateView.as_view(template_name='web/offline.html'), name='offline'),
    path('manifest.json', serve, {'document_root': settings.STATIC_ROOT, 'path': 'web/manifest.json'}, name='manifest'),
]

# ── Multi-devises ────────────────────────────────────────────────────────────
from web import views_devises
urlpatterns += [
    path('administration/devises/',         views_devises.devises_view,          name='devises'),
    path('administration/devises/refresh/', views_devises.devises_refresh,       name='devises_refresh'),
    path('administration/devises/convert/', views_devises.devises_convertir_json, name='devises_convert'),
]

# ── Import produits ───────────────────────────────────────────────────────────
from web import views_import, views_import_modele
urlpatterns += [
    path('administration/import-produits/',         views_import.import_produits,              name='import_produits'),
    path('administration/import-produits/modele/',  views_import_modele.telecharger_modele_csv, name='import_modele_csv'),
]

# ── Notifications & Alertes ──────────────────────────────────────────────────
from web import views_notifications
urlpatterns += [
    path('notifications/',         views_notifications.notifications_liste,    name='notifications'),
    path('notifications/json/',    views_notifications.notifications_json,     name='notifications_json'),
    path('notifications/lu/',      views_notifications.notifications_marquer_lu, name='notifications_marquer_lu'),
    path('notifications/stock/',   views_notifications.alertes_stock_vue,      name='alertes_stock_vue'),
]

# ── IA Avancée (Score Risque & Réappro) ─────────────────────────────────────
from web import views_score_risque, views_reappro, views_assistant
urlpatterns += [
    path('ia/score-risque/',       views_score_risque.score_risque_view,       name='score_risque'),
    path('ia/reappro/',            views_reappro.reappro_view,                 name='reappro'),
    path('ia/reappro/valider/',    views_reappro.reappro_valider,              name='reappro_valider'),
    path('ia/assistant/',          views_assistant.assistant_view,             name='assistant'),
    path('ia/assistant/query/',    views_assistant.assistant_query,            name='assistant_query'),
]

# # ── Analyse Financière (méthode P. Quiry) ─────────────────────────────────────
# from web import views_analyse_financiere
# urlpatterns += [
#     path('finances/analyse/', views_analyse_financiere.analyse_financiere, name='analyse_financiere'),
# ]
