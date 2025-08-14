import requests
import time
import threading
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from apps.load.models.load import Load
from requests.exceptions import ConnectionError, Timeout, RequestException

# Telegram xabarlarini asinxron ravishda yuborish
@receiver(post_save, sender=Load)
def trigger_telegram_message(sender, instance, created, **kwargs):
    # Xabarni alohida oqimda yuborish
    thread = threading.Thread(target=send_telegram_message, args=(sender, instance, created, kwargs))
    thread.daemon = True
    thread.start()

def send_telegram_message(sender, instance, created, kwargs):
    try:
        # Team modelidan telegram ma'lumotlarini olish
        team = instance.team_id

        # Agar team belgilanmagan bo'lsa yoki telegram konfiguratsiyasi bo'lmasa, funksiyadan chiqish
        if not team or not team.telegram_channel_id or not team.telegram_group_id:
            print("Team not assigned or Telegram configuration missing.")
            return

        # Team modelidan telegram konfiguratsiyasini olish
        bot_token = team.telegram_token if hasattr(team, 'telegram_token') else "7582469651:AAHBtrGUmdo2tzDPU4RSI61AFN99EQnqbJE"

        # Telegram kanal va guruh ID formatini tekshirish va to'g'rilash
        channel_id = process_telegram_id(team.telegram_channel_id)
        group_id = process_telegram_id(team.telegram_group_id)

        # Unit number olish
        unit_number = "Not assigned"
        if instance.unit_id:
            unit_number = instance.unit_id.unit_number

        # Trailer make olish
        trailer_make = "Not assigned"
        if instance.unit_id and instance.unit_id.trailer.exists():
            first_trailer = instance.unit_id.trailer.first()
            if first_trailer and first_trailer.make:
                trailer_make = first_trailer.make

        # Driver name olish
        driver_name = "Not assigned"
        if instance.driver and instance.driver.user:
            first_name = instance.driver.user.first_name or ""
            last_name = instance.driver.user.last_name or ""
            driver_name = f"{first_name} {last_name}".strip()
            if not driver_name:
                driver_name = "Not assigned"

        # Team name va dispatcher nickname olish
        team_info = "Not assigned"
        if instance.team_id:
            team_name = instance.team_id.name or "Unknown Team"
            dispatcher_nickname = ""
            if instance.dispatcher and hasattr(instance.dispatcher, 'nickname'):
                dispatcher_nickname = f"    ({instance.dispatcher.nickname})"
            team_info = f"{team_name}{dispatcher_nickname}"

        # Stops ma'lumotlarini olish va formatda saralash
        stops_text = ""
        delivery_stop = None

        if instance.stop.exists():
            for stop in instance.stop.all():
                # Address formatini yaratish
                address_parts = []
                if hasattr(stop, 'address1') and stop.address1:
                    address_parts.append(stop.address1)
                if hasattr(stop, 'address2') and stop.address2:
                    address_parts.append(stop.address2)
                if hasattr(stop, 'city') and stop.city:
                    address_parts.append(stop.city)
                if hasattr(stop, 'state') and stop.state:
                    address_parts.append(stop.state)
                if hasattr(stop, 'zip_code') and stop.zip_code:
                    address_parts.append(str(stop.zip_code))

                full_address = ", ".join(address_parts) if address_parts else "Address not specified"

                # Arrive time formatini yaratish
                arrive_info = ""
                if hasattr(stop, 'appointmentdate') and stop.appointmentdate:
                    # DateTime formatini o'zgartirish
                    arrive_info = f"Date {stop.appointmentdate.strftime('%m/%d/%Y')} Time {stop.appointmentdate.strftime('%H:%M')}"
                else:
                    # If appointmentdate is not available, check for fcfs and plus_hour
                    time_parts = []

                    if hasattr(stop, 'fcfs') and stop.fcfs:
                        time_parts.append(f"FCFS: {stop.fcfs.strftime('%m/%d/%Y %H:%M')}")

                    if hasattr(stop, 'plus_hour') and stop.plus_hour:
                        time_parts.append(f"Plus Hour: {stop.plus_hour.strftime('%m/%d/%Y %H:%M')}")

                    if time_parts:
                        arrive_info = " | ".join(time_parts)
                    else:
                        arrive_info = "FCFS"

                # Reference ID ni olish
                ref_number = ""
                if hasattr(stop, 'reference_id') and stop.reference_id:
                    ref_number = stop.reference_id

                # Stop name ni olish
                stop_name = getattr(stop, 'stop_name', 'Stop')

                # Delivery stopni alohida saqlash
                if stop_name.upper() == 'DELIVERY':
                    delivery_stop = {
                        'stop_name': stop_name,
                        'company': getattr(stop, 'company_name', 'Unknown Company'),
                        'address': full_address,
                        'arrive_info': arrive_info,
                        'ref_number': ref_number
                    }
                else:
                    # Pickup va boshqa stoplar uchun
                    stops_text += f"""
<b>{stop_name}:</b> 🏭
{getattr(stop, 'company_name', 'Unknown Company')}
{full_address}
Arrive: {arrive_info}
{stop_name} №: {ref_number}
"""

        # Agar stops mavjud bo'lmasa, default pickup ma'lumotini ishlatish
        if not stops_text:
            stops_text = f"""
<b>Pick up:</b> 🏭
{instance.pickup_location or 'Location not specified'}
Arrive: Date {instance.pickup_date.strftime('%m/%d/%Y') if instance.pickup_date else 'TBD'} Time FCFS
Pick up №: 
"""

        # Last Stop (Delivery) formatini yaratish
        last_stop_text = ""
        if delivery_stop:
            last_stop_text = f"""
{delivery_stop['company']}
{delivery_stop['address']}
Arrive: {delivery_stop['arrive_info']}
Delivery №: {delivery_stop['ref_number']}"""
        else:
            last_stop_text = f"""
{instance.delivery_location or 'Location not specified'}
Arrive: Date {instance.delivery_date.strftime('%m/%d/%Y') if instance.delivery_date else 'TBD'} Time TBD
Delivery №: """

        # Xabarni yangi formatda tayyorlash
        message = f"""🚚 {unit_number}
🔖{trailer_make}
👨‍✈️ {driver_name}
<b>Load:</b> {instance.load_id or 'Not specified'}
{stops_text}
<b>Last Stop:</b> 🏭{last_stop_text}

<b>Weight:</b> {instance.weight or 'TBD'}

<b>Estimated Payout:</b> ${instance.load_pay or 'TBD'}
  DHM: {instance.empty_mile or 'TBD'}
  LM: {instance.mile or 'TBD'}
<b>$PM:</b> {instance.per_mile or 'TBD'}

<b>Team {team_info}</b>
{instance.company_name or 'Unknown Company'}
---------------------------
⚠️-Traffic/Construction/Weather or other delays (photos or videos) -  should be updated in good time by drivers
⚠️-Please Scale the load after pick up, to avoid axle overweight. Missing scale ticket - 200$ penalty fee.
⚠️-After hooking up the trailer, PTI should be done !!!
🛞<b>Tire pressure:</b>
✍️Drive tire - 105 psi.
✍️Steering tire - 110 psi.
✍️Trailer tire - 100 psi.
🛞🔨if tire has inflation system you need to hit with a hammer to check the pressure.
⚠️📲If you hear air leak sound or detect an oil leak around the rims let us know immediately.
---------------------------
<b>On time PU/DEL:</b>  $150"""

        if created:
            # Send to channel
            channel_data = {
                "chat_id": channel_id,
                "text": message,
                "parse_mode": "HTML"
            }

            channel_response = send_telegram_request(f"https://api.telegram.org/bot{bot_token}/sendMessage", channel_data)
            if channel_response and channel_response.get("ok"):
                instance.message_id = channel_response["result"]["message_id"]

                # Now send to group
                group_data = {
                    "chat_id": group_id,
                    "text": message,
                    "parse_mode": "HTML"
                }

                group_response = send_telegram_request(f"https://api.telegram.org/bot{bot_token}/sendMessage", group_data)
                if group_response and group_response.get("ok"):
                    group_message_id = group_response["result"]["message_id"]
                    instance.group_message_id = group_message_id
                    
                    # Delete the message from group immediately after sending
                    delete_url = f"https://api.telegram.org/bot{bot_token}/deleteMessage"
                    delete_data = {
                        "chat_id": group_id,
                        "message_id": group_message_id
                    }
                    
                    # Add a small delay to ensure message is fully sent before deletion
                    time.sleep(0.5)
                    
                    delete_response = send_telegram_request(delete_url, delete_data)
                    if delete_response and delete_response.get("ok"):
                        print(f"Message sent to group and deleted. Saved group_message_id: {group_message_id}")
                    else:
                        print(f"Message sent to group but failed to delete: {delete_response}")

                # Save both message IDs
                Load.objects.filter(pk=instance.pk).update(
                    message_id=instance.message_id,
                    group_message_id=instance.group_message_id
                )
                print(f"Messages sent - Channel ID: {instance.message_id}, Group ID: {instance.group_message_id}")

            else:
                print(f"Error sending to channel: {channel_response}")
        
        else:
            # Update messages in both places if they exist
            if instance.message_id:
                edit_url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
                edit_data = {
                    "chat_id": channel_id,
                    "message_id": instance.message_id,
                    "text": message,
                    "parse_mode": "HTML"
                }

                edit_response = send_telegram_request(edit_url, edit_data)
                if edit_response and edit_response.get("ok"):
                    print(f"Message updated in channel, message_id: {instance.message_id}")
                else:
                    print(f"Error updating message in channel: {edit_response}")

            # For updates, we don't send to group since the original message was deleted
            # The group_message_id is kept for reference but the message doesn't exist in the group
            print(f"Load updated. Channel message updated. Group message ID {instance.group_message_id} kept for reference.")
            
    except Exception as e:
        # Xatolarni ushlash
        print(f"Error in Telegram notification process: {str(e)}")

