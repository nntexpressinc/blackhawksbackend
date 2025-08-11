
from django.db import models
import requests
from apps.load.models import Load
from apps.auth.models import User
from PIL import Image
from reportlab.pdfgen import canvas
import os
from django.conf import settings
import json

# Telegram ID formatini tekshirish va to'g'rilash
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

def get_group_id_from_updates(bot_token):
    """
    Retrieve group ID from recent updates
    Bot must be in the group and there should be recent messages
    """
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            groups_found = []
            for update in data["result"]:
                if "message" in update:
                    chat = update["message"]["chat"]
                    if chat["type"] in ["group", "supergroup"]:
                        group_info = {
                            "id": chat["id"],
                            "title": chat.get("title", "Unknown"),
                            "type": chat["type"]
                        }
                        if group_info not in groups_found:
                            groups_found.append(group_info)
            
            print("Groups found:")
            for group in groups_found:
                print(f"Group ID: {group['id']}")
                print(f"Group Title: {group['title']}")
                print(f"Group Type: {group['type']}")
                print("---")
            
            return groups_found
        else:
            print(f"Error getting updates: {data.get('description')}")
            return []
    except Exception as e:
        print(f"Error in get_group_id_from_updates: {str(e)}")
        return []

def get_chat_info(bot_token, chat_id):
    """
    Get detailed information about a chat/group
    """
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getChat"
        data = {"chat_id": chat_id}
        response = requests.post(url, data=data, timeout=10)
        
        result = response.json()
        if result.get("ok"):
            chat_info = result["result"]
            return {
                "id": chat_info["id"],
                "title": chat_info.get("title"),
                "type": chat_info["type"],
                "username": chat_info.get("username"),
                "description": chat_info.get("description"),
                "member_count": chat_info.get("member_count")
            }
        else:
            print(f"Error getting chat info: {result.get('description')}")
            return None
    except Exception as e:
        print(f"Error in get_chat_info: {str(e)}")
        return None

def discover_all_chats(bot_token):
    """
    Discover all chats the bot is currently in
    """
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        chat_ids = set()
        if data.get("ok"):
            for update in data["result"]:
                if "message" in update:
                    chat_id = update["message"]["chat"]["id"]
                    chat_ids.add(chat_id)
        
        print("All chats discovered:")
        all_chats = []
        # Get info for each chat
        for chat_id in chat_ids:
            chat_info = get_chat_info(bot_token, chat_id)
            if chat_info:
                all_chats.append(chat_info)
                print(f"Chat ID: {chat_info['id']}")
                print(f"Title: {chat_info.get('title', 'N/A')}")
                print(f"Type: {chat_info['type']}")
                print(f"Username: {chat_info.get('username', 'N/A')}")
                print("---")
        
        return all_chats
    except Exception as e:
        print(f"Error in discover_all_chats: {str(e)}")
        return []

def test_telegram_connection(bot_token):
    """
    Test if bot token is valid and bot is working
    """
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("ok"):
            bot_info = data["result"]
            print("Bot connection successful!")
            print(f"Bot username: @{bot_info['username']}")
            print(f"Bot first name: {bot_info['first_name']}")
            print(f"Bot ID: {bot_info['id']}")
            return True
        else:
            print(f"Bot connection failed: {data.get('description')}")
            return False
    except Exception as e:
        print(f"Error testing bot connection: {str(e)}")
        return False

