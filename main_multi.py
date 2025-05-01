
from playwright.sync_api import Playwright, sync_playwright
from datetime import datetime
import pytz
import requests
import os

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
    saldo_text = saldo_text.replace("Rp.", "").replace("Rp", "").strip().replace(",", "")
    return float(saldo_text)

def run(playwright: Playwright, situs: str, userid: str, bet_raw: str):
    try:
        nomor_kombinasi = baca_file("nomor.txt")
        bet_kali = float(bet_raw)
        jumlah_kombinasi = len(nomor_kombinasi.split('*'))
        bet_per_nomor = bet_kali * 1000
        total_bet_rupiah = jumlah_kombinasi * bet_kali * 1000

        log_status("🌐", f"Login ke situs {situs} dengan userid {userid}...")
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"https://{situs}/#/index?category=lottery")

        page.get_by_role("img", name="close").click()
        with page.expect_popup() as popup_info:
            page.get_by_role("heading", name="HOKI DRAW").click()
        page1 = popup_info.value

        page1.locator("input#loginUser").wait_for()
        page1.locator("input#loginUser").fill(userid)
        page1.locator("input#loginPsw").fill(pw)
        page1.locator("div.login-btn").click()

        try:
            page1.get_by_role("link", name="Saya Setuju").wait_for(timeout=10000)
            page1.get_by_role("link", name="Saya Setuju").click()
        except:
            pass

        try:
            saldo_text = page1.locator("span.overage-num").inner_text().strip()
            saldo_value = parse_saldo(saldo_text)
        except:
            saldo_text = "tidak diketahui"
            saldo_value = 0.0

        page1.locator("a[data-urlkey='5dFast']").click()
        for _ in range(5):
            page1.get_by_text("FULL", exact=True).click()

        page1.locator("#numinput").fill(nomor_kombinasi)
        page1.locator("input#buy3d").fill(str(bet_raw))
        page1.locator("button.jq-bet-submit").click()

        try:
            page1.wait_for_selector("text=Bettingan anda berhasil dikirim.", timeout=15000)
            betting_berhasil = True
        except:
            betting_berhasil = False

        try:
            saldo_text = page1.locator("span.overage-num").inner_text().strip()
            saldo_value = parse_saldo(saldo_text)
        except:
            saldo_value = 0.0

        if betting_berhasil:
            pesan_sukses = (
                f"<b>[SUKSES]</b>\n"
                f"👤 {userid}\n"
                f"🎯 TOTAL <b>{jumlah_kombinasi}</b> HARGA <b>{int(bet_per_nomor):,}</b>\n"
                f"💸 BAYAR Rp. <b>{total_bet_rupiah:,.0f}</b>\n"
                f"💰 SALDO KAMU Rp. <b>{saldo_value:,.0f}</b>\n"
                f"⌚ {wib}"
            )
            kirim_telegram_log("SUKSES", pesan_sukses)
        else:
            pesan_gagal = (
                f"<b>[GAGAL]</b>\n"
                f"👤 {userid}\n"
                f"💸 BAYAR Rp. <b>{total_bet_rupiah:,.0f}</b>\n"
                f"💰 SALDO KAMU Rp. <b>{saldo_value:,.0f}</b>\n"
                f"⌚ {wib}"
            )
            kirim_telegram_log("GAGAL", pesan_gagal)

        context.close()
        browser.close()
    except Exception as e:
        kirim_telegram_log("GAGAL", f"<b>[ERROR]</b>\n{userid}@{situs}\n❌ {str(e)}\n⌚ {wib}")

def main():
    bets = baca_file("bet.txt").splitlines()
    with sync_playwright() as playwright:
        for baris in bets:
            if '|' not in baris:
                continue
            parts = baris.strip().split('|')
            if len(parts) != 3:
                continue
            situs, userid, bet_raw = parts
            run(playwright, situs.strip(), userid.strip(), bet_raw.strip())

if __name__ == "__main__":
    main()
