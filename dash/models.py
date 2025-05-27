from django.db import models

# Create your models here.
class Country(models.Model):
    iso_code = models.CharField(max_length=3, unique=True)  # e.g. 'US', 'VN'
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Indicator(models.Model):
    code = models.CharField(max_length=50, unique=True)  # e.g. 'gdp', 'inflation'
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, blank=True)  # e.g. '%', 'USD', 'points'
    frequency = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ])

    def __str__(self):
        return self.name

class EconomicData(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE)
    date = models.DateField()
    value = models.DecimalField(max_digits=20, decimal_places=4)

    class Meta:
        unique_together = ('country', 'indicator', 'date')
        ordering = ['-date']

    def __str__(self):
        return f'{self.country} - {self.indicator} @ {self.date}: {self.value}'
