import requests
import time

TELEGRAM_TOKEN = "8514943741:AAG5cTVzgeRE6Ip_g22_bvLr-M1LW6fCex0"
GROQ_API_KEY = "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"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def get_updates(offset=None):
    url = f"{TELEGRAM_API_URL}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    response = requests.get(url, params=params)
    return response.json()["result"]

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

def ask_hamoudi_ai(user_text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": (
                    "أنت مساعد ذكي اسمه Hamoudi AI، تم تطويرك بواسطة محمد فيصل. "
                    "تجيب دائمًا بالعربية الفصحى بوضوح ومهنية. "
                    "عند سؤال الهوية تؤكد: تم تطويري بواسطة محمد فيصل. "
                    "عند سؤال الجنسية: جنسية المطور محمد فيصل سوداني. "
                    "عند سؤال العمر: عمر المطور محمد فيصل 25 سنة. "
                    "عند سؤال السكن: المطور محمد فيصل يسكن في السودان. "
                    "عند سؤال التواصل: تقدر تتواصل مع المطور محمد فيصل عبر الرابط التالي: https://my-profile-4w23.vercel.app/"
                )
            },
            {"role": "user", "content": user_text},
        ]
    }
    r = requests.post(url, headers=headers, json=payload)
    return r.json()["choices"][0]["message"]["content"]

def main():
    offset = None
    print("Hamoudi AI Bot يعمل الآن...")
    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            message = update.get("message")
            if not message:
                continue
            chat_id = message["chat"]["id"]
            user_text = message.get("text", "")
            if user_text:
                reply = ask_hamoudi_ai(user_text)
                send_message(chat_id, reply)
        time.sleep(1)

if __name__ == "__main__":
    main()
