# AI-Powered Rate Confirmation File Parser
# This solution uses OpenAI API to extract structured data from various rate con file formats

import json
import openai
from datetime import datetime
from django.core.files.uploadedfile import InMemoryUploadedFile
import PyPDF2
import docx
from io import BytesIO
import re
from django.conf import settings
from openai import OpenAI

class RateConParser:
    def __init__(self):
        # Set up OpenAI client (new v1.0+ API)
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo"  # or "gpt-4" for better accuracy
        
    def extract_text_from_file(self, file):
        """Extract text from various file formats"""
        file_extension = file.name.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            return self._extract_from_pdf(file)
        elif file_extension in ['doc', 'docx']:
            return self._extract_from_docx(file)
        elif file_extension == 'txt':
            return file.read().decode('utf-8')
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def _extract_from_pdf(self, file):
        """Extract text from PDF file"""
        pdf_reader = PyPDF2.PdfReader(BytesIO(file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    
    def _extract_from_docx(self, file):
        """Extract text from DOCX file"""
        doc = docx.Document(BytesIO(file.read()))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def parse_with_ai(self, text_content):
        """Use OpenAI to extract structured data from rate con text"""
        
        # Define the prompt for AI to extract specific logistics data
        prompt = f"""
        Extract the following information from this rate confirmation document and return it as JSON:
        
        Required fields:
        - load_id: Load or reference number
        - pickup_date: Pickup date and time (format: MM/DD/YYYY or YYYY-MM-DD)
        - delivery_date: Delivery date and time (format: MM/DD/YYYY or YYYY-MM-DD)
        - pickup_location: Complete pickup address
        - delivery_location: Complete delivery address
        - equipment_type: Type of equipment (DRYVAN, REEFER, FLATBED, STEPDECK, POWERONLY, etc.)
        - load_pay: Total load payment amount (number only, no currency symbols)
        - mile: Total miles (number only)
        - company_name: Broker/customer company name
        - reference_id: Any reference numbers
        - instructions: Special instructions
        - contact_number: Contact phone number (digits only)
        - email_address: Contact email
        - mc_number: MC number if available
        - bills: Number of bills/pieces
        
        Document text:
        {text_content}
        
        IMPORTANT: Return ONLY valid JSON format with the extracted data. If a field is not found, use null. Do not include any explanatory text before or after the JSON.
        
        Example format:
        {{
            "load_id": "ABC123",
            "pickup_date": "12/25/2024",
            "delivery_date": "12/27/2024",
            "pickup_location": "123 Main St, Chicago, IL 60601",
            "delivery_location": "456 Oak Ave, Dallas, TX 75201",
            "equipment_type": "DRYVAN",
            "load_pay": 2500.00,
            "mile": 925,
            "company_name": "ABC Logistics",
            "reference_id": "REF456",
            "instructions": "Call before pickup",
            "contact_number": "5551234567",
            "email_address": "dispatch@abc.com",
            "mc_number": "123456",
            "bills": 1
        }}
        """
        
        return self._parse_with_openai(prompt)
    
    def _parse_with_openai(self, prompt):
        """Parse using OpenAI API (v1.0+)"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a logistics data extraction expert. Extract data from rate confirmation documents and return only valid JSON format."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            return self._extract_json_from_response(ai_response)
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to regex parsing
            document_text = prompt.split("Document text:")[1] if "Document text:" in prompt else prompt
            return self._fallback_regex_parsing(document_text)
    
    def _extract_json_from_response(self, ai_response):
        """Extract JSON from OpenAI response text"""
        try:
            # Clean the response - remove any markdown formatting
            cleaned_response = ai_response.replace('```json', '').replace('```', '').strip()
            
            # Try to parse as JSON directly
            return json.loads(cleaned_response)
            
        except json.JSONDecodeError:
            try:
                # Try to find JSON in the response using regex
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    return json.loads(json_str)
                else:
                    raise ValueError("No JSON found in AI response")
            except:
                # If all parsing fails, use regex fallback
                print("Failed to parse AI response as JSON, using regex fallback")
                return self._fallback_regex_parsing(ai_response)
    
    def _fallback_regex_parsing(self, text):
        """Fallback regex parsing when AI fails"""
        data = {}
        
        # Common regex patterns for logistics documents
        patterns = {
            'load_id': r'(?:Load|Ref|Reference)[\s#:]*([A-Za-z0-9-]+)',
            'pickup_date': r'(?:Pick\s*up|PU)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'delivery_date': r'(?:Deliver|Del|Drop)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'load_pay': r'(?:\$|Rate|Pay)[\s:]*(\d+[,.]?\d*)',
            'mile': r'(?:Miles?)[\s:]*(\d+)',
            'contact_number': r'(?:Phone|Tel|Contact)[\s:]*(\d{3}[-.]?\d{3}[-.]?\d{4})',
            'email_address': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            'mc_number': r'MC[\s#:]*(\d+)',
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            data[field] = match.group(1) if match else None
        
        # Extract addresses (more complex)
        data['pickup_location'] = self._extract_address(text, 'pickup')
        data['delivery_location'] = self._extract_address(text, 'delivery')
        
        return data
    
    def _extract_address(self, text, address_type):
        """Extract pickup or delivery address"""
        if address_type.lower() == 'pickup':
            keywords = ['pickup', 'origin', 'shipper', 'pu']
        else:
            keywords = ['delivery', 'destination', 'consignee', 'del']
        
        # This is simplified - you'd need more sophisticated address extraction
        for keyword in keywords:
            pattern = rf'{keyword}[\s:]*([^\n]*(?:\n[^\n]*?)*)(?=\n\s*(?:{"delivery|pickup|rate|total"}|$))'
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        return None


# Django View Integration



# URL Configuration
