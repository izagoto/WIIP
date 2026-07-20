import sqlite3
import requests
import os
from Crypto.Cipher import AES
from hkdf import hkdf_expand, hkdf_extract
import hashlib

def decrypt_whatsapp_media(media_key, enc_data, media_type):
    app_info = {
        'image': b'WhatsApp Image Keys',
        'video': b'WhatsApp Video Keys',
        'audio': b'WhatsApp Audio Keys',
        'document': b'WhatsApp Document Keys'
    }
    info = app_info.get(media_type, b'WhatsApp Video Keys')
    
    # Expand the 32 byte media_key into 112 bytes
    # HKDF-SHA256 requires extraction first, then expansion
    prk = hkdf_extract(salt=None, input_key_material=media_key, hash=hashlib.sha256)
    expanded_key = hkdf_expand(prk, info, 112, hash=hashlib.sha256)
    
    iv = expanded_key[:16]
    cipher_key = expanded_key[16:48]
    mac_key = expanded_key[48:80]
    
    # The last 10 bytes of enc_data are the MAC
    enc_data_no_mac = enc_data[:-10]
    
    cipher = AES.new(cipher_key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(enc_data_no_mac)
    
    # Remove PKCS7 padding
    pad = decrypted[-1]
    if isinstance(pad, int):
        decrypted = decrypted[:-pad]
    else:
        decrypted = decrypted[:-ord(pad)]
        
    return decrypted

def main():
    db_path = "R9CX100A5NF.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get 1 video where URL is not null
    cursor.execute("SELECT * FROM message_media WHERE mime_type LIKE 'video%' AND message_url IS NOT NULL LIMIT 1")
    row = cursor.fetchone()

    if row:
        media_key = row['media_key']
        url = row['message_url']
        file_path = row['file_path']
        if file_path:
            file_name = os.path.basename(file_path)
        else:
            file_name = "extracted_video.mp4"
            
        print(f"Found video metadata in DB:")
        print(f"- File Path: {file_path}")
        print(f"- File Name: {file_name}")
        print(f"- Download URL: {url}")
        
        print(f"\nDownloading encrypted video file...")
        response = requests.get(url)
        if response.status_code == 200:
            enc_data = response.content
            print(f"Downloaded encrypted data ({len(enc_data)} bytes). Decrypting...")
            
            try:
                decrypted_data = decrypt_whatsapp_media(media_key, enc_data, 'video')
                with open(file_name, 'wb') as f:
                    f.write(decrypted_data)
                print(f"Successfully extracted and decrypted video to {os.path.abspath(file_name)}")
            except Exception as e:
                print(f"Decryption failed: {e}")
        else:
            print(f"Failed to download. HTTP Status: {response.status_code}")
    else:
        print("No video found in message_media with a valid URL.")

if __name__ == "__main__":
    main()
