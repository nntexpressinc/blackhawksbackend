from django.db import models

from apps.load.models.driver import Driver
class FuelTaxRate(models.Model):
    quarter = models.CharField(max_length=10, choices=[
        ('Quarter 1', 'Quarter 1'),
        ('Quarter 2', 'Quarter 2'),
        ('Quarter 3', 'Quarter 3'),
        ('Quarter 4', 'Quarter 4'),
    ], default='Quarter 1')
    state = models.CharField(max_length=15, choices=[
        ('AL', 'Alabama'),
        ('AK', 'Alaska'),
        ('AZ', 'Arizona'),
        ('AR', 'Arkansas'),
        ('CA', 'California'),
        ('CO', 'Colorado'), 
        ('CT', 'Connecticut'),
        ('DE', 'Delaware'),
        ('FL', 'Florida'),
        ('GA', 'Georgia'),
        ('HI', 'Hawaii'),
        ('ID', 'Idaho'),
        ('IL', 'Illinois'),
        ('IN', 'Indiana'),
        ('IA', 'Iowa'),
        ('KS', 'Kansas'),
        ('KY', 'Kentucky'),
        ('KY Surcharge', 'Kentucky Surcharge'),
        ('LA', 'Louisiana'),
        ('ME', 'Maine'),
        ('MD', 'Maryland'),
        ('MA', 'Massachusetts'),
        ('MI', 'Michigan'),
        ('MN', 'Minnesota'),
        ('MS', 'Mississippi'),
        ('MO', 'Missouri'),
        ('MT', 'Montana'),
        ('NE', 'Nebraska'),
        ('NV', 'Nevada'),
        ('NH', 'New Hampshire'),
        ('NJ', 'New Jersey'),
        ('NM', 'New Mexico'),
        ('NY', 'New York'),
        ('NC', 'North Carolina'),
        ('ND', 'North Dakota'),
        ('OH', 'Ohio'),
        ('OK', 'Oklahoma'),
        ('OR', 'Oregon'),
        ('PA', 'Pennsylvania'),
        ('RI', 'Rhode Island'),
        ('SC', 'South Carolina'),
        ('SD', 'South Dakota'),
        ('TN', 'Tennessee'),
        ('TX', 'Texas'),
        ('UT', 'Utah'),
        ('VT', 'Vermont'),
        ('VA', 'Virginia'),
        ('WA', 'Washington'),
        ('WV', 'West Virginia'),
        ('WI', 'Wisconsin'),
        ('WY', 'Wyoming'), 
    ])
    rate = models.DecimalField(max_digits=5, decimal_places=3)  # Masalan, 0.285
    mpg = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)  # Masalan, 0.285
    year = models.IntegerField(null=True, blank=True)  # Yilni saqlash uchun
    class Meta:
        unique_together = ('quarter', 'state')  # Har bir quarter va state uchun faqat bitta rate bo'lsin

    def __str__(self):
        return f"{self.quarter} - {self.state} - {self.rate}"
    


class Ifta(models.Model):
    fuel_tax_rate = models.ForeignKey(FuelTaxRate, on_delete=models.CASCADE)
    quarter = models.CharField(max_length=10, choices=[
        ('Quarter 1', 'Quarter 1'),
        ('Quarter 2', 'Quarter 2'),
        ('Quarter 3', 'Quarter 3'),
        ('Quarter 4', 'Quarter 4'),
    ])
    state = models.CharField(max_length=20)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    total_miles = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    taxible_gallon = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tax_paid_gallon = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    net_taxible_gallon = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    tax = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    invoice_number = models.CharField(max_length=100, null=True, blank=True)
    weekly_number = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('quarter', 'state', 'driver', 'weekly_number')
    
    def __str__(self):
        return f"{self.driver.user.email} - {self.quarter} - {self.state} - Week {self.weekly_number}"