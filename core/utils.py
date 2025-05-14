# utils.py
import qrcode
import os
from django.conf import settings

def generate_qr_code(business_id, table_number):
    """
    Generate QR code for a specific table number
    
    Args:
        business_id: The ID of the business 
        table_number: The table number to generate QR for
        
    Returns:
        str: The path to the saved QR code image relative to MEDIA_ROOT
    """
    # Create URL with table parameter
    url = f"{settings.BASE_URL}/menu/?table={table_number}&business={business_id}"
    
    # Generate QR code
    qr = qrcode.make(url)
    
    # Create directory if it doesn't exist
    qr_code_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
    os.makedirs(qr_code_dir, exist_ok=True)
    
    # Create unique filename (business_id-table_number.png)
    filename = f"table_{business_id}_{table_number}.png"
    filepath = os.path.join(qr_code_dir, filename)
    
    # Save QR code image
    qr.save(filepath)
    
    # Return path relative to MEDIA_ROOT
    return f"qr_codes/{filename}"