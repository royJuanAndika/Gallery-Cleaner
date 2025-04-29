import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import threading
import sys
import ctypes
from optimized_classifier import OptimizedClassifier
from model_optimizer import ModelOptimizer

class LiteGalleryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gallery Cleaner Lite")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Aktifin high DPI awareness
        self.enable_dpi_awareness()
        
        # Set up style dan skala UI
        self.setup_styling()
        
        # Variabel-variabel
        self.folder_path = tk.StringVar()
        self.model_path = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_text = tk.StringVar()
        self.status_text.set("Pilih model dulu ya...")
        self.model_type = tk.StringVar(value="optimized")  # "original" atau "optimized"
        
        # Variabel pilihan kategori
        self.category_vars = {}
        self.category_labels = ["foods", "landscape", "people", "receipts", "screenshots"]
        for category in self.category_labels:
            self.category_vars[category] = tk.BooleanVar(value=True)
        
        # Bikin instance classifier
        self.classifier = OptimizedClassifier(
            on_progress_update=self.update_progress,
            on_status_update=self.update_status_text,
            on_image_classified=self.log_classification,
            on_error=self.log_error,
            on_complete=self.classification_complete
        )
        
        # Bikin model optimizer
        self.optimizer = ModelOptimizer()
        
        # Bikin elemen GUI
        self.create_widgets()
    
    def enable_dpi_awareness(self):
        """Aktifin DPI awareness buat layar resolusi tinggi"""
        try:
            if sys.platform.startswith('win'):
                # Buat Windows 8.1 ke atas - pake per-monitor DPI awareness
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
                
                # Hitung skala yang pas
                user32 = ctypes.windll.user32
                screen_width = user32.GetSystemMetrics(0)
                scaling_factor = max(1.0, screen_width / 1920)
                self.root.tk.call('tk', 'scaling', scaling_factor)
        except Exception as e:
            print(f"Gagal set DPI awareness: {e}")
    
    def setup_styling(self):
        """Set up styling ttk dan ukuran font"""
        try:
            self.style = ttk.Style()
            if 'clam' in self.style.theme_names():
                self.style.theme_use('clam')
            
            # Konfigurasi ukuran font - dibesarin biar jelas
            default_font = ('Segoe UI', 14)
            heading_font = ('Segoe UI', 16, 'bold')
            title_font = ('Segoe UI', 22, 'bold')
            
            self.style.configure('TLabel', font=default_font)
            self.style.configure('TButton', font=default_font)
            self.style.configure('TEntry', font=default_font)
            self.style.configure('TCheckbutton', font=default_font)
            self.style.configure('TRadiobutton', font=default_font)
            self.style.configure('TLabelframe.Label', font=heading_font)
            
            # Bikin tombol lebih gede
            self.style.configure('TButton', padding=(10, 6))
            
            # Konfigurasi entry widget biar lebih tinggi
            self.style.configure('TEntry', padding=(8, 10))
            
            # Bikin frame lebih padded
            self.style.configure('TFrame', padding=12)
            self.style.configure('TLabelframe', padding=15)
            
            # Aplikasikan ke tab Notebook
            self.style.configure('TNotebook.Tab', font=default_font, padding=(12, 6))
        except Exception as e:
            print(f"Gagal set tema: {e}")
    
    def create_widgets(self):
        # Bikin notebook buat tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Bikin tab utama
        main_tab = ttk.Frame(notebook)
        notebook.add(main_tab, text="Klasifikasi")
        
        # Bikin tab optimasi
        optimization_tab = ttk.Frame(notebook)
        notebook.add(optimization_tab, text="Optimasi Model")
        
        # Set up tab utama
        self.setup_main_tab(main_tab)
        
        # Set up tab optimasi
        self.setup_optimization_tab(optimization_tab)
    
    def setup_main_tab(self, parent):
        # Judul
        title_label = ttk.Label(parent, text="Gallery Cleaner Lite", font=("Helvetica", 22, "bold"))
        title_label.pack(pady=15)
        
        # Frame pilihan model
        model_frame = ttk.LabelFrame(parent, text="Pilihan Model", padding=15)
        model_frame.pack(fill=tk.X, padx=15, pady=8)
        
        model_entry = ttk.Entry(model_frame, textvariable=self.model_path, width=50)
        model_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_model_btn = ttk.Button(model_frame, text="Cari...", command=self.browse_model)
        browse_model_btn.pack(side=tk.RIGHT, padx=5)
        
        # Frame pilihan folder
        folder_frame = ttk.LabelFrame(parent, text="Sumber Gambar", padding=15)
        folder_frame.pack(fill=tk.X, padx=15, pady=8)
        
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path, width=50)
        folder_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_folder_btn = ttk.Button(folder_frame, text="Cari...", command=self.browse_folder)
        browse_folder_btn.pack(side=tk.RIGHT, padx=5)
        
        # Frame pilihan kategori
        category_frame = ttk.LabelFrame(parent, text="Kategori yang Mau Diekstrak", padding=15)
        category_frame.pack(fill=tk.X, padx=15, pady=8)
        
        # Bikin grid buat checkboxes
        for i, category in enumerate(self.category_labels):
            chk = ttk.Checkbutton(
                category_frame, 
                text=category.capitalize(), 
                variable=self.category_vars[category]
            )
            row, col = divmod(i, 3)
            chk.grid(row=row, column=col, sticky=tk.W, padx=10, pady=5)
        
        # Tombol Pilih/Batal Pilih
        select_buttons_frame = ttk.Frame(category_frame)
        select_buttons_frame.grid(row=2, column=0, columnspan=3, pady=5)
        
        select_all_btn = ttk.Button(select_buttons_frame, text="Pilih Semua", command=self.select_all_categories)
        select_all_btn.pack(side=tk.LEFT, padx=5)
        
        deselect_all_btn = ttk.Button(select_buttons_frame, text="Batal Pilih Semua", command=self.deselect_all_categories)
        deselect_all_btn.pack(side=tk.LEFT, padx=5)
        
        # Frame kontrol
        controls_frame = ttk.Frame(parent, padding=15)
        controls_frame.pack(fill=tk.X, padx=15, pady=8)
        
        self.start_button = ttk.Button(controls_frame, text="Mulai Klasifikasi", 
                                    command=self.start_classification)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Frame progress
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding=15)
        progress_frame.pack(fill=tk.X, padx=15, pady=8)
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, 
                                          length=100, mode='determinate', 
                                          variable=self.progress_var)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        status_label = ttk.Label(progress_frame, textvariable=self.status_text)
        status_label.pack(fill=tk.X, padx=5)
        
        # Frame hasil
        results_frame = ttk.LabelFrame(parent, text="Hasil", padding=15)
        results_frame.pack(fill=tk.BOTH, padx=15, pady=8, expand=True)
        
        self.result_text = tk.Text(results_frame, wrap=tk.WORD, font=('Segoe UI', 11))
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        
        self.result_text.insert(tk.END, "Selamat datang di Gallery Cleaner Lite!\n\n")
        self.result_text.insert(tk.END, "1. Pilih file model (.keras, .tflite, atau .onnx)\n")
        self.result_text.insert(tk.END, "2. Pilih folder gambar yang mau diproses\n")
        self.result_text.insert(tk.END, "3. Pilih kategori yang mau diekstrak\n")
        self.result_text.insert(tk.END, "4. Klik 'Mulai Klasifikasi'\n\n")
        self.result_text.insert(tk.END, "Ke tab Optimasi Model buat convert model kamu ke format yang lebih cepat.\n")
    
    def setup_optimization_tab(self, parent):
        # Judul
        title_label = ttk.Label(parent, text="Optimasi Model", font=("Helvetica", 22, "bold"))
        title_label.pack(pady=15)
        
        # Deskripsi
        desc_label = ttk.Label(parent, text="Convert model kamu ke format yang dioptimasi biar inferencenya lebih cepat")
        desc_label.pack(pady=8)
        
        # Frame model input
        input_frame = ttk.LabelFrame(parent, text="Model Input", padding=15)
        input_frame.pack(fill=tk.X, padx=15, pady=8)
        
        self.input_model_path = tk.StringVar()
        input_entry = ttk.Entry(input_frame, textvariable=self.input_model_path, width=50)
        input_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_input_btn = ttk.Button(input_frame, text="Cari...", 
                                     command=lambda: self.browse_file(self.input_model_path, 
                                                                    [("Model Keras", "*.keras *.h5")]))
        browse_input_btn.pack(side=tk.RIGHT, padx=5)
        
        # Frame opsi optimasi
        options_frame = ttk.LabelFrame(parent, text="Opsi Optimasi", padding=15)
        options_frame.pack(fill=tk.X, padx=15, pady=8)
        
        # Pilihan format target
        format_frame = ttk.Frame(options_frame)
        format_frame.pack(fill=tk.X, pady=8)
        
        format_label = ttk.Label(format_frame, text="Format Target:")
        format_label.pack(side=tk.LEFT, padx=5)
        
        self.target_format = tk.StringVar(value="tflite")
        tflite_radio = ttk.Radiobutton(format_frame, text="TensorFlow Lite", 
                                      variable=self.target_format, value="tflite")
        tflite_radio.pack(side=tk.LEFT, padx=10)
        
        onnx_radio = ttk.Radiobutton(format_frame, text="ONNX", 
                                   variable=self.target_format, value="onnx")
        onnx_radio.pack(side=tk.LEFT, padx=10)
        
        # Opsi kuantisasi
        quant_frame = ttk.Frame(options_frame)
        quant_frame.pack(fill=tk.X, pady=8)
        
        self.quantize = tk.BooleanVar(value=False)
        quant_check = ttk.Checkbutton(quant_frame, text="Aktifin Kuantisasi (ukuran lebih kecil, akurasi mungkin turun)", 
                                     variable=self.quantize)
        quant_check.pack(side=tk.LEFT, padx=5)
        
        # Dataset representatif buat kuantisasi
        rep_dataset_frame = ttk.Frame(options_frame)
        rep_dataset_frame.pack(fill=tk.X, pady=8)
        
        rep_label = ttk.Label(rep_dataset_frame, text="Folder Dataset Representatif (buat kuantisasi):")
        rep_label.pack(side=tk.LEFT, padx=5)
        
        self.rep_dataset_path = tk.StringVar()
        rep_entry = ttk.Entry(rep_dataset_frame, textvariable=self.rep_dataset_path, width=30)
        rep_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_rep_btn = ttk.Button(rep_dataset_frame, text="Cari...", 
                                  command=lambda: self.browse_folder_to_var(self.rep_dataset_path))
        browse_rep_btn.pack(side=tk.RIGHT, padx=5)
        
        # Setelan output
        output_frame = ttk.LabelFrame(parent, text="Setelan Output", padding=15)
        output_frame.pack(fill=tk.X, padx=15, pady=8)
        
        output_label = ttk.Label(output_frame, text="Path Model Output (opsional):")
        output_label.pack(anchor=tk.W, padx=5, pady=8)
        
        self.output_model_path = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_model_path, width=50)
        output_entry.pack(fill=tk.X, padx=5, pady=8)
        
        browse_output_btn = ttk.Button(output_frame, text="Cari...", 
                                     command=lambda: self.browse_save_file(self.output_model_path, 
                                                                         self.target_format.get()))
        browse_output_btn.pack(anchor=tk.E, padx=5, pady=8)
        
        # Kontrol
        controls_frame = ttk.Frame(parent, padding=15)
        controls_frame.pack(fill=tk.X, padx=15, pady=15)
        
        convert_btn = ttk.Button(controls_frame, text="Convert Model", 
                               command=self.convert_model)
        convert_btn.pack(side=tk.LEFT, padx=5)
        
        # Frame log
        log_frame = ttk.LabelFrame(parent, text="Log Konversi", padding=15)
        log_frame.pack(fill=tk.BOTH, padx=15, pady=8, expand=True)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=('Segoe UI', 11))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        self.log_text.insert(tk.END, "Selamat datang di Model Optimizer!\n\n")
        self.log_text.insert(tk.END, "Tool ini bantu kamu convert model ke format yang dioptimasi:\n")
        self.log_text.insert(tk.END, "• TensorFlow Lite (.tflite): Ukuran lebih kecil, lebih cepat di mobile\n")
        self.log_text.insert(tk.END, "• ONNX (.onnx): Performa lebih baik di Windows/DirectML\n\n")
        self.log_text.insert(tk.END, "Aktifin kuantisasi buat ukuran model lebih kecil tapi akurasi mungkin sedikit turun.\n")
    
    def select_all_categories(self):
        """Pilih semua checkboxes kategori"""
        for category in self.category_labels:
            self.category_vars[category].set(True)
    
    def deselect_all_categories(self):
        """Batal pilih semua checkboxes kategori"""
        for category in self.category_labels:
            self.category_vars[category].set(False)
    
    def browse_model(self):
        filetypes = [
            ("Semua File Model", "*.keras *.h5 *.tflite *.onnx"),
            ("Model Keras", "*.keras *.h5"),
            ("Model TensorFlow Lite", "*.tflite"),
            ("Model ONNX", "*.onnx")
        ]
        file_path = filedialog.askopenfilename(filetypes=filetypes)
        if file_path:
            self.model_path.set(file_path)
            self.load_selected_model()
    
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
    
    def browse_folder_to_var(self, var):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            var.set(folder_selected)
    
    def browse_file(self, var, filetypes):
        file_path = filedialog.askopenfilename(filetypes=filetypes)
        if file_path:
            var.set(file_path)
    
    def browse_save_file(self, var, format_type):
        filetypes = [("Model TensorFlow Lite", "*.tflite")] if format_type == "tflite" else [("Model ONNX", "*.onnx")]
        extension = ".tflite" if format_type == "tflite" else ".onnx"
        file_path = filedialog.asksaveasfilename(defaultextension=extension, filetypes=filetypes)
        if file_path:
            var.set(file_path)
    
    def load_selected_model(self):
        model_path = self.model_path.get()
        if not model_path:
            return
        
        self.status_text.set("Loading model...")
        self.result_text.insert(tk.END, f"Loading model dari {model_path}...\n")
        
        # Load model di thread terpisah
        threading.Thread(target=self._load_model_thread, args=(model_path,), daemon=True).start()
    
    def _load_model_thread(self, model_path):
        try:
            success = self.classifier.load_model(model_path)
            if success:
                self.root.after(0, lambda: self.status_text.set("Model berhasil di-load. Siap klasifikasi gambar."))
                self.root.after(0, lambda: self.result_text.insert(tk.END, "Model berhasil di-load!\n"))
            else:
                self.root.after(0, lambda: self.status_text.set("Gagal load model."))
                self.root.after(0, lambda: self.result_text.insert(tk.END, "Gagal load model.\n"))
        except Exception as e:
            self.root.after(0, lambda: self.status_text.set("Error loading model."))
            self.root.after(0, lambda: self.result_text.insert(tk.END, f"Error loading model: {str(e)}\n"))
    
    def start_classification(self):
        model_path = self.model_path.get()
        folder = self.folder_path.get()
        
        if not model_path:
            messagebox.showwarning("Model Belum Dipilih", "Pilih file model dulu ya.")
            return
            
        if not folder:
            messagebox.showwarning("Folder Belum Dipilih", "Pilih folder yang ada gambarnya.")
            return
        
        # Ambil kategori yang dipilih
        selected_categories = [category for category, var in self.category_vars.items() if var.get()]
        
        if not selected_categories:
            messagebox.showwarning("Kategori Belum Dipilih", "Pilih minimal satu kategori buat diekstrak.")
            return
        
        # Bersihin hasil sebelumnya
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"Mulai klasifikasi di {folder}...\n")
        self.result_text.insert(tk.END, f"Kategori yang dipilih: {', '.join(selected_categories)}\n\n")
        
        # Reset progress bar
        self.progress_var.set(0)
        self.status_text.set("Processing...")
        
        # Matiin tombol start selama processing
        self.start_button.config(state="disabled")
        
        # Mulai klasifikasi di thread terpisah dengan kategori yang dipilih
        threading.Thread(
            target=self.classifier.process_folder, 
            args=(folder, selected_categories), 
            daemon=True
        ).start()
    
    def convert_model(self):
        input_path = self.input_model_path.get()
        output_path = self.output_model_path.get() or None
        format_type = self.target_format.get()
        quantize = self.quantize.get()
        rep_dataset_path = self.rep_dataset_path.get() if quantize else None
        
        if not input_path:
            messagebox.showwarning("Model Input Belum Dipilih", "Pilih file model input dulu ya.")
            return
        
        # Bersihin log sebelumnya
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, f"Mulai konversi model...\n")
        self.log_text.insert(tk.END, f"Model input: {input_path}\n")
        self.log_text.insert(tk.END, f"Format target: {format_type}\n")
        self.log_text.insert(tk.END, f"Kuantisasi: {'Aktif' if quantize else 'Mati'}\n\n")
        
        # Mulai konversi di thread terpisah
        threading.Thread(
            target=self._convert_model_thread, 
            args=(input_path, output_path, format_type, quantize, rep_dataset_path), 
            daemon=True
        ).start()
    
    def _convert_model_thread(self, input_path, output_path, format_type, quantize, rep_dataset_path):
        try:
            # Redirect log optimizer ke UI
            original_write = sys.stdout.write
            
            def write_to_log(text):
                if text.strip():  # Skip baris kosong
                    self.root.after(0, lambda: self.log_text.insert(tk.END, text))
                    self.root.after(0, lambda: self.log_text.see(tk.END))
                return original_write(text)
            
            # Monkey patch stdout sementara
            sys.stdout.write = write_to_log
            
            try:
                if format_type == "tflite":
                    # Buat TFLite, cek perlu pake dataset representatif apa nggak
                    rep_dataset = None
                    if quantize and rep_dataset_path:
                        rep_dataset = self.optimizer.generate_representative_dataset(rep_dataset_path)
                        
                    # Convert model
                    output_file = self.optimizer.convert_to_tflite(
                        input_path, 
                        output_path, 
                        quantize=quantize, 
                        representative_dataset=rep_dataset
                    )
                    
                    self.root.after(0, lambda: self.log_text.insert(tk.END, 
                                                                 f"\nKonversi selesai! Model TFLite disimpan di: {output_file}\n"))
                                                                 
                elif format_type == "onnx":
                    # Convert ke ONNX
                    output_file = self.optimizer.convert_to_onnx(input_path, output_path)
                    
                    self.root.after(0, lambda: self.log_text.insert(tk.END, 
                                                                 f"\nKonversi selesai! Model ONNX disimpan di: {output_file}\n"))
            finally:
                # Restore stdout
                sys.stdout.write = original_write
            
            # Tunjukin pesan sukses
            self.root.after(0, lambda: messagebox.showinfo("Konversi Selesai", 
                                                         f"Model berhasil diconvert ke format {format_type.upper()}!"))
            
        except Exception as e:
            # Restore stdout kalau perlu
            if sys.stdout.write != original_write:
                sys.stdout.write = original_write
                
            error_msg = str(e)
            self.root.after(0, lambda: self.log_text.insert(tk.END, f"\nError pas konversi: {error_msg}\n"))
            self.root.after(0, lambda: messagebox.showerror("Error Konversi", f"Error convert model: {error_msg}"))
    
    # Callback methods buat classifier
    def update_progress(self, progress_value):
        self.root.after(0, lambda: self.progress_var.set(progress_value))
    
    def update_status_text(self, text):
        self.root.after(0, lambda: self.status_text.set(text))
    
    def log_classification(self, file_name, predicted_class, confidence):
        self.root.after(0, lambda: self.log_result(
            f"'{file_name}' diklasifikasi sebagai {predicted_class} (confidence: {confidence:.2f})"))
    
    def log_error(self, file_name, error_message):
        self.root.after(0, lambda: self.log_result(f"Error pas proses '{file_name}': {error_message}"))
    
    def classification_complete(self, category_counts, processed, total):
        self.root.after(0, lambda: self.show_summary(category_counts, processed, total))
        self.root.after(0, lambda: self.update_status_text(f"Selesai! {processed} gambar disortir ke kategori."))
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
        
        summary += f"\nTotal: {processed} dari {total} gambar diproses dan disortir."
        self.log_result(summary)

def main():
    # Aktifin DPI awareness
    if sys.platform.startswith('win'):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI awareness
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()  # Fallback
    
    root = tk.Tk()
    app = LiteGalleryApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
