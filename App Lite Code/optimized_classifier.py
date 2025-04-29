import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import shutil
import logging

class OptimizedClassifier:
    """
    Image classifier yang mendukung model TensorFlow biasa dan model yang dioptimalkan
    (TensorFlow Lite, ONNX)
    """
    
    def __init__(self, on_progress_update=None, on_status_update=None, 
                 on_image_classified=None, on_error=None, on_complete=None):
        """
        Inisialisasi OptimizedClassifier
        
        Args:
            on_progress_update: Callback untuk update progress (nilai 0-100)
            on_status_update: Callback untuk update teks status
            on_image_classified: Callback ketika gambar diklasifikasikan (filename, class, confidence)
            on_error: Callback ketika terjadi error (filename, error_message)
            on_complete: Callback ketika klasifikasi selesai (category_counts, processed, total)
        """
        self.model = None
        self.model_type = None  # 'keras', 'tflite', 'onnx'
        self.labels = ["foods", "landscape", "people", "receipts", "screenshots"]
        
        # Konfigurasi logging
        self.logger = logging.getLogger("OptimizedClassifier")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Simpan callbacks
        self.on_progress_update = on_progress_update
        self.on_status_update = on_status_update
        self.on_image_classified = on_image_classified
        self.on_error = on_error
        self.on_complete = on_complete
    
    def load_model(self, model_path):
        """
        Load model dari file. Otomatis mendeteksi tipe model berdasarkan ekstensi.
        
        Args:
            model_path: Path ke file model (.keras, .h5, .tflite, .onnx)
            
        Returns:
            True jika model berhasil di-load, False jika gagal
        """
        file_ext = os.path.splitext(model_path)[1].lower()
        
        try:
            if file_ext in ['.keras', '.h5']:
                self.logger.info(f"Loading model Keras dari {model_path}")
                import tensorflow as tf
                self.model = tf.keras.models.load_model(model_path)
                self.model_type = 'keras'
                return True
                
            elif file_ext == '.tflite':
                self.logger.info(f"Loading model TFLite dari {model_path}")
                # Load model TFLite
                interpreter = tf.lite.Interpreter(model_path=model_path)
                interpreter.allocate_tensors()
                self.model = interpreter
                self.model_type = 'tflite'
                return True
                
            elif file_ext == '.onnx':
                self.logger.info(f"Loading model ONNX dari {model_path}")
                try:
                    import onnxruntime as ort
                except ImportError:
                    self.logger.error("ONNX Runtime belum diinstal. Instal dengan: pip install onnxruntime")
                    if self.on_error:
                        self.on_error("", "ONNX Runtime belum diinstal. Silakan instal paket onnxruntime.")
                    return False
                
                # Buat sesi ONNX Runtime
                self.model = ort.InferenceSession(model_path)
                self.model_type = 'onnx'
                return True
                
            else:
                self.logger.error(f"Format model tidak didukung: {file_ext}")
                if self.on_error:
                    self.on_error("", f"Format model tidak didukung: {file_ext}. Format yang didukung: .keras, .h5, .tflite, .onnx")
                return False
                
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            if self.on_error:
                self.on_error("", f"Error loading model: {str(e)}")
            return False
    
    def predict_image(self, img_array):
        """
        Buat prediksi menggunakan model yang sudah di-load
        
        Args:
            img_array: Array gambar yang sudah diproses (dinormalisasi, di-resize ke 224x224)
            
        Returns:
            Tuple dari (predicted_class_index, confidence)
        """
        if self.model is None:
            raise ValueError("Model belum di-load. Silakan load model terlebih dahulu.")
        
        if self.model_type == 'keras':
            # Prediksi Keras standar
            prediction = self.model.predict(np.expand_dims(img_array, axis=0), verbose=0)
            class_idx = np.argmax(prediction)
            confidence = np.max(prediction)
            
        elif self.model_type == 'tflite':
            # Prediksi TFLite
            interpreter = self.model
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            # Cek apakah model dikuantisasi
            is_quantized = input_details[0]['dtype'] == np.uint8 atau input_details[0]['dtype'] == np.int8
            
            if is_quantized:
                # Handle model yang dikuantisasi
                input_scale, input_zero_point = input_details[0]['quantization']
                if input_scale != 0:  # Pastikan tidak ada pembagian dengan nol
                    img_array = img_array / input_scale + input_zero_point
                img_array = img_array.astype(input_details[0]['dtype'])
            
            # Resize jika diperlukan
            input_shape = input_details[0]['shape'][1:3]  # Tinggi, lebar
            if input_shape != (224, 224):
                img_array = tf.image.resize(img_array, input_shape).numpy()
            
            # Buat dimensi batch
            img_batch = np.expand_dims(img_array, axis=0)
            
            # Set input tensor
            interpreter.set_tensor(input_details[0]['index'], img_batch)
            
            # Jalankan inferensi
            interpreter.invoke()
            
            # Dapatkan output
            output_data = interpreter.get_tensor(output_details[0]['index'])
            
            # Dapatkan prediksi
            class_idx = np.argmax(output_data)
            confidence = output_data[0][class_idx]
            
        elif self.model_type == 'onnx':
            # Prediksi ONNX
            import onnxruntime as ort
            
            # Dapatkan input model
            input_name = self.model.get_inputs()[0].name
            
            # Siapkan input
            img_batch = np.expand_dims(img_array, axis=0).astype(np.float32)
            
            # Jalankan inferensi
            output = self.model.run(None, {input_name: img_batch})
            
            # Dapatkan prediksi
            predictions = output[0]
            class_idx = np.argmax(predictions)
            confidence = predictions[0][class_idx]
            
        else:
            raise ValueError(f"Tipe model tidak didukung: {self.model_type}")
        
        return class_idx, confidence
    
    def process_folder(self, folder_path, selected_categories=None):
        """
        Proses semua gambar di folder, klasifikasikan, dan urutkan ke dalam kategori
        
        Args:
            folder_path: Path ke folder yang berisi gambar
            selected_categories: List kategori yang akan diproses (jika None, semua kategori diproses)
        """
        if self.model is None:
            if self.on_error:
                self.on_error("", "Model belum di-load. Silakan load model terlebih dahulu.")
            return
        
        # Jika tidak ada kategori yang dipilih, gunakan semua kategori yang tersedia
        if selected_categories is None atau len(selected_categories) == 0:
            selected_categories = self.labels
        
        try:
            # Buat folder tujuan untuk kategori yang dipilih jika belum ada
            for label in selected_categories:
                dest_path = os.path.join(folder_path, label)
                if not os.path.exists(dest_path):
                    os.makedirs(dest_path)
            
            # Dapatkan file gambar
            image_files = [f for f in os.listdir(folder_path) 
                         if os.path.isfile(os.path.join(folder_path, f)) dan 
                         f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            total_images = len(image_files)
            
            if total_images == 0:
                if self.on_status_update:
                    self.on_status_update("Tidak ada gambar yang ditemukan di folder yang dipilih.")
                if self.on_complete:
                    self.on_complete({label: 0 for label in selected_categories}, 0, 0)
                return
                
            # Track jumlah berdasarkan kategori
            category_counts = {label: 0 for label in self.labels}
            processed = 0
            skipped = 0
            
            # Proses setiap gambar
            for i, img_file in enumerate(image_files):
                try:
                    # Update progress
                    progress = (i / total_images) * 100
                    if self.on_progress_update:
                        self.on_progress_update(progress)
                    
                    if self.on_status_update:
                        self.on_status_update(f"Memproses gambar {i+1} dari {total_images}")
                    
                    # Load dan preprocess gambar
                    img_path = os.path.join(folder_path, img_file)
                    img = load_img(img_path)
                    
                    # Preprocess untuk model
                    img_array = img_to_array(img)
                    img_resized = tf.image.resize(img_array, (224, 224))
                    img_normalized = img_resized / 255.0
                    
                    # Buat prediksi
                    class_idx, confidence = self.predict_image(img_normalized)
                    predicted_class = self.labels[class_idx]
                    
                    # Hanya pindahkan gambar jika kelas prediksi ada di kategori yang dipilih
                    if predicted_class in selected_categories:
                        # Pindahkan gambar ke folder yang sesuai
                        dest_path = os.path.join(folder_path, predicted_class, img_file)
                        shutil.move(img_path, dest_path)
                        
                        # Update jumlah
                        category_counts[predicted_class] += 1
                        processed += 1
                        
                        # Log klasifikasi jika callback disediakan
                        if self.on_image_classified:
                            self.on_image_classified(img_file, predicted_class, confidence)
                    else:
                        skipped += 1
                        if self.on_image_classified:
                            self.on_image_classified(
                                img_file, 
                                f"{predicted_class} (dilewati - tidak ada di kategori yang dipilih)", 
                                confidence
                            )
                
                except Exception as e:
                    self.logger.error(f"Error memproses {img_file}: {str(e)}")
                    if self.on_error:
                        self.on_error(img_file, str(e))
            
            # Selesaikan proses
            if self.on_complete:
                # Filter jumlah untuk hanya menyertakan kategori yang dipilih
                filtered_counts = {k: v for k, v in category_counts.items() if k in selected_categories}
                self.on_complete(filtered_counts, processed, total_images)
                
            if self.on_status_update:
                self.on_status_update(f"Selesai! {processed} gambar diurutkan ke dalam kategori yang dipilih. {skipped} gambar dilewati.")
            
        except Exception as e:
            self.logger.error(f"Error memproses folder: {str(e)}")
            if self.on_error:
                self.on_error("", str(e))

    def classify_single_image(self, image_path):
        """Klasifikasikan satu gambar dan kembalikan kelas prediksi dan confidence"""
        if self.model is None:
            raise ValueError("Model belum di-load. Silakan load model terlebih dahulu.")
            
        try:
            # Load dan preprocess gambar
            img = load_img(image_path)
            
            # Preprocess untuk model
            img_array = img_to_array(img)
            img_resized = tf.image.resize(img_array, (224, 224))
            img_normalized = img_resized / 255.0
            
            # Buat prediksi
            class_idx, confidence = self.predict_image(img_normalized)
            predicted_class = self.labels[class_idx]
            
            return predicted_class, confidence
        
        except Exception as e:
            raise Exception(f"Error mengklasifikasikan gambar: {str(e)}")