def process_telegram_id(telegram_id):
    """
    Telegram ID ni qaysi formatda ekanligini tekshirish va to'g'ri formatga o'zgartirish
    - '@username' formatidan username qilib qaytaradi
    - 'id:123456789' formatidan faqat raqamni qaytaradi
    - '@username extra text' formatidan username qilib qaytaradi
    - Boshqa holatda qiymat o'zgarmaydi
    """
    if not telegram_id:
        return None

    # '@username' formatini tekshirish
    if telegram_id.startswith('@'):
        # '@username' formatidagi bo'lsa, qo'shimcha so'zlarni olib tashlash
        username = telegram_id.split()[0]  # Birinchi so'zni olish (@ bilan)
        return username

    # 'id:123456789' formatini tekshirish
    if telegram_id.lower().startswith('id:'):
        # Faqat ID raqamini qaytarish
        id_parts = telegram_id.split(':')
        if len(id_parts) > 1:
            return id_parts[1].strip()

    # Boshqa formatlar uchun o'zgartirish kerak emas
    return telegram_id

# Telegram so'rovlarini qayta urinish funksiyasi
def send_telegram_request(url, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, data=data, timeout=10)
            return response.json()
        except (ConnectionError, Timeout) as e:
            wait_time = 2 ** attempt
            print(f"Connection error (attempt {attempt+1}/{max_retries}): {str(e)}")
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except RequestException as e:
            print(f"Request error: {str(e)}")
            return None

    print(f"Failed to connect to Telegram API after {max_retries} attempts")
    return None

