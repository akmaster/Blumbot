import pyautogui
from pynput import keyboard, mouse
import cv2
import numpy as np
import time
import threading
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, UnidentifiedImageError
import webbrowser
import os
import sys

# BOT durumu
bot_active = False
search_region = None  # Başlangıçta arama bölgesi yok
target_image_paths = [None, None]  # İki hedef resim dosya yolu
threshold = 0.8  # Varsayılan eşik değeri
start_x, start_y = None, None

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def on_click(x, y, button, pressed):
    global search_region, start_x, start_y

    if pressed and button == mouse.Button.left:
        if start_x is None and start_y is None:
            # İlk tıklama, bölgenin başlangıç koordinatlarını belirler
            start_x, start_y = x, y
            print(f"Başlangıç noktası: ({start_x}, {start_y})")
        else:
            # İkinci tıklama, bölgenin bitiş koordinatlarını belirler
            end_x, end_y = x, y
            print(f"Bitiş noktası: ({end_x}, {end_y})")

            # Arama bölgesini belirle
            width = end_x - start_x
            height = end_y - start_y
            search_region = (start_x, start_y, width, height)
            print(f"Arama bölgesi: {search_region}")

            # Fare dinleyicisini durdur
            return False

def select_region():
    print("Lütfen arama bölgesini fare ile seçin: İlk tıklama başlangıç noktası, ikinci tıklama bitiş noktası.")
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

def start_bot():
    global bot_active, search_region, target_image_paths, threshold, search_mode
    
    if not any(target_image_paths):
        messagebox.showerror("Hata", "Lütfen önce en az bir resim seçin.")
        return
    
    if not search_region:
        messagebox.showerror("Hata", "Lütfen önce bir arama bölgesi seçin.")
        return
    
    target_images = []
    try:
        for path in target_image_paths:
            if path:
                if search_mode.get() == "grayscale":
                    target_image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)  # Gri tonlamalı yükle
                else:
                    target_image = cv2.imread(path, cv2.IMREAD_COLOR)  # Renkli yükle

                if target_image is None:
                    raise ValueError(f"Hedef resim {path} yüklenemedi. Lütfen geçerli bir resim dosyası seçin.")
                
                target_images.append(target_image)

    except Exception as e:
        messagebox.showerror("Hata", f"Resim yüklenirken hata oluştu: {e}")
        return
    
    while bot_active:
        try:
            # Ekranın belirlenen bölgesinin OpenCV formatında ekran görüntüsünü al
            if search_region:
                x, y, w, h = search_region
                screenshot = pyautogui.screenshot(region=search_region)
            else:
                screenshot = pyautogui.screenshot()

            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)  # Convert PIL image to OpenCV format

            if search_mode.get() == "grayscale":
                screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            for target_image in target_images:
                # Ekran görüntüsü içinde hedef resmi arayın
                result = cv2.matchTemplate(screenshot, target_image, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                # Eşik değerini kontrol edin ve eşleşme bulunduğunda tıklayın
                if max_val >= threshold:
                    target_w, target_h = target_image.shape[1], target_image.shape[0]  # width, height
                    # Ekran bölgesine göre gerçek tıklama koordinatlarını hesapla
                    center_x = x + max_loc[0] + target_w // 2
                    center_y = y + max_loc[1] + target_h // 2
                    pyautogui.click(center_x, center_y)
                    print(f"Resim bulundu ve tıklandı ({center_x}, {center_y})")
                else:
                    print("Belirtilen resim bulunamadı.")
        
        except pyautogui.FailSafeException:
            print("PyAutoGUI failsafe triggered! Program durduruldu.")
            bot_active = False
        except Exception as e:
            print(f"Hata: {e}")

def start_bot_thread():
    global bot_active
    if not bot_active:
        bot_active = True
        threading.Thread(target=start_bot).start()

def stop_bot():
    global bot_active
    bot_active = False

def select_region_gui():
    select_region()
    messagebox.showinfo("Bölge Seçimi", "Arama bölgesi seçildi.")

def select_image(index):
    global target_image_paths
    try:
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            target_image_paths[index] = file_path
            image_path_labels[index].config(text=f"Seçilen Resim {index + 1}: {file_path}")
            update_displayed_image(index)
    except UnidentifiedImageError:
        messagebox.showerror("Hata", "Desteklenmeyen resim formatı. Lütfen geçerli bir resim dosyası seçin.")
    except Exception as e:
        messagebox.showerror("Hata", f"Resim seçilirken hata oluştu: {e}")

def update_threshold(val):
    global threshold
    threshold = float(val)
    threshold_label.config(text=f"Eşik Değeri: {threshold:.2f}")

def update_displayed_image(index):
    try:
        # Hedef resmi yükle ve küçük boyutlu göster
        img = Image.open(target_image_paths[index])
        img.thumbnail((200, 200))  # Resmi küçük boyutlu göster
        img_tk = ImageTk.PhotoImage(img)
        image_labels[index].config(image=img_tk)
        image_labels[index].image = img_tk
    except UnidentifiedImageError:
        messagebox.showerror("Hata", "Desteklenmeyen resim formatı. Lütfen geçerli bir resim dosyası seçin.")
    except Exception as e:
        messagebox.showerror("Hata", f"Resim güncellenemedi: {e}")

def on_press(key):
    try:
        if key.char == 's':
            start_bot_thread()
        elif key.char == 'q':
            stop_bot()
    except AttributeError:
        pass

def listen_keyboard():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def open_donate_link(event):
    webbrowser.open_new("https://www.papara.com/donate/AkMasterTV")

# Klavye dinleyicisini ayrı bir iş parçacığında başlat
keyboard_thread = threading.Thread(target=listen_keyboard)
keyboard_thread.daemon = True
keyboard_thread.start()

# GUI oluşturma
root = tk.Tk()
root.title("BOT Kontrol Arayüzü")

search_mode = tk.StringVar(value="grayscale")  # Varsayılan arama modu gri tonlamalı

start_button = tk.Button(root, text="BOT'u Başlat (S)", command=start_bot_thread)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="BOT'u Durdur (Q)", command=stop_bot)
stop_button.pack(pady=10)

