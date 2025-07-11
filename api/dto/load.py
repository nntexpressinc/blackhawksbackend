from rest_framework import serializers
from api.dto.auth import CustomUserSerializer
from api.dto.auth import CustomUserSerializer
from apps.load.models.driver import Pay, DriverPay, DriverExpense
from apps.load.models.truck import Unit
from apps.load.models.team import Team

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = "__all__"
        
from apps.auth.models import User
from apps.load.models import (
    Load, LoadTags, Driver, DriverTags, Trailer, 
    TrailerTags, TruckTags, Truck, Dispatcher,
    DispatcherTags, EmployeeTags, CustomerBroker, 
    Stops, Employee, OtherPay, Commodities)


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = "__all__"


class DriverExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverExpense
        fields = "__all__"
class DriverPaySerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverPay
        fields = "__all__"
        
    
    


class PaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pay
        fields = "__all__"

class DispatcherLoadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dispatcher
        fields = ['id', 'nickname']

class CustomerBrokerLoadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerBroker
        fields = ['id', 'company_name']

# class DriverLoadSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Driver
#         fields = ['id', 'first_name', 'last_name']

class LoadSerializer(serializers.ModelSerializer):
    # ForeignKey maydonlarni faqat ID sifatida qabul qilish uchun
    # created_by = serializers.PrimaryKeyRelatedField(queryset=Dispatcher.objects.all(), required=False, allow_null=True)
    customer_broker = serializers.PrimaryKeyRelatedField(queryset=CustomerBroker.objects.all(), required=False, allow_null=True)
    driver = serializers.PrimaryKeyRelatedField(queryset=Driver.objects.all(), required=False, allow_null=True)
    dispatcher = serializers.PrimaryKeyRelatedField(queryset=Dispatcher.objects.all(), required=False, allow_null=True)
    truck = serializers.PrimaryKeyRelatedField(queryset=Truck.objects.all(), required=False, allow_null=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=LoadTags.objects.all(), required=False, allow_null=True)
    stop = serializers.PrimaryKeyRelatedField(many=True, queryset=Stops.objects.all(), required=False, allow_null=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Load
        fields = "__all__"
        read_only_fields = ['created_by', 'created_date', 'updated_date']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['created_by'] = CustomUserSerializer(instance.created_by).data if instance.created_by else None
        representation['customer_broker'] = CustomerBrokerSerializer(instance.customer_broker).data if instance.customer_broker else None
        representation['driver'] = DriverSerializer(instance.driver).data if instance.driver else None
        representation['dispatcher'] = DispatcherSerializer(instance.dispatcher).data if instance.dispatcher else None
        representation['truck'] = TruckSerializer(instance.truck).data if instance.truck else None
        representation['tags'] = LoadTagsSerializer(instance.tags).data if instance.tags else None
        representation['stop'] = StopsSerializer(instance.stop.all(), many=True).data if instance.stop.exists() else None
        return representation

class DriverSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    class Meta:
        model = Driver
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = CustomUserSerializer(instance.user).data if instance.user else None
        return representation
class TrailerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trailer
        fields = "__all__"

class TrailerTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrailerTags
        fields = "__all__"

class DriverTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverTags
        fields = "__all__"

class TruckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Truck
        fields = "__all__"

class TruckTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TruckTags
        fields = "__all__"

class DispatcherSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    class Meta:
        model = Dispatcher
        fields = "__all__"
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = CustomUserSerializer(instance.user).data if instance.user else None
        return representation

class DispatcherTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DispatcherTags
        fields = "__all__"

class EmployeeSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    class Meta:
        model = Employee
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = CustomUserSerializer(instance.user).data if instance.user else None
        return representation

class EmployeeTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeTags
        fields = "__all__"

class CustomerBrokerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerBroker
        fields = "__all__"
    
class LoadTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoadTags
        fields = "__all__"

class StopsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stops
        fields = "__all__"

class OtherPaySerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherPay
        fields = "__all__"

class CommoditiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commodities
        fields = "__all__"

from apps.load.models.ifta import FuelTaxRate, Ifta 
        
class FuelTaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelTaxRate
        fields = '__all__'


class BulkFuelTaxRateSerializer(serializers.Serializer):
    quarter = serializers.CharField()
    rates = serializers.ListField(
        child=serializers.DictField()
    )
    
    def validate_rates(self, value):
        """Validate that each rate entry has the correct structure"""
        for rate_data in value:
            for state, rate_info in rate_data.items():
                if not isinstance(rate_info, dict):
                    raise serializers.ValidationError(f"Rate info for {state} must be a dictionary")
                
                if 'rate' not in rate_info:
                    raise serializers.ValidationError(f"Rate is required for {state}")
                
                try:
                    float(rate_info['rate'])
                except (ValueError, TypeError):
                    raise serializers.ValidationError(f"Rate for {state} must be a valid number")
                
                if 'mpg' in rate_info and rate_info['mpg'] is not None:
                    try:
                        float(rate_info['mpg'])
                    except (ValueError, TypeError):
                        raise serializers.ValidationError(f"MPG for {state} must be a valid number")
        
        return value
    
    def create(self, validated_data):
        quarter = validated_data['quarter']
        rates_data = validated_data['rates']
        
        created_rates = []
        for rate_data in rates_data:
            for state, rate_info in rate_data.items():
                fuel_tax_rate, created = FuelTaxRate.objects.update_or_create(
                    quarter=quarter,
                    state=state,
                    defaults={
                        'rate': rate_info.get('rate', 0),
                        'mpg': rate_info.get('mpg', None)
                    }
                )
                created_rates.append(fuel_tax_rate)
        
        return created_rates



from apps.load.models.ifta import Ifta, FuelTaxRate


class IftaSerializer(serializers.ModelSerializer):
    fuel_tax_rate = FuelTaxRateSerializer(read_only=True)
    driver_name = serializers.CharField(source='driver.name', read_only=True)
    
    class Meta:
        model = Ifta
        fields = '__all__'
        read_only_fields = ('fuel_tax_rate', 'taxible_gallon', 'net_taxible_gallon', 'tax')


class BulkIftaSerializer(serializers.Serializer):
    quarter = serializers.CharField()
    weekly_number = serializers.IntegerField()
    driver = serializers.PrimaryKeyRelatedField(queryset=Driver.objects.all())
    ifta_records = serializers.ListField(
        child=serializers.DictField()
    )
    
    def create(self, validated_data):
        quarter = validated_data['quarter']
        weekly_number = validated_data['weekly_number']
        driver = validated_data['driver']
        ifta_records_data = validated_data['ifta_records']
        
        created_records = []
        for record_data in ifta_records_data:
            ifta_record = Ifta.objects.create(
                quarter=quarter,
                state=record_data['state'],
                driver=driver,
                total_miles=record_data['total_miles'],
                tax_paid_gallon=record_data.get('tax_paid_gallon'),
                invoice_number=record_data.get('invoice_number'),
                weekly_number=weekly_number
            )
            created_records.append(ifta_record)
        
        return created_records