# O'zgarishlarni kuzatish
@receiver(pre_save, sender=Load)
def detect_changes(sender, instance, **kwargs):
    if instance.pk:
        try:
            # Ma'lumotlar bazasidan joriy yozuvni olish
            old_instance = Load.objects.get(pk=instance.pk)

            # Muhim maydonlardagi o'zgarishlarni tekshirish
            fields_to_check = [
                'load_id', 'reference_id', 'driver', 'company_name', 'instructions',
                'load_status', 'tags', 'equipment_type', 'created_date', 'load_pay', 'weight',
                'driver_pay', 'total_pay', 'mile', 'empty_mile', 'created_date', 'total_miles',
                'rate_con', 'bol', 'pod', 'comercial_invoice', 'pickup_date', 'delivery_date',
                'pickup_location', 'delivery_location', 'unit_id', 'team_id', 'dispatcher',
                'pictures'
            ]

            # O'zgargan maydonlarni saqlash
            instance._changed_fields = []

            for field in fields_to_check:
                old_value = getattr(old_instance, field)
                new_value = getattr(instance, field)
                if old_value != new_value:
                    instance._changed_fields.append(field)

        except Load.DoesNotExist:
            # Bu yangi obyekt
            pass

#automat rename files
import os
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from apps.load.models.load import Load
from apps.chat.models import Chat  # Adjust import path as needed
from apps.auth.models import User

