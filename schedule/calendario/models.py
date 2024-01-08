from django.db import models

# Create your models here.
class Formula(models.Model):
    campo_1 = models.CharField(max_length=255)
    campo_2 = models.CharField(max_length=255, null=True, blank=True)
    operador = models.CharField(max_length=10, null=True, blank=True)
    sinal = models.CharField(max_length=10, null=True, blank=True)
    valor = models.FloatField(null=True)