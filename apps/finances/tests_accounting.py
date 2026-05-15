from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from finances.models import CompteComptable, JournalFinancier, EcritureComptable, Depense, CategorieDepense
from commandes.models import Commande, Paiement
from clients.models import Client
from produits.models import Produit
from stock.models import Localisation

User = get_user_model()

class AccountingSystemTest(TestCase):
    def setUp(self):
        # The loaddata from migrate/fixture might not be available in transactional test DB 
        # unless we use TransactionTestCase or loaddata explicitly here.
        # But signals need the accounts, so let's create them.
        self.caisse = CompteComptable.objects.create(code='101', nom='Caisse', type='ACTIF')
        self.clients = CompteComptable.objects.create(code='401', nom='Clients', type='ACTIF')
        self.ventes = CompteComptable.objects.create(code='701', nom='Ventes', type='PRODUIT')
        self.charges = CompteComptable.objects.create(code='602', nom='Charges', type='CHARGE')
        
        self.user = User.objects.create_user(email="compta@test.com", nom="Compta", password="pass")
        self.client_mouctar = Client.objects.create(nom="Mouctar")
        self.cat = CategorieDepense.objects.create(nom="Loyer")

    def test_journalisation_depense(self):
        """Une dépense doit créer une entrée journal et 2 écritures (Débit 602 / Crédit 101)"""
        dep = Depense.objects.create(
            montant=150000,
            description="Loyer Bureau",
            categorie=self.cat,
            cree_par=self.user
        )
        
        # Check Journal
        journal = JournalFinancier.objects.get(type_operation='DEPENSE', reference_doc=dep.numero)
        self.assertEqual(journal.montant_gnf, 150000)
        self.assertEqual(journal.type_flux, 'SORTIE')
        
        # Check Ledger
        ecritures = journal.ecritures.all()
        self.assertEqual(ecritures.count(), 2)
        
        debit = ecritures.get(compte__code='602')
        self.assertEqual(debit.debit, 150000)
        self.assertEqual(debit.credit, 0)
        
        credit = ecritures.get(compte__code='101')
        self.assertEqual(credit.debit, 0)
        self.assertEqual(credit.credit, 150000)

    def test_journalisation_paiement(self):
        """Un paiement doit créer une entrée journal (Débit 101 / Crédit 401)"""
        cmd = Commande.objects.create(numero="CMD-001", client=self.client_mouctar, total_ttc=500000)
        pay = Paiement.objects.create(
            commande=cmd,
            montant=200000,
            mode_paiement='CASH',
            enregistre_par=self.user
        )
        
        journal = JournalFinancier.objects.get(type_operation='PAIEMENT', reference_doc=pay.numero)
        self.assertEqual(journal.type_flux, 'ENTREE')
        
        ecritures = journal.ecritures.all()
        self.assertEqual(ecritures.get(compte__code='101').debit, 200000)
        self.assertEqual(ecritures.get(compte__code='401').credit, 200000)

    def test_journalisation_vente_sur_validation(self):
        """Une commande VALIDEE doit créer une entrée journal VENTE (Débit 401 / Crédit 701)"""
        cmd = Commande.objects.create(
            numero="CMD-VENTE-01", 
            client=self.client_mouctar, 
            total_ttc=800000,
            cree_par=self.user
        )
        
        # Normalement pas encore de journal
        self.assertFalse(JournalFinancier.objects.filter(reference_doc=cmd.numero).exists())
        
        # Validation
        cmd.statut = 'VALIDEE'
        cmd.save()
        
        journal = JournalFinancier.objects.get(type_operation='VENTE', reference_doc=cmd.numero)
        self.assertEqual(journal.montant_gnf, 800000)
        
        ecritures = journal.ecritures.all()
        self.assertEqual(ecritures.get(compte__code='401').debit, 800000)
        self.assertEqual(ecritures.get(compte__code='701').credit, 800000)

    def test_journal_immutability(self):
        """On ne peut pas modifier une entrée du journal existante"""
        jrn = JournalFinancier.objects.create(
            type_operation='AJUSTEMENT',
            reference_doc='REF',
            description='Test',
            montant=100,
            montant_gnf=100,
            type_flux='ENTREE',
            utilisateur=self.user
        )
        
        jrn.description = "Modifié"
        with self.assertRaises(ValidationError):
            jrn.save()

    def test_paiement_numero_sequentiel(self):
        """Les paiements doivent avoir des numéros séquentiels PAY-YYYYMM-XXXX"""
        cmd = Commande.objects.create(numero="CMD-SEQ", client=self.client_mouctar, total_ttc=1000)
        p1 = Paiement.objects.create(commande=cmd, montant=10, enregistre_par=self.user)
        p2 = Paiement.objects.create(commande=cmd, montant=10, enregistre_par=self.user)
        
        self.assertTrue(p1.numero.startswith('PAY-'))
        self.assertNotEqual(p1.numero, p2.numero)
        
        num1 = int(p1.numero.split('-')[-1])
        num2 = int(p2.numero.split('-')[-1])
        self.assertEqual(num2, num1 + 1)
