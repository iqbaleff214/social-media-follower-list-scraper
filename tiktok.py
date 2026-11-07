from playwright.sync_api import sync_playwright
import csv
import time
import os

# Konfigurasi
TARGET_USERNAME = "iqbaleff214"
NAMA_FILE_CSV = "followers_tiktok.csv"
STATE_FILE = "tiktok_state.json" # File untuk menyimpan session/login

semua_followers = []
username_tercatat = set()

def tangkap_response(response):
    if "api/user/follower/list" in response.url and response.status == 200:
        try:
            data = response.json()
            user_list = data.get("userList", [])
            for item in user_list:
                username = item.get("user", {}).get("uniqueId", "")
                if username and username not in username_tercatat:
                    username_tercatat.add(username)
                    semua_followers.append({
                        "username": username,
                        "nama": item.get("user", {}).get("nickname", ""),
                        "foto": item.get("user", {}).get("avatarThumb", "")
                    })
            print(f"📥 Ditangkap {len(user_list)} data. Total: {len(semua_followers)}")
        except:
            pass

def main():
    print("🚀 Memulai TikTok Server Scraper...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Tetap False untuk kelabuhi anti-bot
        
        # Cek apakah file sesi login sudah ada
        if os.path.exists(STATE_FILE):
            print("Memuat sesi login yang tersimpan...")
            context = browser.new_context(storage_state=STATE_FILE)
        else:
            print("Membuat sesi baru...")
            context = browser.new_context()
            
        page = context.new_page()
        page.on("response", tangkap_response)

        # 1. Buka halaman target
        page.goto(f"https://www.tiktok.com/@{TARGET_USERNAME}")
        page.wait_for_timeout(5000) # Tunggu loading awal

        # Jika ini pertama kali jalan di server, kamu mungkin harus memancingnya 
        # dengan login manual dulu (dijelaskan di bawah)
        
        # 2. Otomatis klik tombol Followers
        try:
            print("Mencari tombol followers...")
            page.locator(f'a[href="/@{TARGET_USERNAME}/followers"]').click()
            page.wait_for_timeout(3000)
        except Exception as e:
            print("Gagal mengklik tombol followers (mungkin butuh login atau UI berubah).")
            browser.close()
            return

        # 3. AUTO-SCROLL LOGIC
        print("Mulai auto-scroll...")
        # Mencari elemen pop-up followers (TikTok sering ganti nama class-nya)
        # Tapi secara umum kita bisa arahkan mouse ke tengah layar dan putar roda mouse
        
        scroll_attempts = 0
        max_scrolls = 50 # Batasi agar tidak infinite loop (sesuaikan dengan target)
        
        while scroll_attempts < max_scrolls:
            # Posisikan mouse di tengah layar (area pop-up) lalu scroll ke bawah
            page.mouse.move(500, 500) 
            page.mouse.wheel(0, 2000) # Scroll ke bawah sejauh 2000 pixel
            page.wait_for_timeout(3000) # Jeda untuk biarkan API memuat data baru
            
            scroll_attempts += 1
            # Note: Dalam kasus nyata, kamu butuh logika untuk mengecek apakah
            # data baru masih masuk atau sudah mentok bawah.
            
        # Simpan sesi login terbaru sebelum ditutup
        context.storage_state(path=STATE_FILE)
        browser.close()

    # Menyimpan CSV
    if semua_followers:
        print(f"💾 Menyimpan {len(semua_followers)} followers ke CSV...")
        with open(NAMA_FILE_CSV, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=["username", "nama", "foto"])
            writer.writeheader()
            writer.writerows(semua_followers)
        print("✅ Proses selesai!")

if __name__ == "__main__":
    main()