def send_telegram_message_with_retry(bot_token, chat_id, message, reply_to_message_id=None, max_retries=3):
    """
    Send telegram message with retry mechanism
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    if reply_to_message_id:
        data["reply_to_message_id"] = reply_to_message_id
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, data=data, timeout=10)
            response_data = response.json()
            
            if response_data.get("ok"):
                return response_data
            else:
                print(f"Telegram API error (attempt {attempt+1}): {response_data.get('description')}")
                if attempt == max_retries - 1:
                    return response_data
        except requests.exceptions.RequestException as e:
            print(f"Connection error (attempt {attempt+1}): {str(e)}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
    
    return None

class Chat(models.Model):
    load_id = models.ForeignKey(Load, related_name='LoadChat', on_delete=models.CASCADE)
    message = models.CharField(max_length=300)
    user = models.ForeignKey(User, related_name='UserChat', on_delete=models.CASCADE)
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    group_message_id = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Yangi obyekt yaratilganda
            super().save(*args, **kwargs)

            # Team ma'lumotlarini olish
            team = self.load_id.team_id
            
            # Agar team belgilanmagan bo'lsa yoki telegram ma'lumotlari bo'lmasa, funksiyadan chiqamiz
            if not team or not team.telegram_group_id or not self.load_id.group_message_id:
                print("Team not assigned, Telegram configuration missing, or load has no group_message_id.")
                return
            
            # Team modelidagi telegram ma'lumotlaridan foydalanish
            bot_token = team.telegram_token if hasattr(team, 'telegram_token') else "7582469651:AAHBtrGUmdo2tzDPU4RSI61AFN99EQnqbJE"  # Default token
            
            # Telegram ID formatini tekshirish va to'g'rilash
            group_channel_id = process_telegram_id(team.telegram_group_id)
            
            message = f"{self.user.email}: {self.message}"

            # Agar fayl bo'lmasa, faqat matnli xabar yuboramiz
            if not self.file:
                reply_to_id = None
                try:
                    reply_to_id = int(self.load_id.group_message_id) + 1  # +1 qo'shiladi
                except (ValueError, TypeError):
                    print("Invalid group_message_id format")
                
                response_data = send_telegram_message_with_retry(
                    bot_token, 
                    group_channel_id, 
                    message, 
                    reply_to_id
                )

                if response_data and response_data.get("ok"):
                    print("Matnli xabar yuborildi.")
                    self.group_message_id = response_data["result"]["message_id"]
                    super().save(update_fields=['group_message_id'])
                else:
                    print(f"Xatolik (matn): {response_data.get('description') if response_data else 'Network error'}")
                    return

            # Agar fayl bo'lsa, uni tekshirish va yuborish (xabar faqat caption'da)
            if self.file:
                file_path = self.file.path
                file_name = self.file.name

                reply_to_id = None
                try:
                    reply_to_id = int(self.load_id.group_message_id) + 1  # +1 qo'shiladi
                except (ValueError, TypeError):
                    print("Invalid group_message_id format")

                # Fayl turi bo'yicha tekshirish
                if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):  # Rasm bo'lsa
                    # Rasmni PDF ga aylantirish
                    pdf_path = self.convert_image_to_pdf(file_path)
                    if pdf_path:
                        response_data = self.send_document(bot_token, group_channel_id, pdf_path, message, reply_to_id)
                        
                        # Vaqtinchalik PDF faylni o'chirish
                        if os.path.exists(pdf_path):
                            os.remove(pdf_path)
                    else:
                        print("Failed to convert image to PDF")
                        return

                else:  # PDF yoki boshqa fayl bo'lsa
                    response_data = self.send_document(bot_token, group_channel_id, file_path, message, reply_to_id)

                if response_data and response_data.get("ok"):
                    print("Fayl muvaffaqiyatli yuborildi.")
                    self.group_message_id = response_data["result"]["message_id"]
                    super().save(update_fields=['group_message_id'])
                else:
                    print(f"Xatolik (fayl): {response_data.get('description') if response_data else 'Network error'}")

        else:
            super().save(*args, **kwargs)

    def send_document(self, bot_token, chat_id, file_path, caption, reply_to_message_id=None, max_retries=3):
        """
        Send document with retry mechanism
        """
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        data = {
            "chat_id": chat_id,
            "caption": caption
        }
        
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id

        for attempt in range(max_retries):
            try:
                with open(file_path, 'rb') as doc_file:
                    files = {"document": (os.path.basename(file_path), doc_file)}
                    response = requests.post(url, data=data, files=files, timeout=30)
                
                response_data = response.json()
                
                if response_data.get("ok"):
                    return response_data
                else:
                    print(f"Document send error (attempt {attempt+1}): {response_data.get('description')}")
                    if attempt == max_retries - 1:
                        return response_data
            except requests.exceptions.RequestException as e:
                print(f"Connection error sending document (attempt {attempt+1}): {str(e)}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)
            except FileNotFoundError:
                print(f"File not found: {file_path}")
                return None
        
        return None

    def convert_image_to_pdf(self, image_path):
        """Rasmni PDF ga aylantirish"""
        try:
            image = Image.open(image_path)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Vaqtinchalik PDF fayl yaratish
            pdf_filename = f"{os.path.splitext(os.path.basename(image_path))[0]}.pdf"
            pdf_path = os.path.join(settings.MEDIA_ROOT, 'temp', pdf_filename)
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

            # PDF yaratish
            c = canvas.Canvas(pdf_path)
            img_width, img_height = image.size
            
            # A4 o'lchamiga moslashtirish
            a4_width, a4_height = 595.27, 841.89  # A4 size in points
            
            # Rasmni A4 ga sig'dirish uchun masshtablash
            scale_x = a4_width / img_width
            scale_y = a4_height / img_height
            scale = min(scale_x, scale_y)
            
            new_width = img_width * scale
            new_height = img_height * scale
            
            # Rasm markazda joylashishi uchun koordinatalar
            x = (a4_width - new_width) / 2
            y = (a4_height - new_height) / 2
            
            c.setPageSize((a4_width, a4_height))
            c.drawImage(image_path, x, y, new_width, new_height)
            c.showPage()
            c.save()

            return pdf_path
        except Exception as e:
            print(f"Error converting image to PDF: {str(e)}")
            return None

    @classmethod
    def discover_team_groups(cls, team):
        """
        Discover all groups for a specific team's bot token
        """
        if not hasattr(team, 'telegram_token') or not team.telegram_token:
            print("Team has no telegram token")
            return []
        
        bot_token = team.telegram_token
        
        print(f"Discovering groups for team: {team.name}")
        print(f"Testing bot connection...")
        
        if not test_telegram_connection(bot_token):
            return []
        
        print("Getting group information...")
        groups = get_group_id_from_updates(bot_token)
        
        return groups

    @classmethod
    def setup_team_telegram(cls, team, group_id, channel_id=None):
        """
        Setup telegram configuration for a team
        """
        if not hasattr(team, 'telegram_token') or not team.telegram_token:
            print("Team needs a telegram token first")
            return False
        
        # Test the group ID
        chat_info = get_chat_info(team.telegram_token, group_id)
        if not chat_info:
            print(f"Cannot access group with ID: {group_id}")
            return False
        
        print(f"Setting up telegram for team: {team.name}")
        print(f"Group: {chat_info['title']} (ID: {chat_info['id']})")
        
        # Update team with group ID
        team.telegram_group_id = str(group_id)
        if channel_id:
            team.telegram_channel_id = str(channel_id)
        team.save()
        
        print("Telegram configuration updated successfully!")
        return True