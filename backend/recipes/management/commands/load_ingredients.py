import csv
import os

from recipes.models import Ingredient
from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand
from django.shortcuts import get_object_or_404


MODELS_FIELDS = {}
#DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')

class Command(BaseCommand):
    help = 'Creating model objects according the file path specified'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help="file path")
        parser.add_argument('--model_name', type=str, help="model name")
        parser.add_argument('--app_name', type=str,
                            help="django app name that the model is connected to")
        #parser.add_argument('filename', default='ingredients.csv',
                            #nargs='?', type=str)

    def handle(self, *args, **options):
        file_path = options['path']
        #model = Ingredient
        model = apps.get_model(options['app_name'], options['model_name'])
        with open(file_path, 'rt', encoding='utf-8') as csv_file:
        #with open(os.path.join(DATA_ROOT, options['filename']), 'rt', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file, delimiter=',')
            for row in reader:
                for field, value in row.items():
                    if field in MODELS_FIELDS.keys():
                        row[field] = get_object_or_404(
                            MODELS_FIELDS[field], pk=value
                        )
                for a,b in row.items():
                    print(a, b)
                    c = input()
                model.objects.create(**row)