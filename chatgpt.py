import csv
from django.conf import settings
from django.db import models, transaction
from django.core.exceptions import ImproperlyConfigured

# Django settings
settings.configure(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'your_database_name',
            'USER': 'your_username',
            'PASSWORD': 'your_password',
            'HOST': 'your_host',
            'PORT': 'your_port',
        }
    }
)

# Django model
class Disk(models.Model):
    name = models.CharField(max_length=100)
    size = models.IntegerField()

    def __str__(self):
        return self.name

# Insert data into the database from CSV
def insert_data_from_csv(file_path):
    with open(file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip the header row
        with transaction.atomic():
            for row in csv_reader:
                name = row[0]
                size = int(row[1])
                Disk.objects.create(name=name, size=size)

# Main function
def main():
    file_path = input("Enter the path to the CSV file: ")
    insert_data_from_csv(file_path)

if __name__ == '__main__':
    main()
