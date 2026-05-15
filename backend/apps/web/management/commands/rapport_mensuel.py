"""
management/commands/rapport_mensuel.py
Génère le rapport mensuel automatique BSG.

Usage :
  python manage.py rapport_mensuel          # mois courant
  python manage.py rapport_mensuel --mois 2024-03

Planification sur Render (render.yaml) :
  - type: cron
    name: rapport-mensuel
    schedule: "0 7 1 * *"     # Le 1er de chaque mois à 7h
    buildCommand: pip install -r requirements.txt
    startCommand: python manage.py rapport_mensuel
"""
import os
import logging
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.db.models import Sum, Count, Q
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Génère et envoie le rapport mensuel BSG par email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mois',
            help='Mois au format YYYY-MM (défaut: mois précédent)',
            default=None,
        )
        parser.add_argument(
            '--email',
            help='Email destinataire (défaut: admins BSG)',
            default=None,
        )
        parser.add_argument(
            '--no-email',
            action='store_true',
            help='Générer sans envoyer par email (sauvegarde locale)',
        )

    def handle(self, *args, **options):
        # ── Déterminer la période ─────────────────────────────────────────
        mois_str = options.get('mois')
        if mois_str:
            try:
                annee, mois = map(int, mois_str.split('-'))
            except ValueError:
                self.stderr.write(f'Format invalide : {mois_str}. Utiliser YYYY-MM')
                return
        else:
            today = date.today()
            # Mois précédent par défaut
            premier_ce_mois = today.replace(day=1)
            fin_mois_prec   = premier_ce_mois - timedelta(days=1)
            annee, mois     = fin_mois_prec.year, fin_mois_prec.month

        debut = date(annee, mois, 1)
        if mois == 12:
            fin = date(annee + 1, 1, 1) - timedelta(days=1)
        else:
            fin = date(annee, mois + 1, 1) - timedelta(days=1)

        self.stdout.write(f'📊 Génération rapport : {debut} → {fin}')

        # ── Collecter les données ─────────────────────────────────────────
        ctx = self._collecter_donnees(debut, fin)
        ctx['debut'] = debut
        ctx['fin']   = fin
        ctx['mois_label'] = debut.strftime('%B %Y')

        # ── Générer le HTML ───────────────────────────────────────────────
        html = render_to_string('web/rapports/rapport_mensuel_email.html', ctx)

        # ── Sauvegarder en local ──────────────────────────────────────────
        os.makedirs('rapports', exist_ok=True)
        nom_fichier = f'rapports/BSG_Rapport_{annee}_{mois:02d}.html'
        with open(nom_fichier, 'w', encoding='utf-8') as f:
            f.write(html)
        self.stdout.write(f'✅ Rapport sauvegardé : {nom_fichier}')

        # ── Générer PDF si WeasyPrint disponible ──────────────────────────
        pdf_path = None
        try:
            from weasyprint import HTML
            pdf_path = nom_fichier.replace('.html', '.pdf')
            HTML(string=html).write_pdf(pdf_path)
            self.stdout.write(f'✅ PDF généré : {pdf_path}')
        except ImportError:
            self.stdout.write(self.style.WARNING('⚠ WeasyPrint non installé — pas de PDF'))

        # ── Envoyer par email ──────────────────────────────────────────────
        if not options.get('no_email'):
            self._envoyer_email(html, pdf_path, ctx, options.get('email'), annee, mois)

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Rapport mensuel {debut.strftime("%B %Y")} terminé.'
        ))

    def _collecter_donnees(self, debut, fin):
        from finances.models import JournalFinancier, Depense
        from commandes.models import Commande, LigneCommande
        from clients.models import Client
        from produits.models import Produit

        def jnl_sum(flux, op=None):
            qs = JournalFinancier.objects.filter(
                created_at__date__gte=debut,
                created_at__date__lte=fin,
                type_flux=flux
            )
            if op:
                qs = qs.filter(type_operation=op)
            return float(qs.aggregate(t=Sum('montant_gnf'))['t'] or 0)

        entrees  = jnl_sum('ENTREE')
        sorties  = jnl_sum('SORTIE')
        profit   = entrees - sorties

        # Top 5 produits
        top_produits = list(
            LigneCommande.objects.filter(
                commande__date_creation__date__gte=debut,
                commande__date_creation__date__lte=fin,
                commande__statut__in=['VALIDEE', 'LIVREE'],
            ).values('produit__nom').annotate(
                total_qte=Sum('quantite'),
                total_ca=Sum('sous_total')
            ).order_by('-total_qte')[:5]
        )

        # Top 5 clients
        top_clients = list(
            Commande.objects.filter(
                date_creation__date__gte=debut,
                date_creation__date__lte=fin,
                statut__in=['VALIDEE', 'LIVREE'],
                client__isnull=False
            ).values('client__nom').annotate(
                nb_commandes=Count('id'),
                total_ca=Sum('total_ttc')
            ).order_by('-total_ca')[:5]
        )

        # Dépenses par catégorie
        dep_par_cat = list(
            Depense.objects.filter(
                date_depense__date__gte=debut,
                date_depense__date__lte=fin,
            ).values('categorie__nom').annotate(
                total=Sum('montant_gnf')
            ).order_by('-total')[:6]
        )

        nb_commandes = Commande.objects.filter(
            date_creation__date__gte=debut,
            date_creation__date__lte=fin,
        ).count()

        nb_clients_actifs = Client.objects.filter(actif=True).count()
        nb_alertes_stock  = Produit.objects.filter(est_en_alerte=True, actif=True).count()

        return {
            'entrees':          entrees,
            'sorties':          sorties,
            'profit':           profit,
            'nb_commandes':     nb_commandes,
            'top_produits':     top_produits,
            'top_clients':      top_clients,
            'dep_par_cat':      dep_par_cat,
            'nb_clients':       nb_clients_actifs,
            'nb_alertes_stock': nb_alertes_stock,
            'dep_entreprise':   float(Depense.objects.filter(
                date_depense__date__gte=debut,
                date_depense__date__lte=fin,
                type_depense='ENTREPRISE'
            ).aggregate(t=Sum('montant_gnf'))['t'] or 0),
            'dep_personnel': float(Depense.objects.filter(
                date_depense__date__gte=debut,
                date_depense__date__lte=fin,
                type_depense='PERSONNEL'
            ).aggregate(t=Sum('montant_gnf'))['t'] or 0),
        }

    def _envoyer_email(self, html, pdf_path, ctx, email_dest, annee, mois):
        from auth_users.models import Utilisateur
        if email_dest:
            destinataires = [email_dest]
        else:
            destinataires = list(
                Utilisateur.objects.filter(role='ADMIN', actif=True)
                .values_list('email', flat=True)
            )

        if not destinataires:
            self.stdout.write(self.style.WARNING('⚠ Aucun destinataire trouvé'))
            return

        try:
            email = EmailMessage(
                subject=f'[BSG] Rapport mensuel — {ctx["mois_label"]}',
                body=html,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bsg.com'),
                to=destinataires,
            )
            email.content_subtype = 'html'

            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    email.attach(
                        f'BSG_Rapport_{annee}_{mois:02d}.pdf',
                        f.read(),
                        'application/pdf'
                    )

            email.send()
            self.stdout.write(f'✅ Email envoyé à : {", ".join(destinataires)}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Email échoué : {e}'))
