import urllib.request
import urllib.parse
import urllib.error
import json
import csv
import time
import random
import re
import os

# ==========================================
# 1. KONFIGURASI MANUAL
# ==========================================
# WAJIB COPY COOKIE BARU DARI BROWSER (Setelah login ulang/refresh)
SESSION_COOKIE = os.getenv("INSTAGRAM_SESSION_COOKIE")
TARGET_USER_ID = os.getenv("INSTAGRAM_TARGET_USER_ID")
NAMA_FILE_CSV = os.getenv("INSTAGRAM_CSV_FILENAME", "followers.csv")

def get_csrf_token(cookie_string):
    """Mengekstrak CSRF Token dari string Cookie"""
    match = re.search(r'csrftoken=([^;]+)', cookie_string)
    if match:
        return match.group(1)
    return ""

# ==========================================
# 2. FUNGSI SCRAPER (REST API V1)
# ==========================================
def fetch_followers_api(max_id=""):
    url = f"https://www.instagram.com/api/v1/friendships/{TARGET_USER_ID}/followers/?count=50"
    if max_id:
        url += f"&max_id={max_id}"

    # Ekstrak token secara otomatis
    csrf_token = get_csrf_token(SESSION_COOKIE)

    # HEADERS DIPERBARUI: Menambahkan CSRF Token & XMLHttpRequest
    headers = {
        "Cookie": SESSION_COOKIE,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "X-IG-App-ID": "936619743392459",
        "X-CSRFToken": csrf_token,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "*/*"
    }

    req = urllib.request.Request(url, headers=headers, method='GET')
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"❌ Terjadi kesalahan sistem: {e}")
        
    return None

# ==========================================
# 3. LOGIKA UTAMA & PENYIMPANAN
# ==========================================
def main():
    csrf = get_csrf_token(SESSION_COOKIE)
    if not csrf:
        print("⚠ Peringatan: 'csrftoken' tidak ditemukan di dalam teks Cookie-mu!")
        print("Pastikan kamu meng-copy KESELURUHAN teks cookie, bukan cuma 'sessionid'.\n")
        return

    print(f"Mulai mengambil followers untuk User ID: {TARGET_USER_ID}...")
    
    semua_followers = []
    has_next_page = True
    next_max_id = ""
    halaman = 1

    while has_next_page:
        print(f"-> Mengambil halaman {halaman}...")
        data = fetch_followers_api(next_max_id)
        
        if not data:
            print("Berhenti: Gagal mengambil data. Cookie mungkin hangus.")
            break
            
        users = data.get('users', [])
        
        for user in users:
            semua_followers.append({
                "username": user.get('username', ''),
                "full_name": user.get('full_name', ''),
                "is_private": user.get('is_private', False),
                "profile_pic_url": user.get('profile_pic_url', '')
            })
            
        next_max_id = data.get('next_max_id')
        if next_max_id:
            has_next_page = True
            halaman += 1
            
            jeda = random.uniform(3.0, 7.0) # Jeda sedikit diperlama agar lebih aman
            time.sleep(jeda)
        else:
            has_next_page = False

    if semua_followers:
        print(f"\nMenyimpan {len(semua_followers)} followers ke '{NAMA_FILE_CSV}'...")
        with open(NAMA_FILE_CSV, mode='w', newline='', encoding='utf-8-sig') as file_csv:
            kolom = ["username", "full_name", "is_private", "profile_pic_url"]
            writer = csv.DictWriter(file_csv, fieldnames=kolom)
            writer.writeheader()
            for follower in semua_followers:
                writer.writerow(follower)
        print("✅ Proses selesai!")
    else:
        print("⚠ Tidak ada data yang disimpan.")

if __name__ == "__main__":
    main()