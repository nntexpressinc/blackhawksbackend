from django.db import models
import logging

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from .dispatcher import Dispatcher
from apps.auth.models import User
from .customerbroker import CustomerBroker
from .driver import Driver
from .truck import Truck
from .truck import Unit
from .team import Team
# from .stops import Stops
# from apps.load.models.stops import Stops
import requests
class LoadTags(models.Model):
    TAG_CHOICES = [
        ('HAZ', 'Haz'),
        ('DEDICATED LANE', 'Dedicated Lane'),
        ('HOT LOAD', 'Hot Load'),
        ('ISSUE', 'Issue'),
    ]

    tag = models.CharField(max_length=50, choices=TAG_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.tag


class Load(models.Model):
    TAGS_CHOICES = [
        ('HAZ', 'Haz'),
        ('DEDICATED-LINE', 'Dedicated-Line'),

    ]

    EQUIPMENT_TYPE_CHOICES = [
        ('DRYVAN', 'Dryvan'),
        ('REEFER', 'Reefer'),
        ('CARHAUL', 'Carhaul'),
        ('FLATBED', 'Flatbed'),
        ('STEPDECK', 'Stepdeck'),
        ('POWERONLY', 'PowerOnly'),
        ('RGN', 'Rgn'),
        ('TANKERSTYLE', 'TankerStyle'),
    ]

    LOAD_STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('COVERED', 'Covered'),
        ('DISPATCHED', 'Dispatched'),
        ('LOADING', 'Loading'),
        ('ON_ROUTE', 'On Route'),
        ('UNLOADING', 'Unloading'),
        ('IN_YARD', 'In Yard'),
        ('DELIVERED', 'Delivered'),
        ('COMPLETED', 'Completed'),
        ('CANCELED', 'Canceled'),
        )
    INVOICE_STATUS_CHOICES = (
        ('NOT_DETERMINED', 'Not Determined'),
        ('INVOICED', 'Invoiced'),
        ('PAID', 'Paid'),
        ('UNPAID', 'Unpaid'),
    )
    company_name = models.CharField(max_length=200, blank=True, null=True)
    reference_id = models.CharField(max_length=200, blank=True, null=True)
    instructions = models.CharField(max_length=200, blank=True, null=True)
    bills = models.IntegerField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='dispatcher', on_delete=models.CASCADE, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    load_id = models.CharField(max_length=200, blank=True, null=True)
    trip_id = models.IntegerField(blank=True, null=True)
    customer_broker = models.ForeignKey(CustomerBroker, related_name='customer_broker', on_delete=models.CASCADE, blank=True, null=True)
    driver = models.ForeignKey(Driver, related_name='driver', on_delete=models.CASCADE, blank=True, null=True)
    co_driver = models.CharField(max_length=100, null=True, blank=True)
    truck = models.ForeignKey(Truck, related_name='truck', on_delete=models.CASCADE, blank=True, null=True)
    dispatcher = models.ForeignKey(Dispatcher, related_name='created_by', on_delete=models.CASCADE, blank=True, null=True)
    load_status = models.CharField(max_length=50, choices=LOAD_STATUS_CHOICES, blank=True, null=True)
    tags = models.ForeignKey(LoadTags, related_name='loadtags', on_delete=models.CASCADE, blank=True, null=True)
    equipment_type = models.CharField(max_length=50, choices=EQUIPMENT_TYPE_CHOICES, blank=True, null=True)
    trip_status = models.CharField(max_length=50, blank=True, null=True)
    invoice_status = models.CharField(max_length=50, blank=True, null=True, default='Unpaid')
    trip_bil_status = models.CharField(max_length=50, blank=True, null=True)
    load_pay = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    driver_pay = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_pay = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    per_mile = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    mile = models.IntegerField(blank=True, null=True)
    empty_mile = models.IntegerField(blank=True, null=True)
    total_miles = models.IntegerField(blank=True, null=True)
    flagged = models.BooleanField(default=False, blank=True, null=True)
    flagged_reason = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    chat = models.TextField(blank=True, null=True)
    ai = models.BooleanField(blank=True, null=True) 
    rate_con = models.FileField(blank=True, null=True)
    bol = models.FileField(blank=True, null=True)
    pod = models.FileField(blank=True, null=True)
    document = models.FileField(blank=True, null=True)
    comercial_invoice = models.FileField(blank=True, null=True)
    message_id = models.CharField(max_length=255, null=True, blank=True)
    pickup_date = models.DateTimeField(blank=True, null=True)
    delivery_date = models.DateTimeField(blank=True, null=True)
    pickup_location = models.CharField(max_length=200, blank=True, null=True)
    delivery_location = models.CharField(max_length=200, blank=True, null=True)
    driver_location = models.CharField(max_length=200, blank=True, null=True)
    stop = models.ManyToManyField('Stops', related_name='related_loads', blank=True, null=True)
    group_message_id = models.CharField(max_length=50, null=True, blank=True)
    unit_id = models.ForeignKey(Unit, related_name='unit_load', on_delete=models.CASCADE, blank=True, null=True)
    team_id = models.ForeignKey(Team, related_name='team_load', on_delete=models.CASCADE, blank=True, null=True)
    amazon_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    weekly_number = models.CharField(max_length=100, blank=True, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    pictures = models.FileField(upload_to='load_pictures/', blank=True, null=True)