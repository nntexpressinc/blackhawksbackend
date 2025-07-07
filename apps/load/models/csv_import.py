from django.db import models
from django.core.exceptions import ValidationError
import pandas as pd
import logging
from datetime import datetime
from django.db import transaction
from apps.load.models.load import Load
from apps.load.models.stops import Stops

logger = logging.getLogger(__name__)

class GoogleSheetsImport(models.Model):
    csv_file = models.FileField(upload_to='imports/', help_text="Google Sheets dan yuklab olingan CSV fayl")
    start_row = models.IntegerField(default=2, help_text="Boshlanish qatori (2 - header dan keyin)")
    end_row = models.IntegerField(blank=True, null=True, help_text="Tugash qatori (bo'sh bo'lsa oxirigacha)")
    imported_at = models.DateTimeField(auto_now_add=True)
    total_records = models.IntegerField(default=0)
    success_records = models.IntegerField(default=0)
    failed_records = models.IntegerField(default=0)
    error_log = models.TextField(blank=True, null=True)
    is_processed = models.BooleanField(default=False)
    
    # Dispatcher mapping
    DISPATCHER_MAPPING = {
        'Uktam': 1,
        'Muhammadali': 2,
        'Alibek': 3,
        'Bayramali': 4,
        'Jasur': 5,
        'Kamron': 6,
    }
    
    # Unit mapping
    UNIT_MAPPING = {
        '100': 1,
        '103': 2,
        '104': 3,
        '105': 4,
    }
    
    # Driver mapping
    DRIVER_MAPPING = {
        'Omid Barakzai': 1,
        'Jalaluddin Sharifi': 2,
        'Muhibullah Altintash': 3,
        'Muhammad Asif': 4,
    }
    
    def clean(self):
        if self.start_row < 1:
            raise ValidationError("Boshlanish qatori 1 dan kichik bo'lishi mumkin emas")
        if self.end_row and self.end_row < self.start_row:
            raise ValidationError("Tugash qatori boshlanish qatoridan kichik bo'lishi mumkin emas")
    
    def process_csv(self):
        """CSV faylni qayta ishlab Load va Stops modellarini yaratish"""
        if not self.csv_file:
            raise ValidationError("CSV fayl yuklanmagan")
        
        try:
            # CSV faylni o'qish
            df = pd.read_csv(self.csv_file.path, encoding='utf-8')
            
            # Qatorlarni cheklash
            start_idx = self.start_row - 1  # pandas 0-indexli
            end_idx = self.end_row - 1 if self.end_row else len(df)
            
            df_slice = df.iloc[start_idx:end_idx + 1]
            
            self.total_records = len(df_slice)
            success_count = 0
            error_messages = []
            
            with transaction.atomic():
                for index, row in df_slice.iterrows():
                    try:
                        # Load yaratish
                        load_data = self._extract_load_data(row)
                        
                        # Load data mavjudligini tekshirish
                        if not load_data:
                            error_msg = f"Qator {index + 1}: Load ma'lumotlari bo'sh"
                            error_messages.append(error_msg)
                            logger.warning(error_msg)
                            continue
                        
                        load = Load.objects.create(**load_data)

                        # Stops yaratish
                        stops_data = self._extract_stops_data(row, load)
                        stops_instances = []

                        for stop_data in stops_data:
                            # Faqat dict va bo'sh bo'lmagan dict uchun create chaqiramiz
                            if isinstance(stop_data, dict) and stop_data:
                                stop = Stops.objects.create(**stop_data)
                                stops_instances.append(stop)

                        # Load ga stops larni bog'lash
                        if stops_instances:
                            load.stop.set(stops_instances)

                        success_count += 1
                        logger.info(f"Load {load.load_id} muvaffaqiyatli yaratildi")

                    except Exception as e:
                        error_msg = f"Qator {index + 1}: {str(e)}"
                        error_messages.append(error_msg)
                        logger.error(error_msg)
                        continue
            
            # Natijalarni saqlash
            self.success_records = success_count
            self.failed_records = self.total_records - success_count
            self.error_log = '\n'.join(error_messages) if error_messages else None
            self.is_processed = True
            self.save()
            
            return True
            
        except Exception as e:
            self.error_log = f"Umumiy xatolik: {str(e)}"
            self.is_processed = True
            self.save()
            logger.error(f"CSV import xatoligi: {str(e)}")
            return False
    
    def _extract_load_data(self, row):
        """Qatordan Load uchun ma'lumotlarni ajratib olish"""
        from .dispatcher import Dispatcher
        from .driver import Driver
        from .truck import Unit
        from .customerbroker import CustomerBroker
        from apps.auth.models import User
        
        load_data = {}
        
        # Majburiy maydonlar tekshiruvi
        blackhawks_load = row.get('Blackhawks load number')
        if not pd.notna(blackhawks_load) or not str(blackhawks_load).strip():
            logger.warning(f"Blackhawks load number bo'sh yoki noto'g'ri: {blackhawks_load}")
            return None
        
        # Blackhawks load number -> load_id
        load_data['load_id'] = str(blackhawks_load).strip()
        
        # Dispatch name -> dispatcher
        dispatch_name = row.get('Dispatch name', '').strip()
        if dispatch_name and dispatch_name in self.DISPATCHER_MAPPING:
            try:
                dispatcher_obj = Dispatcher.objects.get(id=self.DISPATCHER_MAPPING[dispatch_name])
                load_data['dispatcher'] = dispatcher_obj
            except Dispatcher.DoesNotExist:
                logger.warning(f"Dispatcher ID {self.DISPATCHER_MAPPING[dispatch_name]} topilmadi")
        
        # Unit № -> unit_id
        unit_num = str(row.get('Unit №', '')).strip()
        if unit_num and unit_num in self.UNIT_MAPPING:
            try:
                unit_obj = Unit.objects.get(id=self.UNIT_MAPPING[unit_num])
                load_data['unit_id'] = unit_obj
            except Unit.DoesNotExist:
                logger.warning(f"Unit ID {self.UNIT_MAPPING[unit_num]} topilmadi")
        
        # Driver -> driver
        driver_name = row.get('Assiged trailer Driver', '').strip()
        if driver_name and driver_name in self.DRIVER_MAPPING:
            try:
                driver_obj = Driver.objects.get(id=self.DRIVER_MAPPING[driver_name])
                load_data['driver'] = driver_obj
            except Driver.DoesNotExist:
                logger.warning(f"Driver ID {self.DRIVER_MAPPING[driver_name]} topilmadi")
        
        # Load № -> trip_id
        load_num = row.get('Load №')
        if pd.notna(load_num):
            try:
                load_data['trip_id'] = int(load_num)
            except (ValueError, TypeError):
                logger.warning(f"Load № ni int ga o'tkazib bo'lmadi: {load_num}")
        
        # Rate -> load_pay va total_pay
        rate = row.get('Rate')
        if pd.notna(rate):
            try:
                rate_value = float(str(rate).replace('$', '').replace(',', ''))
                load_data['load_pay'] = rate_value
                load_data['total_pay'] = rate_value
            except (ValueError, TypeError):
                logger.warning(f"Rate ni float ga o'tkazib bo'lmadi: {rate}")
        
        # Agar load_data bo'sh bo'lsa, kamida load_id bilan qaytarish
        if not load_data:
            load_data = {'load_id': str(blackhawks_load).strip()}
        
        return load_data
    
    def _extract_stops_data(self, row, load):
        """Qatordan Stops uchun ma'lumotlarni ajratib olish"""
        stops_data = []
        
        # PICKUP Stop
        pickup_data = self._create_stop_data(
            row, load, 'PICKUP',
            address_col=' Pick up 🏭 Address',
            date_col='Pick up/Arrive 🏭 Date',
            time_col='Pick up /Arrive 🏭 Time',
            company_col='Pick up 🏭 Facility name',
            ref_col='Pick up 🏭 Number'
        )
        if pickup_data:
            stops_data.append(pickup_data)

        # DELIVERY Stop (Last Stop)
        delivery_data = self._create_stop_data(
            row, load, 'DELIVERY',
            address_col='Delivery Address for Last Stop',
            date_col='Arrive Date for Last Stop',
            time_col='Arrive Time for Last Stop',
            company_col='Delivery name for Last Stop 🏭',
            ref_col='Pick up / Delivery № for Last Stop'
        )
        if delivery_data:
            stops_data.append(delivery_data)

        # Stop-2
        stop2_data = self._create_stop_data(
            row, load, 'Stop-2',
            address_col='Delivery address for Stop2',
            date_col='Delivery Date for Stop2',
            time_col='Delivery Time for Stop2',
            company_col=' Delivery name for Stop🏭2',
            ref_col='Delivery number for Stop2'
        )
        if stop2_data:
            stops_data.append(stop2_data)

        # Stop-3
        stop3_data = self._create_stop_data(
            row, load, 'Stop-3',
            address_col='Delivery Adress for Stop3',
            date_col='Delivery Date for Stop3',
            time_col='Delivery Time for Stop3',
            company_col='Delivery name for Stop3',
            ref_col='Delivery Number for Stop3'
        )
        if stop3_data:
            stops_data.append(stop3_data)

        return stops_data
    
    def _create_stop_data(self, row, load, stop_name, address_col, date_col, time_col, company_col, ref_col):
        """Bitta stop uchun ma'lumotlarni yaratish"""
        # Address majburiy - mavjud emas bo'lsa None qaytarish
        address = row.get(address_col)
        if not pd.notna(address) or not str(address).strip():
            return None
        
        stop_data = {
            'load': load,
            'stop_name': stop_name,
            'address1': str(address).strip(),
        }
        
        # Company name
        company = row.get(company_col)
        if pd.notna(company) and str(company).strip():
            stop_data['company_name'] = str(company).strip()
        
        # Reference ID
        ref_id = row.get(ref_col)
        if pd.notna(ref_id) and str(ref_id).strip():
            stop_data['reference_id'] = str(ref_id).strip()
        
        # Date va Time ni birlashtirish
        appointment_datetime = self._combine_date_time(
            row.get(date_col), row.get(time_col)
        )
        if appointment_datetime:
            stop_data['appointmentdate'] = appointment_datetime
        
        return stop_data
    
    def _combine_date_time(self, date_val, time_val):
        """Sana va vaqtni birlashtirish"""
        try:
            if pd.notna(date_val) and pd.notna(time_val):
                # Date ni parse qilish
                if isinstance(date_val, str):
                    date_obj = pd.to_datetime(date_val, errors='coerce')
                    if pd.isna(date_obj):
                        return None
                    date_obj = date_obj.date()
                else:
                    date_obj = date_val
                
                # Time ni parse qilish
                if isinstance(time_val, str):
                    time_obj = pd.to_datetime(time_val, errors='coerce')
                    if pd.isna(time_obj):
                        return None
                    time_obj = time_obj.time()
                else:
                    time_obj = time_val
                
                # Birlashtirish
                return datetime.combine(date_obj, time_obj)
            
            elif pd.notna(date_val):
                # Faqat sana
                date_obj = pd.to_datetime(date_val, errors='coerce')
                if pd.isna(date_obj):
                    return None
                return date_obj
            
            return None
            
        except Exception as e:
            logger.warning(f"Sana/vaqt parse qilishda xatolik: {str(e)}")
            return None
    
    def __str__(self):
        return f"Import {self.imported_at.strftime('%Y-%m-%d %H:%M')} - {self.success_records}/{self.total_records}"
    
    class Meta:
        verbose_name = "Google Sheets Import"
        verbose_name_plural = "Google Sheets Imports"