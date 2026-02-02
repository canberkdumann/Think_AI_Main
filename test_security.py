import json
import os

def check_last_memory():
    file_path = "conversation_memory.jsonl"
    
    if not os.path.exists(file_path):
        print("❌ HATA: conversation_memory.jsonl dosyası bulunamadı.")
        print("   -> Önce projeyi çalıştırıp (python gradio_ui.py) yapay zekaya bir mesaj yazmalısın.")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                print("⚠️ Hafıza dosyası boş.")
                return

            last_entry = json.loads(lines[-1])
            print("\n--- SON HAFIZA KAYDI ---")
            print(f"Kullanıcı Girdisi (Log): {last_entry["user"]}")
            
            if "[CONFIDENTIAL" in last_entry["user"]:
                print("\n✅ BAŞARILI: Hassas veri maskelenmiş!")
            else:
                print("\n⚠️ BİLGİ: Maskelenecek hassas veri bulunamadı veya maskeleme çalışmadı.")
                print("   (Eğer mesajında telefon/email yoksa bu normaldir.)")
                
    except Exception as e:
        print(f"Bir hata oluştu: {e}")

if __name__ == "__main__":
    check_last_memory()

