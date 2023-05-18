from django.db import models

# myapp/models.py

from django.db import models

class Disk(models.Model):
    name = models.CharField(max_length=100)
    size = models.IntegerField()

    def __str__(self):
        return self.name
