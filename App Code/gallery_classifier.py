import os
import numpy as np
import tensorflow as tf
import keras
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import shutil

# Set backend
# os.environ["KERAS_BACKEND"] = "plaidml.keras.backend"

class GalleryClassifier:
    def __init__(self, on_progress_update=None, on_status_update=None, 
                 on_image_classified=None, on_error=None, on_complete=None):
        """
        Inisialisasi GalleryClassifier
        
        Args:
            on_progress_update: Callback buat update progress (nilai 0-100)
            on_status_update: Callback buat update teks status
            on_image_classified: Callback pas gambar diklasifikasi (nama file, kelas, kepercayaan diri)
            on_error: Callback pas ada error (nama file, pesan error)
            on_complete: Callback pas klasifikasi selesai (jumlah kategori, diproses, total)
        """
        self.model = None
        self.labels = ["foods", "landscape", "people", "receipts", "screenshots"]
        
        # Simpan callbacks
        self.on_progress_update = on_progress_update
        self.on_status_update = on_status_update
        self.on_image_classified = on_image_classified
        self.on_error = on_error
        self.on_complete = on_complete
    
    def load_model(self, model_path):
        """Load model klasifikasi"""
        self.model = keras.saving.load_model(model_path)
        return self.model is not None
    
    def process_folder(self, folder_path, selected_categories=None):
        """
        Proses semua gambar di folder, klasifikasi, terus urutin ke kategori
        
        Args:
            folder_path: Path ke folder yang ada gambarnya
            selected_categories: List kategori yang mau diproses (kalo None, semua diproses)
        """
        if self.model is None:
            if self.on_error:
                self.on_error("", "Model belum di-load. Load dulu ya!")
            return
        
        # Kalo gak ada kategori yang dipilih, pake semua kategori yang ada
        if selected_categories is None or len(selected_categories) == 0:
            selected_categories = self.labels
        
        try:
            # Bikin folder tujuan buat kategori yang dipilih kalo belum ada
            for label in selected_categories:
                dest_path = os.path.join(folder_path, label)
                if not os.path.exists(dest_path):
                    os.makedirs(dest_path)
            
            # Ambil file gambar
            image_files = [f for f in os.listdir(folder_path) 
                         if os.path.isfile(os.path.join(folder_path, f)) and 
                         f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            total_images = len(image_files)
            
            if total_images == 0:
                if self.on_status_update:
                    self.on_status_update("Gak ada gambar di folder ini.")
                if self.on_complete:
                    self.on_complete({label: 0 for label in selected_categories}, 0, 0)
                return
                
            # Catat jumlah per kategori
            category_counts = {label: 0 for label in self.labels}
            processed = 0
            skipped = 0
            
            # Proses tiap gambar
            for i, img_file in enumerate(image_files):
                try:
                    # Update progress
                    progress = (i / total_images) * 100
                    if self.on_progress_update:
                        self.on_progress_update(progress)
                    
                    if self.on_status_update:
                        self.on_status_update(f"Lagi proses gambar {i+1} dari {total_images}")
                    
                    # Load dan preprocess gambar
                    img_path = os.path.join(folder_path, img_file)
                    img = load_img(img_path)
                    
                    # Preprocess buat model
                    img_array = img_to_array(img)
                    img_resized = tf.image.resize(img_array, (224, 224))
                    img_normalized = img_resized / 255.0
                    img_batch = np.expand_dims(img_normalized, axis=0)
                    
                    # Bikin prediksi
                    prediction = self.model.predict(img_batch, verbose=0)
                    predicted_class = self.labels[np.argmax(prediction)]
                    confidence = np.max(prediction)
                    
                    # Cuma pindahin gambar kalo kelas prediksinya ada di kategori yang dipilih
                    if predicted_class in selected_categories:
                        # Pindahin gambar ke folder yang sesuai
                        dest_path = os.path.join(folder_path, predicted_class, img_file)
                        shutil.copy(img_path, dest_path)
                        
                        # Update jumlah
                        category_counts[predicted_class] += 1
                        processed += 1
                        
                        # Catat klasifikasi kalo ada callback
                        if self.on_image_classified:
                            self.on_image_classified(img_file, predicted_class, confidence)
                    else:
                        skipped += 1
                        if self.on_image_classified:
                            self.on_image_classified(
                                img_file, 
                                f"{predicted_class} (dilewati - gak ada di kategori yang dipilih)", 
                                confidence
                            )
                
                except Exception as e:
                    if self.on_error:
                        self.on_error(img_file, str(e))
            
            # Proses selesai
            if self.on_complete:
                # Filter jumlah biar cuma ada kategori yang dipilih
                filtered_counts = {k: v for k, v in category_counts.items() if k in selected_categories}
                self.on_complete(filtered_counts, processed, total_images)
                
            if self.on_status_update:
                self.on_status_update(f"Selesai! {processed} gambar udah diurutin ke kategori yang dipilih. {skipped} gambar dilewati.")
            
        except Exception as e:
            if self.on_error:
                self.on_error("", str(e))

    def classify_single_image(self, image_path):
        """Klasifikasi satu gambar dan return kelas prediksi sama kepercayaan diri"""
        if self.model is None:
            raise ValueError("Model belum di-load. Load dulu ya!")
            
        try:
            # Load dan preprocess gambar
            img = load_img(image_path)
            
            # Preprocess buat model
            img_array = img_to_array(img)
            img_resized = tf.image.resize(img_array, (224, 224))
            img_normalized = img_resized / 255.0
            img_batch = np.expand_dims(img_normalized, axis=0)
            
            # Bikin prediksi
            prediction = self.model.predict(img_batch, verbose=0)
            predicted_class = self.labels[np.argmax(prediction)]
            confidence = np.max(prediction)
            
            return predicted_class, confidence
        
        except Exception as e:
            raise Exception(f"Error klasifikasi gambar: {str(e)}")
