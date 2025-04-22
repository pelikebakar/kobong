from playwright.sync_api import Playwright, sync_playwright
from datetime import datetime
import pytz
import requests
import os

userid = os.getenv("userid")
pw = os.getenv("pw")
telegram_token = os.getenv("TELEGRAM_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

wib = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M WIB")

def log_status(emoji: str, message: str):
    print(f"{emoji} {message}")

def baca_file(file_name: str) -> str:
    with open(file_name, 'r') as file:
        return file.read().strip()

def kirim_telegram_log(status: str, pesan: str):
    print(pesan)
    if telegram_token and telegram_chat_id:
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                data={
                    "chat_id": telegram_chat_id,
                    "text": pesan,
                    "parse_mode": "HTML"
                }
            )
            if response.status_code != 200:
                print(f"Gagal kirim ke Telegram. Status: {response.status_code}")
                print(f"Respon Telegram: {response.text}")
        except Exception as e:
            print("Error saat mengirim ke Telegram:", e)
    else:
        print("Token atau chat_id tidak tersedia.")

def parse_saldo(saldo_text: str) -> float:
    print("🧪 SALDO RAW:", saldo_text)
    saldo_text = saldo_text.replace("Rp.", "").replace("Rp", "").strip()
    saldo_text = saldo_text.replace(",", "")  # Hapus koma (ribuan)
    print("🧪 SALDO CLEANED:", saldo_text)
    return float(saldo_text)


def run(playwright: Playwright) -> None:
    try:
        log_status("📂", "Membaca file nomor & bet...")
        nomor_kombinasi = baca_file("nomor.txt")
        bet_raw = baca_file("bet.txt")
        bet_kali = float(bet_raw)
        jumlah_kombinasi = len(nomor_kombinasi.split('*'))
        total_bet_rupiah = jumlah_kombinasi * bet_kali * 1000
        log_status("📬", f"Nomor ditemukan: {nomor_kombinasi} | Bet: {bet_raw}")

        log_status("🌐", "Membuka browser...")
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://wdbos39652.com/#/index?category=lottery")
        page.get_by_role("img", name="close").click()

        with page.expect_popup() as popup_info:
            page.get_by_role("heading", name="HOKI DRAW").click()
        page1 = popup_info.value

        log_status("🔐", "Login ke akun...")
        page1.locator("input#loginUser").wait_for()
        page1.locator("input#loginUser").fill(userid)
        page1.locator("input#loginPsw").wait_for()
        page1.locator("input#loginPsw").fill(pw)
        page1.locator("div.login-btn").wait_for()
        page1.locator("div.login-btn").click()

        try:
            page1.get_by_role("link", name="Saya Setuju").wait_for(timeout=10000)
            page1.get_by_role("link", name="Saya Setuju").click()
        except:
            print("⚠️ Tombol 'Saya Setuju' tidak muncul, lanjut...")

        # 💰 Cek saldo awal
        try:
            saldo_text = page1.locator("span.overage-num").inner_text().strip()
            saldo_value = parse_saldo(saldo_text)
        except Exception as e:
            saldo_text = "tidak diketahui"
            saldo_value = 0.0
            print("⚠️ Gagal ambil saldo:", e)

        log_status("🧭", "Navigasi ke 5D Fast...")
        page1.locator("a[data-urlkey='5dFast']").wait_for()
        page1.locator("a[data-urlkey='5dFast']").click()
        page1.locator("li.mode_full[data-tabkey='full']").wait_for()
        page1.locator("li.mode_full[data-tabkey='full']").click()

        log_status("🧾", "Mengisi form taruhan...")
        page1.locator("textarea#numinput").wait_for()
        page1.locator("textarea#numinput").fill(nomor_kombinasi)
        page1.locator("input#buy3d").wait_for()
        page1.locator("input#buy3d").fill(str(bet_raw))

        log_status("📨", "Mengirim taruhan...")
        page1.locator("button.jq-bet-submit").wait_for()
        page1.locator("button.jq-bet-submit").click()

        log_status("⏳", "Menunggu konfirmasi dari sistem...")
        try:
            page1.wait_for_selector("text=Bettingan anda berhasil dikirim.", timeout=15000)
            betting_berhasil = True
        except:
            betting_berhasil = False

        # 💰 Cek saldo setelah betting
        try:
            saldo_text = page1.locator("span.overage-num").inner_text().strip()
            saldo_value = parse_saldo(saldo_text)
        except Exception as e:
            saldo_text = "tidak diketahui"
            saldo_value = 0.0
            print("⚠️ Gagal ambil saldo:", e)

        if betting_berhasil:
            pesan_sukses = (
                "<b>[SUKSES]</b>\n"
                f"🎯 <b>{jumlah_kombinasi}</b> kombinasi\n"
                f"💸 Rp. <b>{total_bet_rupiah:,.0f}</b>\n"
                f"💰SALDO KAMU Rp. <b>{saldo_value:,.2f}</b>\n"
                f"⌚ {wib}"
            )
            log_status("✅", pesan_sukses)
            kirim_telegram_log("SUKSES", pesan_sukses)
        else:
            pesan_gagal = (
                "<b>[GAGAL]</b>\n"
                f"❌ Gagal❗\n"
                f"💸 Rp. <b>{total_bet_rupiah:,.0f}</b>\n"
                f"💰 SALDO KAMU Rp. <b>{saldo_value:,.2f}</b>\n"
                f"⌚ {wib}"
            )
            log_status("❌", pesan_gagal)
            kirim_telegram_log("GAGAL", pesan_gagal)

        context.close()
        browser.close()

    except Exception as e:
        log_status("❌", "Terjadi kesalahan saat menjalankan script.")
        print("Detail error:", e)
        kirim_telegram_log("GAGAL", f"<b>[GAGAL]</b>\n❌ Error: {str(e)}\n⌚ {wib}")

with sync_playwright() as playwright:
    run(playwright)
