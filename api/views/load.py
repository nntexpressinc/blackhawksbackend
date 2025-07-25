from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework import permissions
from datetime import datetime
from django.db.models import Sum, Q, Min, Max
from decimal import Decimal
from rest_framework.pagination import PageNumberPagination
from django.core.files.base import ContentFile

from apps.load.models.ifta import Ifta, FuelTaxRate
from apps.load.models.driver import Pay, DriverPay, DriverExpense
from apps.load.models.truck import Unit
from apps.load.models.team import Team
from api.dto.load import TeamSerializer
from apps.auth.models import Company
from apps.load.models import (
    Load, LoadTags, Driver, DriverTags, Trailer, 
    TrailerTags, TruckTags, Truck, Dispatcher,
    DispatcherTags, EmployeeTags, CustomerBroker, 
    Stops, Employee, OtherPay, Commodities)

from api.dto.load import (
    LoadSerializer, DriverSerializer, 
    DriverTagsSerializer, TrailerSerializer, 
    TrailerTagsSerializer, TruckSerializer, 
    TruckTagsSerializer, DispatcherSerializer, 
    DispatcherTagsSerializer, EmployeeSerializer, 
    EmployeeTagsSerializer, CustomerBrokerSerializer, 
    LoadTagsSerializer, StopsSerializer, OtherPaySerializer, 
    CommoditiesSerializer, PaySerializer, DriverPaySerializer, 
    DriverExpenseSerializer,  UnitSerializer, FuelTaxRateSerializer, BulkFuelTaxRateSerializer,
    IftaSerializer, BulkIftaSerializer)


class CustomPagination(PageNumberPagination):
    page_size = 25
    def get_paginated_response(self, data):
        # Create a standard paginated response
        response = Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })
        
        # Replace the hostname in the pagination links
        if response.data['next']:
            response.data['next'] = response.data['next'].replace('https://0.0.0.0:8000', 'https://api1.biznes-armiya.uz')
        if response.data['previous']:
            response.data['previous'] = response.data['previous'].replace('https://0.0.0.0:8000', 'https://api1.biznes-armiya.uz')
            
        return response




class TeamListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        teams = Team.objects.all()
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TeamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class TeamDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Team.objects.all()
    serializer_class = TeamSerializer

class UnitListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        units = Unit.objects.all()
        serializer = UnitSerializer(units, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UnitSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UnitDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer


class DriverExpenseListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        driver_expenses = DriverExpense.objects.all()
        serializer = DriverExpenseSerializer(driver_expenses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = DriverExpenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class DriverExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DriverExpense.objects.all()
    serializer_class = DriverExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

class DriverPayListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        driver_pays = DriverPay.objects.all()
        serializer = DriverPaySerializer(driver_pays, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = DriverPaySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class DriverPayDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = DriverPay.objects.all()
    serializer_class = DriverPaySerializer


class PayListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        pays = Pay.objects.all()
        serializer = PaySerializer(pays, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PaySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PayDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Pay.objects.all()
    serializer_class = PaySerializer
    

class LoadListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        loads = Load.objects.all()
        serializer = LoadSerializer(loads, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = LoadSerializer(data=request.data, context={'request': request})  # request ni context sifatida uzatamiz
        if serializer.is_valid():
            # created_by ga request.user ni qo‘shamiz
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoadDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Load.objects.all()
    serializer_class = LoadSerializer



class DriverListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    # pagination_class = CustomPagination

    # def get(self, request):
    #     drivers = Driver.objects.all()
    #     paginator = self.pagination_class()
    #     page = paginator.paginate_queryset(drivers, request)
    #     serializer = DriverSerializer(page, many=True)
    #     return paginator.get_paginated_response(serializer.data)
    
    # def post(self, request):
    #     serializer = DriverSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request):
        drivers = Driver.objects.all()
        serializer = DriverSerializer(drivers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request):
        serializer = DriverSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DriverDetailView(generics.RetrieveUpdateDestroyAPIView):

    permission_classes = [permissions.IsAuthenticated]
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer


class DriverTagsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        driver_tags = DriverTags.objects.all()
        serializer = DriverTagsSerializer(driver_tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = DriverTagsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class DriverTagsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = DriverTags.objects.all()
    serializer_class = DriverTagsSerializer

class TrailerListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        trailers = Trailer.objects.all()
        serializer = TrailerSerializer(trailers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = TrailerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class TrailerDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Trailer.objects.all()
    serializer_class = TrailerSerializer

class TrailerTagsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        trailer_tags = TrailerTags.objects.all()
        serializer = TrailerTagsSerializer(trailer_tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = TrailerTagsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class TrailerTagsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = TrailerTags.objects.all()
    serializer_class = TrailerTagsSerializer

class TruckListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        trucks = Truck.objects.all()
        serializer = TruckSerializer(trucks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = TruckSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class TruckDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Truck.objects.all()
    serializer_class = TruckSerializer

class TruckTagsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        truck_tags = TruckTags.objects.all()
        serializer = TruckTagsSerializer(truck_tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = TruckTagsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class TruckTagsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = TruckTags.objects.all()
    serializer_class = TruckTagsSerializer

class DispatcherListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        dispatchers = Dispatcher.objects.all()
        serializer = DispatcherSerializer(dispatchers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = DispatcherSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class DispatcherDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Dispatcher.objects.all()
    serializer_class = DispatcherSerializer

class DispatcherTagsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        dispatcher_tags = DispatcherTags.objects.all()
        serializer = DispatcherTagsSerializer(dispatcher_tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = DispatcherTagsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class DispatcherTagsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = DispatcherTags.objects.all()
    serializer_class = DispatcherTagsSerializer

class EmployeeListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        employees = Employee.objects.all()
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = EmployeeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

class EmployeeTagsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        employee_tags = EmployeeTags.objects.all()
        serializer = EmployeeTagsSerializer(employee_tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = EmployeeTagsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class EmployeeTagsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = EmployeeTags.objects.all()
    serializer_class = EmployeeTagsSerializer
    
class CustomerBrokerListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        custom_brokers = CustomerBroker.objects.all()
        serializer = CustomerBrokerSerializer(custom_brokers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = CustomerBrokerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CustomerBrokerDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = CustomerBroker.objects.all()
    serializer_class = CustomerBrokerSerializer

class CommoditiesListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        commodities = Commodities.objects.all()
        serializer = CommoditiesSerializer(commodities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = CommoditiesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CommoditiesDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Commodities.objects.all()
    serializer_class = CommoditiesSerializer

class OtherPayListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        other_pays = OtherPay.objects.all()
        serializer = OtherPaySerializer(other_pays, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = OtherPaySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class OtherPayDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = OtherPay.objects.all()
    serializer_class = OtherPaySerializer

class StopsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        stops = Stops.objects.all()
        serializer = StopsSerializer(stops, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = StopsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class StopsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Stops.objects.all()
    serializer_class = StopsSerializer

class LoadTagsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        load_tags = LoadTags.objects.all()
        serializer = LoadTagsSerializer(load_tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = LoadTagsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoadTagsDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = LoadTags.objects.all()
    serializer_class = LoadTagsSerializer



from datetime import datetime
from apps.auth.models import Company


class DriverPayCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # POST so'rovdan ma'lumotlarni olish
        pay_from = request.data.get('pay_from')
        pay_to = request.data.get('pay_to')
        driver_id = request.data.get('driver')
        notes = request.data.get('notes', '')
        invoice_number = request.data.get('invoice_number')
        weekly_number = request.data.get('weekly_number')
        load_driver_pay_ids = request.data.get('load_driver_pay', [])
        load_company_driver_pay_ids = request.data.get('load_company_driver_pay', [])

        # Sana formatini tekshirish va konvertatsiya qilish
        try:
            pay_from_date = datetime.strptime(pay_from, '%Y-%m-%d').date()
            pay_to_date = datetime.strptime(pay_to, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Driver obyektini olish
        try:
            driver = Driver.objects.get(id=driver_id)
        except Driver.DoesNotExist:
            return Response({"error": "Driver not found."}, status=status.HTTP_404_NOT_FOUND)

        # Driverga bog'langan Pay obyektini olish
        try:
            pay = Pay.objects.filter(driver=driver).latest('id')
        except Pay.DoesNotExist:
            return Response({"error": "No Pay found for this driver."}, status=status.HTTP_404_NOT_FOUND)

        # DriverPay obyektini boshlang'ich saqlash
        driver_pay = DriverPay(
            driver=driver,
            pay=pay,
            pay_from=pay_from_date,
            pay_to=pay_to_date,
            amount=0.0,
            notes=notes,
            invoice_number=invoice_number,
            weekly_number=weekly_number,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        driver_pay.save()
        
        # Asosiy filterlangan loadlar
        loads_with_dates = Load.objects.filter(
            driver=driver,
            stop__appointmentdate__isnull=False,
            invoice_status='Paid'
        ).annotate(
            calculated_pickup_date=Min('stop__appointmentdate', filter=Q(stop__stop_name='PICKUP')),
            calculated_delivery_date=Max('stop__appointmentdate', filter=Q(stop__stop_name='DELIVERY'))
        ).filter(
            calculated_pickup_date__isnull=False,
            calculated_delivery_date__isnull=False
        )

        # Filter loads based on overlap with pay period
        filtered_loads = loads_with_dates.filter(
            Q(calculated_pickup_date__date__gte=pay_from_date, calculated_pickup_date__date__lte=pay_to_date) |
            Q(calculated_delivery_date__date__gte=pay_from_date, calculated_delivery_date__date__lte=pay_to_date) |
            Q(calculated_pickup_date__date__lte=pay_from_date, calculated_delivery_date__date__gte=pay_to_date)
        ).distinct()

        # 1. load_driver_pay_ids dan qo'shimcha loadlarni qo'shish
        if load_driver_pay_ids:
            # Qo'shimcha loadlarni alohida olish
            additional_driver_loads = Load.objects.filter(
                id__in=load_driver_pay_ids,
                driver=driver,
                invoice_status='Paid'
            ).annotate(
                calculated_pickup_date=Min('stop__appointmentdate', filter=Q(stop__stop_name='PICKUP')),
                calculated_delivery_date=Max('stop__appointmentdate', filter=Q(stop__stop_name='DELIVERY'))
            )
            
            # Barcha load ID'larni birlashtirish
            all_load_ids = set(filtered_loads.values_list('id', flat=True))
            additional_load_ids = set(additional_driver_loads.values_list('id', flat=True))
            combined_load_ids = all_load_ids.union(additional_load_ids)
            
            # Birlashtirilgan ID'lar bilan yangi queryset yaratish
            filtered_loads = Load.objects.filter(
                id__in=combined_load_ids,
                driver=driver,
                invoice_status='Paid'
            ).annotate(
                calculated_pickup_date=Min('stop__appointmentdate', filter=Q(stop__stop_name='PICKUP')),
                calculated_delivery_date=Max('stop__appointmentdate', filter=Q(stop__stop_name='DELIVERY'))
            ).distinct()

        # ManyToMany fieldlarni saqlash
        if load_driver_pay_ids:
            driver_pay.load_driver_pay.set(load_driver_pay_ids)
        if load_company_driver_pay_ids:
            driver_pay.load_company_driver_pay.set(load_company_driver_pay_ids)

        # Hisoblash va natijani tayyorlash
        total_pay = 0.0
        total_load_pays = 0.0
        total_other_pays = 0.0
        load_details = []
        chargebag_deductions = []
        total_loads_formula = []
        total_other_pays_formula = []
        total_chargebag_amount = 0.0

        for load in filtered_loads:
            load_payment = 0.0
            load_formula = []
            if load.load_pay and pay.standart:
                load_payment = float(load.load_pay) * (float(pay.standart) / 100)
                total_load_pays += load_payment
                load_formula.append(f"${load.load_pay:.2f} * {pay.standart}%")

            load_total_pay = float(load.total_pay) if load.total_pay else 0.0

            other_pays = OtherPay.objects.filter(load=load)
            load_chargebag_amount = 0.0
            other_pay_details = []

            for other_pay in other_pays:
                if other_pay.amount:
                    amount = float(other_pay.amount)
                    
                    if other_pay.pay_type in ['DETENTION', 'LAYOVER']:
                        amount_with_percentage = amount * (float(pay.standart) / 100) if pay.standart else amount
                        load_payment += amount_with_percentage
                        total_other_pays += amount_with_percentage
                        total_other_pays_formula.append(f"${amount:.2f} * {pay.standart}%")
                        other_pay_info = {
                            "pay_type": other_pay.pay_type,
                            "formula": f"${amount:.2f} * {pay.standart}%",
                            "result": f"${amount_with_percentage:.2f}",
                            "note": other_pay.note if other_pay.note else ''
                        }
                    elif other_pay.pay_type == 'CHARGEBACK':
                        load_chargebag_amount += amount
                        total_chargebag_amount += amount
                        load_payment -= amount
                        chargebag_deductions.append({
                            "load_id": load.load_id,
                            "amount": f"${amount:.2f}",
                            "note": other_pay.note if other_pay.note else '',
                            "pay_type": other_pay.pay_type
                        })
                        other_pay_info = {
                            "pay_type": other_pay.pay_type,
                            "formula": f"-${amount:.2f}",
                            "result": f"-${amount:.2f}",
                            "note": other_pay.note if other_pay.note else ''
                        }
                    elif other_pay.pay_type in ['EQUIPMENT', 'LUMPER', 'DRIVERASSIST', 'TRAILERWASH', 'ESCORTFEE', 'BONUS', 'OTHER']:
                        load_payment += amount
                        total_other_pays += amount
                        total_other_pays_formula.append(f"${amount:.2f}")
                        other_pay_info = {
                            "pay_type": other_pay.pay_type,
                            "formula": f"${amount:.2f}",
                            "result": f"${amount:.2f}",
                            "note": other_pay.note if other_pay.note else ''
                        }
                    else:
                        load_payment += amount
                        total_other_pays += amount
                        total_other_pays_formula.append(f"${amount:.2f}")
                        other_pay_info = {
                            "pay_type": other_pay.pay_type,
                            "formula": f"${amount:.2f}",
                            "result": f"${amount:.2f}",
                            "note": other_pay.note if other_pay.note else ''
                        }

                    other_pay_details.append(other_pay_info)

            # Get actual pickup and delivery information from stops
            pickup_stop = None
            delivery_stop = None
            
            for stop in load.stop.all():
                if stop.stop_name == 'PICKUP':
                    pickup_stop = stop
                elif stop.stop_name == 'DELIVERY':
                    delivery_stop = stop
            
            pickup_info = "N/A"
            delivery_info = "N/A"
            
            if pickup_stop and pickup_stop.appointmentdate:
                pickup_location = f"{pickup_stop.city}, {pickup_stop.state}" if pickup_stop.city else pickup_stop.address1
                pickup_info = f"{pickup_stop.appointmentdate.strftime('%Y-%m-%d')}, {pickup_location}"
            
            if delivery_stop and delivery_stop.appointmentdate:
                delivery_location = f"{delivery_stop.city}, {delivery_stop.state}" if delivery_stop.city else delivery_stop.address1
                delivery_info = f"{delivery_stop.appointmentdate.strftime('%Y-%m-%d')}, {delivery_location}"

            load_info = {
                "Load #": load.load_id,
                "Pickup": pickup_info,
                "Delivery": delivery_info,
                "Formula": " + ".join(load_formula) if load_formula else "N/A",
                "Result": f"${load_payment:.2f}",
                "Notes": load.note if load.note else '',
                "Chargebag Deduction": f"${load_chargebag_amount:.2f}" if load_chargebag_amount > 0 else None,
                "Other Payments": other_pay_details if other_pay_details else None
            }
            load_details.append(load_info)
            if load_formula:
                total_loads_formula.append(f"({load_info['Formula']} = ${load_payment:.2f})")

        escrow_weekly = driver.escrow_deposit if driver.escrow_deposit else 0

        # Fix 2: Update the driver's cost field by adding the escrow amount
        if escrow_weekly > 0:
            driver.cost = (driver.cost or 0) + escrow_weekly
            driver.save()

        # UPDATED: Filter expenses by date range and update invoice_number, weekly_number
        expenses = DriverExpense.objects.filter(
            driver=driver,
            expense_date__gte=pay_from_date,
            expense_date__lte=pay_to_date
        )

        # NEW: Update the filtered expenses with invoice_number and weekly_number
        if invoice_number or weekly_number:
            update_fields = {}
            if invoice_number:
                update_fields['invoice_number'] = invoice_number
                update_fields['invoice_status'] = 'Invoiced'
            if weekly_number:
                update_fields['weekly_number'] = weekly_number
            
            if update_fields:
                expenses.update(**update_fields)

        # NEW: Update the filtered loads with invoice_number and weekly_number
        if invoice_number or weekly_number:
            load_update_fields = {}
            if invoice_number:
                load_update_fields['invoice_number'] = invoice_number
                load_update_fields['invoice_status'] = 'Invoiced'
            if weekly_number:
                load_update_fields['weekly_number'] = weekly_number
            
            if load_update_fields:
                filtered_loads.update(**load_update_fields)

        # NEW: IFTA tax calculation
        total_ifta_tax = 0.0
        ifta_details = []
        
        if weekly_number:
            # Filter IFTA records by driver and weekly_number
            ifta_records = Ifta.objects.filter(
                driver=driver,
                weekly_number=weekly_number
            )
            
            # Update invoice_number in IFTA records if provided
            if invoice_number:
                ifta_records.update(invoice_number=invoice_number)
            
            # Calculate total IFTA tax
            for ifta in ifta_records:
                if ifta.tax:
                    tax_amount = float(ifta.tax)
                    total_ifta_tax += tax_amount
                    ifta_details.append({
                        "state": ifta.state,
                        "quarter": ifta.quarter,
                        "tax_amount": f"${tax_amount:.2f}",
                        "total_miles": float(ifta.total_miles) if ifta.total_miles else 0,
                        "taxible_gallon": float(ifta.taxible_gallon) if ifta.taxible_gallon else 0,
                        "tax_paid_gallon": float(ifta.tax_paid_gallon) if ifta.tax_paid_gallon else 0,
                        "net_taxible_gallon": float(ifta.net_taxible_gallon) if ifta.net_taxible_gallon else 0
                    })

        total_expenses = 0.0
        total_income = 0.0
        expense_details = []
        income_formula = []
        expenses_formula = []

        for expense in expenses:
            amount = float(expense.amount)
            if expense.transaction_type == '+':
                total_income += amount
                income_formula.append(f"${amount:.2f}")
            elif expense.transaction_type == '-':
                total_expenses += amount
                expenses_formula.append(f"${amount:.2f}")

            expense_details.append({
                "Description": expense.description,
                "Formula": f"{'+' if expense.transaction_type == '+' else '-'}${amount:.2f}",
                "Result": f"${amount:.2f}",
                "Type": "Income" if expense.transaction_type == '+' else "Expense",
                "Date": expense.expense_date.strftime('%Y-%m-%d') if expense.expense_date else 'N/A'
            })

        # UPDATED: Calculate final total_pay correctly with IFTA tax deduction
        print(f"DEBUG: total_load_pays = {total_load_pays}")
        print(f"DEBUG: total_other_pays = {total_other_pays}")
        print(f"DEBUG: total_chargebag_amount = {total_chargebag_amount}")
        print(f"DEBUG: escrow_weekly = {escrow_weekly}")
        print(f"DEBUG: total_expenses = {total_expenses}")
        print(f"DEBUG: total_income = {total_income}")
        print(f"DEBUG: total_ifta_tax = {total_ifta_tax}")
        
        total_pay = total_load_pays + total_other_pays - escrow_weekly - total_expenses + total_income - total_chargebag_amount - total_ifta_tax

        print(f"DEBUG: calculated total_pay = {total_pay}")
        total_pay = max(total_pay, 0)

        # Prepare total_pay formula
        total_pay_formula = []
        if total_load_pays > 0:
            total_pay_formula.append(f"Load Pays: ${total_load_pays:.2f}")
        if total_other_pays > 0:
            total_pay_formula.append(f"Other Pays: ${total_other_pays:.2f}")
        if total_chargebag_amount > 0:
            total_pay_formula.append(f"Chargeback: -${total_chargebag_amount:.2f}")
        if escrow_weekly > 0:
            total_pay_formula.append(f"Escrow: -${escrow_weekly:.2f}")
        if total_income > 0:
            total_pay_formula.append(f"Income: ${total_income:.2f}")
        if total_expenses > 0:
            total_pay_formula.append(f"Expenses: -${total_expenses:.2f}")
        if total_ifta_tax > 0:
            total_pay_formula.append(f"IFTA: -${total_ifta_tax:.2f}")

        driver_pay.loads = load_details
        driver_pay.amount = total_pay
        driver_pay.save()

        # Driver ma'lumotlari
        driver_info = {
            "first_name": driver.user.first_name if driver.user else None,
            "last_name": driver.user.last_name if driver.user else None,
            "contact_number": driver.user.telephone if driver.user else None,
            "address1": driver.user.address if driver.user else None,
            "generate_date": driver_pay.created_at.strftime('%Y-%m-%d %H:%M:%S') if driver_pay.created_at else None,
            "report_date": driver_pay.updated_at.strftime('%Y-%m-%d %H:%M:%S') if driver_pay.updated_at else None,
            "search_from": driver_pay.pay_from.strftime('%Y-%m-%d') if driver_pay.pay_from else None,
            "search_to": driver_pay.pay_to.strftime('%Y-%m-%d') if driver_pay.pay_to else None,
            "company_name": driver.user.company_name if driver.user else None,
            "invoice_number": driver_pay.invoice_number,
            "weekly_number": driver_pay.weekly_number,
        }

        # UPDATED: Get company information from Company model
        try:
            company = Company.objects.first()
            company_info = {
                "company_name": company.company_name if company else None,
                "phone": company.phone if company else None,
                "fax": company.fax if company else None,
                "state": company.state if company else None,
                "city": company.city if company else None,
                "zip": company.zip if company else None,
                "company_logo": company.company_logo.url if company and company.company_logo else None,
            }
        except Company.DoesNotExist:
            company_info = {
                "company_name": None,
                "phone": None,
                "fax": None,
                "state": None,
                "city": None,
                "zip": None,
                "company_logo": None,
            }

        # Yakuniy javob
        response_data = {
            "driver": driver_info,
            "company_info": company_info,
            "loads": load_details,
            "total_load_pays": {
                "Formula": " + ".join(total_loads_formula) if total_loads_formula else "N/A",
                "Result": f"${total_load_pays:.2f}"
            },
            "total_other_pays": {
                "Formula": " + ".join(total_other_pays_formula) if total_other_pays_formula else "N/A",
                "Result": f"${total_other_pays:.2f}"
            },
            "escrow_deduction": {
                "Formula": f"-${escrow_weekly:.2f}" if escrow_weekly else "N/A",
                "Result": f"${escrow_weekly:.2f}"
            },
            "chargeback_deductions": chargebag_deductions,
            "expenses": expense_details,
            "total_expenses": {
                "Formula": " + ".join(expenses_formula) if expenses_formula else "N/A",
                "Result": f"${total_expenses:.2f}"
            },
            "total_income": {
                "Formula": " + ".join(income_formula) if income_formula else "N/A",
                "Result": f"${total_income:.2f}"
            },
            "ifta_deduction": {
                "Formula": f"-${total_ifta_tax:.2f}" if total_ifta_tax > 0 else "N/A",
                "Result": f"${total_ifta_tax:.2f}",
                "Details": ifta_details
            },
            "total_pay": {
                "Formula": " + ".join(total_pay_formula) if total_pay_formula else "N/A",
                "Result": f"${total_pay:.2f}"
            }
        }

        # Company Driver uchun qo'shimcha hisob-kitob
        if driver.driver_type == 'COMPANY_DRIVER':
            # 2. Company Driver uchun load_company_driver_pay_ids dan qo'shimcha loadlarni qo'shish
            company_driver_loads = filtered_loads  # Asosiy filterlangan loadlar
            
            if load_company_driver_pay_ids:
                # Company Driver uchun qo'shimcha loadlarni alohida olish
                additional_company_loads = Load.objects.filter(
                    id__in=load_company_driver_pay_ids,
                    driver=driver,
                    invoice_status='Paid'
                ).annotate(
                    calculated_pickup_date=Min('stop__appointmentdate', filter=Q(stop__stop_name='PICKUP')),
                    calculated_delivery_date=Max('stop__appointmentdate', filter=Q(stop__stop_name='DELIVERY'))
                )
                
                # Company Driver uchun barcha load ID'larni birlashtirish
                company_load_ids = set(filtered_loads.values_list('id', flat=True))
                additional_company_load_ids = set(additional_company_loads.values_list('id', flat=True))
                combined_company_load_ids = company_load_ids.union(additional_company_load_ids)
                
                # Company Driver uchun yangi queryset yaratish
                company_driver_loads = Load.objects.filter(
                    id__in=combined_company_load_ids,
                    driver=driver,
                    invoice_status='Paid'
                ).annotate(
                    calculated_pickup_date=Min('stop__appointmentdate', filter=Q(stop__stop_name='PICKUP')),
                    calculated_delivery_date=Max('stop__appointmentdate', filter=Q(stop__stop_name='DELIVERY'))
                ).distinct()
            
            # Company Driver uchun miles va pay hisoblash
            cd_loads_data = []
            total_miles = 0
            
            for load in company_driver_loads:
                # Get loaded miles from load.mile field
                loaded_miles = load.mile if load.mile else 0
                total_miles += loaded_miles
                
                # Get pickup and delivery locations
                pickup_location = "N/A"
                delivery_location = "N/A"
                
                for stop in load.stop.all():
                    if stop.stop_name == 'PICKUP':
                        pickup_location = f"{stop.city}, {stop.state}" if stop.city else stop.address1
                    elif stop.stop_name == 'DELIVERY':
                        delivery_location = f"{stop.city}, {stop.state}" if stop.city else stop.address1
                
                cd_loads_data.append({
                    'load_number': load.load_id,
                    'load_id': load.load_id,
                    'loaded_miles': loaded_miles,
                    'pickup_location': pickup_location,
                    'delivery_location': delivery_location,
                    'trip': f"{pickup_location} - {delivery_location}"
                })
            
            # Calculate company driver pay (total miles * $0.65)
            miles_rate = 0.65
            company_driver_pay = total_miles * miles_rate
            
            # Save company driver data to DriverPay model
            driver_pay.total_miles = total_miles
            driver_pay.miles_rate = miles_rate
            driver_pay.company_driver_pay = company_driver_pay
            driver_pay.company_driver_data = {
                'loads': cd_loads_data,
                'total_miles': total_miles,
                'miles_rate': miles_rate,
                'total_pay': company_driver_pay,
                'calculation_summary': {
                    'formula': f"{total_miles} miles × ${miles_rate} = ${company_driver_pay:.2f}",
                    'loads_count': len(cd_loads_data)
                }
            }
            driver_pay.save()
            
            # Add company driver data to response
            response_data['company_driver_data'] = {
                'total_miles': total_miles,
                'miles_rate': f"${miles_rate}",
                'company_driver_pay': f"${company_driver_pay:.2f}",
                'loads_detail': cd_loads_data,
                'calculation_summary': {
                    'formula': f"{total_miles} miles × ${miles_rate} = ${company_driver_pay:.2f}",
                    'loads_count': len(cd_loads_data)
                }
            }

        return Response(response_data, status=status.HTTP_201_CREATED)
    


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from collections import defaultdict



class FuelTaxRateViewSet(viewsets.ModelViewSet):
    queryset = FuelTaxRate.objects.all()
    serializer_class = FuelTaxRateSerializer
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Create multiple fuel tax rates for all states in a single request
        Expected format:
        {
            "quarter": "Quarter 1",
            "rates": [
                {
                    "AL": {"rate": 0.285, "mpg": 7.5},
                    "AK": {"rate": 0.195, "mpg": 8.0}
                }
            ]
        }
        """
        serializer = BulkFuelTaxRateSerializer(data=request.data)
        if serializer.is_valid():
            created_rates = serializer.save()
            return Response(
                FuelTaxRateSerializer(created_rates, many=True).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_quarter(self, request):
        """
        Get all fuel tax rates grouped by quarter
        """
        quarter = request.query_params.get('quarter')
        if quarter:
            rates = FuelTaxRate.objects.filter(quarter=quarter)
        else:
            rates = FuelTaxRate.objects.all()
        
        grouped_data = defaultdict(list)
        for rate in rates:
            grouped_data[rate.quarter].append(FuelTaxRateSerializer(rate).data)
        
        return Response(dict(grouped_data))
    
    @action(detail=False, methods=['put'])
    def bulk_update(self, request):
        """
        Update multiple fuel tax rates for a quarter
        """
        quarter = request.data.get('quarter')
        rates_data = request.data.get('rates', [])
        
        updated_rates = []
        for rate_data in rates_data:
            for state, rate_info in rate_data.items():
                try:
                    fuel_tax_rate = FuelTaxRate.objects.get(quarter=quarter, state=state)
                    fuel_tax_rate.rate = rate_info.get('rate', fuel_tax_rate.rate)
                    fuel_tax_rate.mpg = rate_info.get('mpg', fuel_tax_rate.mpg)
                    fuel_tax_rate.save()
                    updated_rates.append(fuel_tax_rate)
                except FuelTaxRate.DoesNotExist:
                    continue
        
        return Response(
            FuelTaxRateSerializer(updated_rates, many=True).data,
            status=status.HTTP_200_OK
        )


class IftaViewSet(viewsets.ModelViewSet):
    queryset = Ifta.objects.all()
    serializer_class = IftaSerializer
    
    def get_queryset(self):
        queryset = Ifta.objects.select_related('fuel_tax_rate', 'driver').all()
        quarter = self.request.query_params.get('quarter')
        driver = self.request.query_params.get('driver')
        weekly_number = self.request.query_params.get('weekly_number')
        
        if quarter:
            queryset = queryset.filter(quarter=quarter)
        if driver:
            queryset = queryset.filter(driver=driver)
        if weekly_number:
            queryset = queryset.filter(weekly_number=weekly_number)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Create multiple IFTA records for all states in a single request
        Expected format:
        {
            "quarter": "Quarter 1",
            "weekly_number": 1,
            "driver": 1,
            "ifta_records": [
                {
                    "state": "AL",
                    "total_miles": 1000,
                    "tax_paid_gallon": 50,
                    "invoice_number": "INV-001"
                }
            ]
        }
        """
        serializer = BulkIftaSerializer(data=request.data)
        if serializer.is_valid():
            created_records = serializer.save()
            return Response(
                IftaSerializer(created_records, many=True).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_quarter_and_driver(self, request):
        """
        Get IFTA records grouped by quarter and driver
        """
        quarter = request.query_params.get('quarter')
        driver_id = request.query_params.get('driver')
        weekly_number = request.query_params.get('weekly_number')
        
        filters = Q()
        if quarter:
            filters &= Q(quarter=quarter)
        if driver_id:
            filters &= Q(driver_id=driver_id)
        if weekly_number:
            filters &= Q(weekly_number=weekly_number)
        
        records = Ifta.objects.filter(filters).select_related('fuel_tax_rate', 'driver')
        
        grouped_data = defaultdict(lambda: defaultdict(list))
        for record in records:
            grouped_data[record.quarter][record.driver.name].append(
                IftaSerializer(record).data
            )
        
        return Response(dict(grouped_data))
    
    @action(detail=False, methods=['put'])
    def bulk_update(self, request):
        """
        Update multiple IFTA records
        """
        quarter = request.data.get('quarter')
        driver_id = request.data.get('driver')
        weekly_number = request.data.get('weekly_number')
        ifta_records_data = request.data.get('ifta_records', [])
        
        updated_records = []
        for record_data in ifta_records_data:
            try:
                ifta_record = Ifta.objects.get(
                    quarter=quarter,
                    state=record_data['state'],
                    driver_id=driver_id,
                    weekly_number=weekly_number
                )
                
                # Update fields
                ifta_record.total_miles = record_data.get('total_miles', ifta_record.total_miles)
                ifta_record.tax_paid_gallon = record_data.get('tax_paid_gallon', ifta_record.tax_paid_gallon)
                ifta_record.invoice_number = record_data.get('invoice_number', ifta_record.invoice_number)
                
                ifta_record.save()  # This will trigger the signal for recalculation
                updated_records.append(ifta_record)
                
            except Ifta.DoesNotExist:
                continue
        
        return Response(
            IftaSerializer(updated_records, many=True).data,
            status=status.HTTP_200_OK
        )


# your_app/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import os

from apps.load.models.ifta import IFTAReport
from api.dto.load import (
    IFTAReportSerializer, 
    IFTAReportCreateSerializer, 
    IFTAReportListSerializer
)
from apps.load.services import process_ifta_report


class IFTAReportListCreateView(generics.ListCreateAPIView):
    """List all IFTA reports and create new ones"""
    queryset = IFTAReport.objects.all().order_by('-id')
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return IFTAReportCreateSerializer
        return IFTAReportListSerializer
    
    def create(self, request, *args, **kwargs):
        """Create IFTA report and process files"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save the instance
        instance = serializer.save()
        
        try:
            # Process the files
            success = process_ifta_report(instance)
            
            if success:
                # Return the processed report
                response_serializer = IFTAReportSerializer(instance, context={'request': request})
                return Response(
                    {
                        'message': 'IFTA Report processed successfully',
                        'data': response_serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
            else:
                # Delete the instance if processing failed
                instance.delete()
                return Response(
                    {'error': 'Failed to process IFTA report files'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            # Delete the instance if processing failed
            instance.delete()
            return Response(
                {'error': f'Error processing files: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class IFTAReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific IFTA report"""
    queryset = IFTAReport.objects.all()
    serializer_class = IFTAReportSerializer
    parser_classes = [MultiPartParser, FormParser]


class IFTAReportDownloadView(APIView):
    """Download the result Excel file"""
    
    def get(self, request, pk):
        report = get_object_or_404(IFTAReport, pk=pk)
        
        if not report.result_file:
            return Response(
                {'error': 'Result file not available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Serve the file
        file_path = report.result_file.path
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                return response
        else:
            return Response(
                {'error': 'Result file not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class IFTAReportReprocessView(APIView):
    """Reprocess the IFTA report"""
    
    def post(self, request, pk):
        report = get_object_or_404(IFTAReport, pk=pk)
        
        try:
            # Clear existing result file
            if report.result_file:
                report.result_file.delete()
            
            # Reprocess
            success = process_ifta_report(report)
            
            if success:
                serializer = IFTAReportSerializer(report, context={'request': request})
                return Response(
                    {
                        'message': 'IFTA Report reprocessed successfully',
                        'data': serializer.data
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Failed to reprocess IFTA report'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': f'Error reprocessing files: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.load.models.load import Load
from apps.load.models.customerbroker import CustomerBroker
from apps.load.models.stops import Stops
from api.dto.load import LoadSerializer
from datetime import datetime
from django.utils.dateparse import parse_datetime
import openai
import fitz  # PyMuPDF
import json



class RateConUploadView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Read PDF text
        pdf_text = self._extract_text_from_pdf(file)
        if not pdf_text:
            return Response({"error": "Unable to read PDF."}, status=status.HTTP_400_BAD_REQUEST)

        # Ask AI to extract order data
        try:
            ai_data = self._ask_ai_for_data(pdf_text)
            order_data = json.loads(ai_data)
        except Exception as e:
            return Response({"error": "AI processing failed", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Create Load and Stops
        load = self._create_load_and_stops(order_data, request.user)

        return Response({"message": "Load and stops created successfully", "load_id": load.id}, status=status.HTTP_201_CREATED)

    def _extract_text_from_pdf(self, file):
        text = ""
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text

    import os
    from dotenv import load_dotenv

    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    def _ask_ai_for_data(self, text):
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a logistics assistant that extracts structured JSON data from shipping rate confirmation documents."},
                {"role": "user", "content": f"Extract the following fields from the text: freight_bill, equipment, rate, pickup_address, pickup_date, pickup_note, delivery_address, delivery_date, delivery_note, total_miles. Respond only with valid JSON.\n\n{text}"}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content

    
    def _create_load_and_stops(self, data, user):
        load = Load.objects.create(
            reference_id=data.get('freight_bill'),
            equipment_type='DRYVAN',  # Optionally map
            load_pay=data.get('rate'),
            total_miles=data.get('total_miles'),
            created_by=user,
            pickup_location=data.get('pickup_address'),
            delivery_location=data.get('delivery_address'),
            pickup_date=parse_datetime(data.get('pickup_date')),
            delivery_date=parse_datetime(data.get('delivery_date')),
            ai=True
        )

        if data.get('pickup_address'):
            Stops.objects.create(
                load=load,
                stop_name='PICKUP',
                location=data['pickup_address'],
                appointmentdate=parse_datetime(data.get('pickup_date')),
                note=data.get('pickup_note')
            )

        if data.get('delivery_address'):
            Stops.objects.create(
                load=load,
                stop_name='DELIVERY',
                location=data['delivery_address'],
                appointmentdate=parse_datetime(data.get('delivery_date')),
                note=data.get('delivery_note')
            )

        return load