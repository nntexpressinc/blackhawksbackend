# models.py - GoogleSheetsImport modeli qo'shish
from django.db import models
from django.core.exceptions import ValidationError
import pandas as pd
import logging
from datetime import datetime
from django.db import transaction
from apps.load.models.load import Load
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
                        load = Load.objects.create(**load_data)
                        
                        # Stops yaratish
                        stops_data = self._extract_stops_data(row, load)
                        stops_instances = []
                        
                        for stop_data in stops_data:
                            if stop_data:  # Bo'sh bo'lmagan stops
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
        load_data = {}
        
        # Blackhawks load number -> load_id
        if pd.notna(row.get('Blackhawks load number')):
            load_data['load_id'] = str(row['Blackhawks load number'])
        
        # Dispatch name -> dispatcher
        dispatch_name = row.get('Dispatch name', '').strip()
        if dispatch_name in self.DISPATCHER_MAPPING:
            load_data['dispatcher_id'] = self.DISPATCHER_MAPPING[dispatch_name]
        
        # Unit № -> unit_id
        unit_num = str(row.get('Unit №', '')).strip()
        if unit_num in self.UNIT_MAPPING:
            load_data['unit_id'] = self.UNIT_MAPPING[unit_num]
        
        # Driver -> driver
        driver_name = row.get('Assiged trailer Driver', '').strip()
        if driver_name in self.DRIVER_MAPPING:
            load_data['driver_id'] = self.DRIVER_MAPPING[driver_name]
        
        # Load № -> trip_id
        if pd.notna(row.get('Load №')):
            try:
                load_data['trip_id'] = int(row['Load №'])
            except (ValueError, TypeError):
                pass
        
        # Rate -> load_pay va total_pay
        if pd.notna(row.get('Rate')):
            try:
                rate_value = float(str(row['Rate']).replace('$', '').replace(',', ''))
                load_data['load_pay'] = rate_value
                load_data['total_pay'] = rate_value
            except (ValueError, TypeError):
                pass
        
        # DeadHead -> empty_mile
        if pd.notna(row.get('DeadHead')):
            try:
                load_data['empty_mile'] = int(row['DeadHead'])
            except (ValueError, TypeError):
                pass
        
        # Loaded mile -> mile
        if pd.notna(row.get('Loaded mile')):
            try:
                load_data['mile'] = int(row['Loaded mile'])
            except (ValueError, TypeError):
                pass
        
        # $ per mile -> per_mile
        if pd.notna(row.get('$ per mile')):
            try:
                per_mile_value = float(str(row['$ per mile']).replace('$', '').replace(',', ''))
                load_data['per_mile'] = per_mile_value
            except (ValueError, TypeError):
                pass
        
        # Broker -> customer_broker (har doim 1)
        if pd.notna(row.get('Broker')):
            load_data['customer_broker_id'] = 1
        
        # NOTE -> note
        if pd.notna(row.get('NOTE')):
            load_data['note'] = str(row['NOTE'])
        
        # Pick up Address -> pickup_location
        if pd.notna(row.get(' Pick up 🏭 Address')):
            load_data['pickup_location'] = str(row[' Pick up 🏭 Address'])
        
        # Delivery Address -> delivery_location
        if pd.notna(row.get('Delivery Address for Last Stop')):
            load_data['delivery_location'] = str(row['Delivery Address for Last Stop'])
        
        # Default values
        load_data['load_status'] = 'OPEN'
        load_data['created_by_id'] = 1  # Default user
        
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
        # Address majburiy
        if not pd.notna(row.get(address_col)):
            return None
        
        stop_data = {
            'load': load,
            'stop_name': stop_name,
            'address1': str(row[address_col]),
        }
        
        # Company name
        if pd.notna(row.get(company_col)):
            stop_data['company_name'] = str(row[company_col])
        
        # Reference ID
        if pd.notna(row.get(ref_col)):
            stop_data['reference_id'] = str(row[ref_col])
        
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
                    date_obj = pd.to_datetime(date_val).date()
                else:
                    date_obj = date_val
                
                # Time ni parse qilish
                if isinstance(time_val, str):
                    time_obj = pd.to_datetime(time_val).time()
                else:
                    time_obj = time_val
                
                # Birlashtirish
                return datetime.combine(date_obj, time_obj)
            
            elif pd.notna(date_val):
                # Faqat sana
                return pd.to_datetime(date_val)
            
            return None
            
        except Exception as e:
            logger.warning(f"Sana/vaqt parse qilishda xatolik: {str(e)}")
            return None
    
    def __str__(self):
        return f"Import {self.imported_at.strftime('%Y-%m-%d %H:%M')} - {self.success_records}/{self.total_records}"
    
    class Meta:
        verbose_name = "Google Sheets Import"
        verbose_name_plural = "Google Sheets Imports"

