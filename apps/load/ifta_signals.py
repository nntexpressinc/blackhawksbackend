from decimal import Decimal
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from apps.load.models.ifta import FuelTaxRate, Ifta
from apps.load.models.driver import Driver


@receiver(pre_save, sender=Ifta)
def calculate_ifta_values(sender, instance, **kwargs):
    try:
        # Get the FuelTaxRate record
        fuel_tax_rate = FuelTaxRate.objects.get(
            quarter=instance.quarter,
            state=instance.state
        )
        
        # Set the fuel_tax_rate foreign key
        instance.fuel_tax_rate = fuel_tax_rate
        
        # Calculate taxible_gallon
        if instance.total_miles:
            if fuel_tax_rate.mpg and fuel_tax_rate.mpg > 0:
                # Convert total_miles to Decimal for consistent calculation
                total_miles_decimal = Decimal(str(instance.total_miles))
                instance.taxible_gallon = total_miles_decimal / fuel_tax_rate.mpg
            else:
                instance.taxible_gallon = Decimal('0.000')
        else:
            instance.taxible_gallon = Decimal('0.000')
        
        # Calculate net_taxible_gallon
        if instance.tax_paid_gallon:
            tax_paid_gallon = Decimal(str(instance.tax_paid_gallon))
            instance.net_taxible_gallon = instance.taxible_gallon - tax_paid_gallon
        else:
            instance.net_taxible_gallon = instance.taxible_gallon
        
        # Calculate tax
        instance.tax = instance.net_taxible_gallon * fuel_tax_rate.rate
        
    except FuelTaxRate.DoesNotExist:
        raise ValueError(f"FuelTaxRate not found for quarter {instance.quarter} and state {instance.state}")