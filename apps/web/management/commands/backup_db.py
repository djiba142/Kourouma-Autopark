"""
management/commands/backup_db.py

Commande Django : python manage.py backup_db

Exporte toutes les données dans un fichier JSON horodaté.
À planifier avec un cron Render ou une tâche scheduler.

Usage :
  python manage.py backup_db              # export JSON
  python manage.py backup_db --dest /tmp  # dossier cible
"""
import os
import json
import gzip
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core import serializers
from django.apps import apps


class Command(BaseCommand):
    help = 'Exporte toute la base de données BSG en JSON compressé'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dest',
            default='backups',
            help='Dossier de destination (défaut: backups/)',
        )

    def handle(self, *args, **options):
        dest = options['dest']
        os.makedirs(dest, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename  = os.path.join(dest, f'bsg_backup_{timestamp}.json.gz')

        # Modèles à exclure (sessions, logs Django internes)
        exclude_apps = {'sessions', 'admin', 'contenttypes', 'auth'}

        all_data = []
        total    = 0

        for model in apps.get_models():
            app_label = model._meta.app_label
            if app_label in exclude_apps:
                continue
            try:
                qs   = model.objects.all()
                data = json.loads(serializers.serialize('json', qs))
                all_data.extend(data)
                nb = len(data)
                total += nb
                if nb > 0:
                    self.stdout.write(f'  ✓ {app_label}.{model.__name__} — {nb} enregistrement(s)')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ {model.__name__} ignoré : {e}')
                )

        # Écriture compressée
        with gzip.open(filename, 'wt', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

        size_kb = os.path.getsize(filename) // 1024
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Backup terminé : {filename}\n'
                f'   {total} objets exportés — {size_kb} KB compressé'
            )
        )