select_button = tk.Button(root, text="Arama Bölgesini Seç", command=select_region_gui)
select_button.pack(pady=10)

image_buttons = []
image_path_labels = []
image_labels = []

for i in range(2):
    image_button = tk.Button(root, text=f"Resim Seç {i + 1}", command=lambda i=i: select_image(i))
    image_button.pack(pady=10)
    image_buttons.append(image_button)

    image_path_label = tk.Label(root, text=f"Seçilen Resim {i + 1}: Henüz seçilmedi")
    image_path_label.pack(pady=10)
    image_path_labels.append(image_path_label)

    image_label = tk.Label(root)
    image_label.pack(pady=10)
    image_labels.append(image_label)

threshold_slider = tk.Scale(root, from_=0.5, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=update_threshold)
threshold_slider.set(threshold)
threshold_slider.pack(pady=10)

threshold_label = tk.Label(root, text=f"Eşik Değeri: {threshold:.2f}")
threshold_label.pack(pady=10)

search_mode_label = tk.Label(root, text="Arama Modu:")
search_mode_label.pack(pady=10)

grayscale_radiobutton = tk.Radiobutton(root, text="Gri Tonlamalı", variable=search_mode, value="grayscale")
grayscale_radiobutton.pack()

color_radiobutton = tk.Radiobutton(root, text="Renkli", variable=search_mode, value="color")
color_radiobutton.pack()

donate_message = tk.Label(root, text="Program işinize yaradıysa beni desteklemek için donate gönderebilirsiniz", font=("Helvetica", 12))
donate_message.pack(pady=10)

donate_label = tk.Label(root, text="Buraya tıklayın", fg="blue", cursor="hand2", font=("Helvetica", 12, "bold"))
donate_label.pack(pady=5)
donate_label.bind("<Button-1>", open_donate_link)

root.mainloop()