def debug_load_fields():
    """Debug function to check which file fields exist in Load model"""
    load_fields = [field.name for field in Load._meta.get_fields() if hasattr(field, 'upload_to')]
    print("File fields found in Load model:")
    for field in load_fields:
        print(f"  - {field}")
    return load_fields

def rename_file(file_field, prefix, load_id):
    """
    Rename uploaded file with the specified prefix and load_id
    Returns the renamed file or None if no file
    """
    if not file_field or not load_id:
        return None
    
    try:
        # Get the file extension
        original_name = file_field.name
        file_extension = os.path.splitext(original_name)[1]
        
        # Create new filename
        new_filename = f"{prefix}_{load_id}{file_extension}"
        
        # Read the file content
        file_content = file_field.read()
        
        # Reset file pointer to beginning after reading
        file_field.seek(0)
        
        # Create a new ContentFile with the renamed filename
        renamed_file = ContentFile(file_content, name=new_filename)
        
        print(f"File renamed from '{original_name}' to '{new_filename}'")
        return renamed_file
        
    except Exception as e:
        print(f"Error renaming file: {str(e)}")
        return None

@receiver(pre_save, sender=Load)
def handle_file_uploads(sender, instance, **kwargs):
    """
    Handle file uploads and renaming before saving the Load instance
    Only processes files that are uploaded during updates (not initial creation)
    """
    if not instance.load_id:
        return  # Skip if load_id is not set
    
    # Dictionary mapping file fields to their prefixes
    # Note: Using the exact field names from the Load model
    file_mappings = {
        'rate_con': 'RC',
        'bol': 'BOL', 
        'pod': 'POD',
        'comercial_invoice': 'Invoice',
        'pictures': 'Pictures'
    }
    
    # Store information about uploaded files for post_save signal
    if not hasattr(instance, '_uploaded_files'):
        instance._uploaded_files = {}
    
    # Only process if this is an update (has primary key) since files are uploaded later
    if not instance.pk:
        return  # Skip new instances since files are not uploaded during creation
    
    try:
        # Get the old instance to compare files
        old_instance = Load.objects.get(pk=instance.pk)
        
        # Check each file field for changes
        for field_name, prefix in file_mappings.items():
            # Safely get the file fields using hasattr to avoid AttributeError
            if not hasattr(instance, field_name):
                print(f"Warning: Field '{field_name}' not found in Load model")
                continue
                
            old_file = getattr(old_instance, field_name, None)
            new_file = getattr(instance, field_name, None)
            
            # If a new file has been uploaded (file exists and is different from old one)
            if new_file and (not old_file or old_file.name != new_file.name):
                # Rename the file
                renamed_file = rename_file(new_file, prefix, instance.load_id)
                if renamed_file:
                    setattr(instance, field_name, renamed_file)
                    # Store info for chat record creation
                    instance._uploaded_files[field_name] = {
                        'file': renamed_file,
                        'prefix': prefix
                    }
                    print(f"File uploaded and renamed for field '{field_name}': {prefix}_{instance.load_id}")
                    
    except Load.DoesNotExist:
        # This shouldn't happen for updates, but handle gracefully
        print("Error: Load instance not found in database during update")
        pass
    except Exception as e:
        print(f"Error processing file uploads: {str(e)}")
        pass

