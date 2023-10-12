import csv

from django.core.management import BaseCommand, CommandError

from recipes.models import Ingredient

MODELS_FIELDS = {}


class Command(BaseCommand):
    help = 'Creating model objects according the file path specified'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, help="file path")

    def handle(self, *args, **options):
        file_path = options['path']
        try:
            with open(file_path, 'r', encoding='utf-8') as csv_file:
                reader = csv.reader(csv_file)
                for row in reader:
                    name, measurement_unit = row
                    Ingredient.objects.get_or_create(
                        name=name, measurement_unit=measurement_unit)
                self.stdout.write(
                    self.style.SUCCESS('Ингредиенты загружены')
                )
        except FileNotFoundError:
            raise CommandError('Добавьте файл')
