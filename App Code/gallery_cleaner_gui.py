import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import threading
from gallery_classifier import GalleryClassifier

# Tambahkan import ini untuk kesadaran DPI
import ctypes
import sys

class GalleryCleanerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gallery Cleaner")
        self.root.geometry("800x600")  # Ukuran jendela diperbesar
        self.root.resizable(True, True)
        
        # Set skala yang sesuai untuk tampilan DPI tinggi
        try:
            if sys.platform.startswith('win'):
                # Dapatkan DPI sistem dan set skala yang sesuai
                # Alih-alih memaksa 1.0, kita akan menggunakan nilai yang lebih sesuai
                import ctypes
                user32 = ctypes.windll.user32
                screen_width = user32.GetSystemMetrics(0)
                screen_height = user32.GetSystemMetrics(1)
                
                # Hitung skala yang sesuai (berdasarkan standar 96 DPI umum)
                scaling_factor = max(1.5, screen_width / 1920)  # Gunakan setidaknya 1.5 atau skala berdasarkan lebar
                self.root.tk.call('tk', 'scaling', scaling_factor)
                print(f"Setting scaling factor to: {scaling_factor}")
        except Exception as e:
            print(f"Could not set DPI scaling: {e}")
            
        # Coba gunakan tema yang lebih modern jika tersedia
        try:
            self.style = ttk.Style()
            if 'clam' in self.style.theme_names():
                self.style.theme_use('clam')  # Gunakan tema yang lebih bersih
            
            # Konfigurasi ukuran font untuk keterbacaan yang lebih baik - JAUH lebih besar sekarang
            default_font = ('Segoe UI', 14)  # Ditingkatkan dari 10
            heading_font = ('Segoe UI', 18, 'bold')  # Ditingkatkan dari 12
            title_font = ('Segoe UI', 24, 'bold')  # Font judul lebih besar
            
            self.style.configure('TLabel', font=default_font)
            self.style.configure('TButton', font=default_font)
            self.style.configure('TEntry', font=default_font)
            self.style.configure('TLabelframe.Label', font=heading_font)
            
            # Buat tombol lebih besar
            self.style.configure('TButton', padding=(10, 5))
            
            # Konfigurasi widget entry agar lebih tinggi
            self.style.configure('TEntry', padding=(5, 8))
            
            # Buat frame lebih padded
            self.style.configure('TFrame', padding=8)
            self.style.configure('TLabelframe', padding=10)
        except Exception as e:
            print(f"Could not set theme: {e}")
        
        # Variabel-variabel
        self.folder_path = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_text = tk.StringVar()
        self.status_text.set("Loading model...")
        
        # Variabel pemilihan kategori
        self.category_vars = {}
        self.category_labels = ["foods", "landscape", "people", "receipts", "screenshots"]
        for category in self.category_labels:
            self.category_vars[category] = tk.BooleanVar(value=True)
        
        # Buat instance classifier
        self.classifier = GalleryClassifier(
            on_progress_update=self.update_progress,
            on_status_update=self.update_status_text,
            on_image_classified=self.log_classification,
            on_error=self.log_error,
            on_complete=self.classification_complete
        )
        
        # Buat elemen GUI
        self.create_widgets()
        
        # Muat model dalam thread terpisah
        self.load_model_thread = threading.Thread(target=self.load_model)
        self.load_model_thread.daemon = True
        self.load_model_thread.start()
    
    def create_widgets(self):
        # Buat frame utama
        main_frame = ttk.Frame(self.root, padding="20")  # Padding diperbesar
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Judul
        title_label = ttk.Label(main_frame, text="Gallery Cleaner", font=("Helvetica", 24, "bold"))  # Ditingkatkan dari 16
        title_label.pack(pady=15)  # Padding diperbesar
        
        # Deskripsi
        desc_label = ttk.Label(main_frame, text="Pilih folder untuk klasifikasi dan urutkan gambar ke dalam kategori")
        desc_label.pack(pady=10)  # Padding diperbesar
        
        # Frame pemilihan folder
        folder_frame = ttk.LabelFrame(main_frame, text="Sumber Gambar", padding=15)  # Padding diperbesar
        folder_frame.pack(fill=tk.X, padx=15, pady=15)  # Padding diperbesar
        
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path, width=50)
        folder_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)  # Padding diperbesar
        
        browse_button = ttk.Button(folder_frame, text="Browse...", command=self.browse_folder)
        browse_button.pack(side=tk.RIGHT, padx=10)  # Padding diperbesar
        
        # Frame pemilihan kategori
        category_frame = ttk.LabelFrame(main_frame, text="Kategori yang Akan Diekstrak", padding=15)
        category_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Buat dua kolom checkbox untuk tata letak yang lebih baik
        left_column = ttk.Frame(category_frame)
        left_column.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        right_column = ttk.Frame(category_frame)
        right_column.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Tambahkan checkbox untuk setiap kategori
        for i, category in enumerate(self.category_labels):
            # Alternatif antara kolom kiri dan kanan
            parent_frame = left_column if i < (len(self.category_labels) + 1) // 2 else right_column
            
            # Buat style yang lebih besar untuk checkbutton
            self.style.configure('Large.TCheckbutton', 
                                font=('Segoe UI', 14),  # Ukuran font ditingkatkan
                                padding=10)  # Padding ditingkatkan
            
            chk = ttk.Checkbutton(
                parent_frame, 
                text=category.capitalize(), 
                variable=self.category_vars[category],
                style='Large.TCheckbutton'  # Terapkan style yang lebih besar
            )
            chk.pack(anchor=tk.W, pady=8)  # Padding vertikal ditingkatkan antara checkbox
        
        # Tombol Pilih/Tidak Pilih semua
        select_buttons_frame = ttk.Frame(category_frame)
        select_buttons_frame.pack(fill=tk.X, pady=10)
        
        select_all_btn = ttk.Button(
            select_buttons_frame, 
            text="Pilih Semua", 
            command=self.select_all_categories,
            padding=(5, 2)
        )
        select_all_btn.pack(side=tk.LEFT, padx=10)
        
        deselect_all_btn = ttk.Button(
            select_buttons_frame, 
            text="Tidak Pilih Semua", 
            command=self.deselect_all_categories,
            padding=(5, 2)
        )
        deselect_all_btn.pack(side=tk.LEFT, padx=10)
        
        # Frame kontrol
        controls_frame = ttk.Frame(main_frame, padding=15)  # Padding diperbesar
        controls_frame.pack(fill=tk.X, padx=15, pady=10)  # Padding diperbesar
        
        self.start_button = ttk.Button(controls_frame, text="Mulai Klasifikasi", 
                                     command=self.start_classification, state="disabled")
        self.start_button.pack(side=tk.LEFT, padx=10)  # Padding diperbesar
        
        # Frame progress
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=15)  # Padding diperbesar
        progress_frame.pack(fill=tk.X, padx=15, pady=10)  # Padding diperbesar
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, 
                                          length=100, mode='determinate', 
                                          variable=self.progress_var)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=10)  # Padding diperbesar
        
        status_label = ttk.Label(progress_frame, textvariable=self.status_text)
        status_label.pack(fill=tk.X, padx=10)  # Padding diperbesar
        
        # Frame hasil
        results_frame = ttk.LabelFrame(main_frame, text="Hasil", padding=15)  # Padding diperbesar
        results_frame.pack(fill=tk.BOTH, padx=15, pady=15, expand=True)  # Padding diperbesar
        
        # Konfigurasi ukuran font teks hasil
        self.result_text = tk.Text(results_frame, wrap=tk.WORD, font=('Segoe UI', 12))  # Ukuran font ditingkatkan
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        
        # self.result_text.insert(tk.END, "Ready to classify images. The model will sort images into these categories:\n")
        # self.result_text.insert(tk.END, "- foods\n- landscape\n- people\n- receipts\n- screenshots\n\n")
        self.result_text.insert(tk.END, "Silakan pilih folder dan klik 'Mulai Klasifikasi'.\n")
    
    def select_all_categories(self):
        """Pilih semua checkbox kategori"""
        for category in self.category_labels:
            self.category_vars[category].set(True)
    
    def deselect_all_categories(self):
        """Tidak pilih semua checkbox kategori"""
        for category in self.category_labels:
            self.category_vars[category].set(False)
    
    def load_model(self):
        try:
            self.classifier.load_model("resnet50_pretrained_not-frozen.keras")
            self.root.after(0, self.model_loaded)
        except Exception as e:
            self.root.after(0, lambda: self.model_load_error(str(e)))
    
    def model_loaded(self):
        self.status_text.set("Model berhasil dimuat. Siap untuk klasifikasi gambar.")
        self.start_button.config(state="normal")
    
    def model_load_error(self, error_message):
        self.status_text.set("Error saat memuat model.")
        messagebox.showerror("Error Memuat Model", f"Gagal memuat model: {error_message}")
    
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
    
    def start_classification(self):
        folder = self.folder_path.get()
        if not folder:
            messagebox.showwarning("Folder Belum Dipilih", "Silakan pilih folder yang berisi gambar.")
            return
        
        # Dapatkan kategori yang dipilih
        selected_categories = [category for category, var in self.category_vars.items() if var.get()]
        
        if not selected_categories:
            messagebox.showwarning("Kategori Belum Dipilih", "Silakan pilih setidaknya satu kategori untuk diekstrak.")
            return
        
        # Bersihkan hasil sebelumnya
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"Memulai klasifikasi di {folder}...\n")
        self.result_text.insert(tk.END, f"Kategori yang dipilih: {', '.join(selected_categories)}\n\n")
        
        # Reset progress bar
        self.progress_var.set(0)
        self.status_text.set("Memproses...")
        
        # Nonaktifkan tombol mulai selama pemrosesan
        self.start_button.config(state="disabled")
        
        # Mulai klasifikasi dalam thread terpisah dengan kategori yang dipilih
        threading.Thread(
            target=self.classifier.process_folder, 
            args=(folder, selected_categories), 
            daemon=True
        ).start()
    
    # Metode callback untuk classifier
    def update_progress(self, progress_value):
        self.root.after(0, lambda: self.progress_var.set(progress_value))
    
    def update_status_text(self, text):
        self.root.after(0, lambda: self.status_text.set(text))
    
    def log_classification(self, file_name, predicted_class, confidence):
        self.root.after(0, lambda: self.log_result(
            f"Gambar '{file_name}' diklasifikasikan sebagai {predicted_class} (kepercayaan: {confidence:.2f})"))
    
    def log_error(self, file_name, error_message):
        self.root.after(0, lambda: self.log_result(f"Error memproses '{file_name}': {error_message}"))
    
    def classification_complete(self, category_counts, processed, total):
        self.root.after(0, lambda: self.show_summary(category_counts, processed, total))
        self.root.after(0, lambda: self.update_status_text(f"Selesai! {processed} gambar diurutkan ke dalam kategori."))
        self.root.after(0, lambda: self.start_button.config(state="normal"))
        self.root.after(0, lambda: self.progress_var.set(100))
    
    def log_result(self, message):
        self.result_text.insert(tk.END, message + "\n")
        self.result_text.see(tk.END)
    
    def show_summary(self, category_counts, processed, total):
        summary = "\n----- Ringkasan Klasifikasi -----\n"
        for category, count in category_counts.items():
            if processed > 0:
                percentage = (count / processed) * 100
                summary += f"{category}: {count} gambar ({percentage:.1f}%)\n"
            else:
                summary += f"{category}: 0 gambar (0%)\n"
        
        summary += f"\nTotal: {processed} dari {total} gambar diproses dan diurutkan."
        self.log_result(summary)

def main():
    # Aktifkan kesadaran DPI sebelum membuat jendela utama, tetapi dengan pendekatan yang lebih baik
    if sys.platform.startswith('win'):
        try:
            # Untuk Windows 8.1 dan yang lebih baru - gunakan kesadaran DPI per-monitor
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Diubah dari 1 menjadi 2 untuk kesadaran per-monitor
        except AttributeError:
            # Untuk Windows 7 dan yang lebih lama
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception as e:
            print(f"Failed to set DPI awareness: {e}")
    
    root = tk.Tk()
    app = GalleryCleanerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