@receiver(post_save, sender=Load)
def create_chat_records(sender, instance, created, **kwargs):
    """
    Create Chat records for uploaded files after Load instance is saved
    """
    # Check if there are uploaded files to process
    if not hasattr(instance, '_uploaded_files') or not instance._uploaded_files:
        return
    
    # Try to get a default user for the chat record
    # You might want to modify this logic based on your requirements
    default_user = None
    
    # Option 1: Use the created_by user if available
    if instance.created_by:
        default_user = instance.created_by
    else:
        # Option 2: Use the dispatcher user if available
        if instance.dispatcher and hasattr(instance.dispatcher, 'user'):
            default_user = instance.dispatcher.user
        else:
            # Option 3: Get the first admin/superuser as fallback
            try:
                default_user = User.objects.filter(is_staff=True).first()
            except:
                pass
    
    if not default_user:
        print("Warning: No user found for Chat record creation")
        return
    
    # Create chat records for each uploaded file
    for field_name, file_info in instance._uploaded_files.items():
        try:
            # Map field names to chat messages
            message_mapping = {
                'rate_con': 'RC',
                'bol': 'BOL',
                'pod': 'POD',
                'comercial_invoice': 'Invoice',
                'pictures': 'Pictures'
            }
            
            message = message_mapping.get(field_name, field_name.upper())
            
            # Create the chat record with notify_websocket=False to avoid sending notification
            chat_record = Chat(
                load_id=instance,
                message=message,
                user=default_user,
                file=getattr(instance, field_name),  # Use the saved file field
                notify_websocket=False  # Disable websocket notification for file uploads
            )
            
            # Save the chat record
            chat_record.save()
            
            print(f"Chat record created for {field_name}: {message}")
            
        except Exception as e:
            print(f"Error creating chat record for {field_name}: {str(e)}")
    
    # Clean up the temporary attribute
    delattr(instance, '_uploaded_files')

# Alternative approach: Custom upload_to function for each field
def rate_con_upload_path(instance, filename):
    """Custom upload path for rate_con files"""
    if instance.load_id:
        file_extension = os.path.splitext(filename)[1]
        return f"load_documents/RC_{instance.load_id}{file_extension}"
    return f"load_documents/{filename}"

def bol_upload_path(instance, filename):
    """Custom upload path for bol files"""
    if instance.load_id:
        file_extension = os.path.splitext(filename)[1]
        return f"load_documents/BOL_{instance.load_id}{file_extension}"
    return f"load_documents/{filename}"

def pod_upload_path(instance, filename):
    """Custom upload path for pod files"""
    if instance.load_id:
        file_extension = os.path.splitext(filename)[1]
        return f"load_documents/POD_{instance.load_id}{file_extension}"
    return f"load_documents/{filename}"

def comercial_invoice_upload_path(instance, filename):
    """Custom upload path for comercial_invoice files"""
    if instance.load_id:
        file_extension = os.path.splitext(filename)[1]
        return f"load_documents/Invoice_{instance.load_id}{file_extension}"
    return f"load_documents/{filename}"

def pictures_upload_path(instance, filename):
    """Custom upload path for pictures files"""
    if instance.load_id:
        file_extension = os.path.splitext(filename)[1]
        return f"load_documents/Pictures_{instance.load_id}{file_extension}"
    return f"load_documents/{filename}"
