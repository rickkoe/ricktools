from django.shortcuts import render

# myapp/views.py

from django.shortcuts import render
from myapp.models import Disk
import csv
from django.db import models
from django.shortcuts import render

def import_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        reader = csv.reader(csv_file.read().decode('utf-8').splitlines())
        header = next(reader)  # Get the header row

        # Create a dynamically generated model
        model_fields = {}
        for column_name in header:
            field_name = column_name.lower().replace(' ', '_')
            model_fields[field_name] = models.CharField(max_length=100)

        # Create the model class dynamically
        dynamic_model = type('DynamicModel', (models.Model,), model_fields)
        dynamic_model._meta.db_table = 'myapp_dynamicmodel'
        dynamic_model.objects = models.Manager()

        # Set the module attribute to avoid the '__module__' KeyError
        dynamic_model.__module__ = __name__

        # Import the data into the dynamic model
        for row in reader:
            kwargs = {field_name: value for field_name, value in zip(model_fields.keys(), row)}
            dynamic_model.objects.create(**kwargs)

        return render(request, 'success.html')

    return render(request, 'import.html')
