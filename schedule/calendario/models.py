from django.db import models

# Create your models here.
from django.db import models

class CalendarEvent(models.Model):
    title = models.CharField(max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):
        return self.title