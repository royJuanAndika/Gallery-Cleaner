import os
import tensorflow as tf
import numpy as np
import logging
from tensorflow import keras

class ModelOptimizer:
    """Utility untuk mengonversi dan mengoptimalkan model deep learning"""
    
    def __init__(self):
        self.logger = logging.getLogger("ModelOptimizer")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def convert_to_tflite(self, model_path, output_path=None, quantize=False, 
                          representative_dataset=None, target_formats=None):
        """
        Mengonversi model Keras ke format TensorFlow Lite
        
        Args:
            model_path: Path ke model Keras (.keras, .h5)
            output_path: Path output untuk model TFLite (default: sama dengan input dengan ekstensi .tflite)
            quantize: Apakah model akan di-quantize (mengurangi ukuran, mungkin mempengaruhi akurasi)
            representative_dataset: Fungsi yang menyediakan data representatif untuk quantization
            target_formats: Daftar format target (misalnya, [tf.float16])
            
        Returns:
            Path ke model TFLite yang dikonversi
        """
        if output_path is None:
            base_path = os.path.splitext(model_path)[0]
            output_path = f"{base_path}.tflite"
        
        self.logger.info(f"Memuat model dari {model_path}")
        model = keras.models.load_model(model_path)
        
        # Membuat TFLite converter
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        
        # Mengonfigurasi optimasi
        if quantize:
            self.logger.info("Menerapkan quantization")
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            
            # Jika dataset representatif disediakan, gunakan untuk quantization integer penuh
            if representative_dataset:
                self.logger.info("Menggunakan dataset representatif untuk quantization")
                converter.representative_dataset = representative_dataset
                converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
                converter.inference_input_type = tf.int8
                converter.inference_output_type = tf.int8
        
        # Mengatur format target jika ditentukan
        if target_formats:
            converter.target_spec.supported_types = target_formats
        
        # Mengonversi model
        self.logger.info("Mengonversi model ke format TFLite")
        tflite_model = converter.convert()
        
        # Menyimpan model
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        self.logger.info(f"Model TFLite disimpan ke {output_path}")
        
        # Mencetak perbandingan ukuran
        original_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
        converted_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        reduction = (1 - converted_size / original_size) * 100
        
        self.logger.info(f"Ukuran model asli: {original_size:.2f} MB")
        self.logger.info(f"Ukuran model yang dikonversi: {converted_size:.2f} MB")
        self.logger.info(f"Pengurangan ukuran: {reduction:.2f}%")
        
        return output_path

    def convert_to_onnx(self, model_path, output_path=None):
        """
        Mengonversi model Keras ke format ONNX
        
        Args:
            model_path: Path ke model Keras
            output_path: Path output untuk model ONNX
            
        Returns:
            Path ke model ONNX yang dikonversi
        """
        try:
            import tf2onnx
            import onnx
        except ImportError:
            self.logger.error("Paket tf2onnx atau onnx tidak ditemukan. Instal dengan: pip install tf2onnx onnx")
            return None
        
        if output_path is None:
            base_path = os.path.splitext(model_path)[0]
            output_path = f"{base_path}.onnx"
        
        self.logger.info(f"Memuat model dari {model_path}")
        model = keras.models.load_model(model_path)
        
        # Mengonversi model
        self.logger.info("Mengonversi model ke format ONNX")
        
        # Membuat fungsi konkret dari model
        input_signature = [tf.TensorSpec([1, 224, 224, 3], tf.float32, name='input')]
        concrete_func = tf.function(lambda x: model(x)).get_concrete_function(input_signature)
        
        # Mengonversi ke model ONNX
        onnx_model, _ = tf2onnx.convert.from_concrete_function(concrete_func, output_path=output_path)
        
        self.logger.info(f"Model ONNX disimpan ke {output_path}")
        
        # Mencetak perbandingan ukuran
        original_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
        converted_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        
        self.logger.info(f"Ukuran model asli: {original_size:.2f} MB")
        self.logger.info(f"Ukuran model yang dikonversi: {converted_size:.2f} MB")
        
        return output_path
    
    def generate_representative_dataset(self, folder_path, num_samples=100):
        """
        Membuat fungsi dataset representatif untuk quantization dari sampel gambar
        
        Args:
            folder_path: Path ke folder yang berisi sampel gambar
            num_samples: Jumlah sampel yang akan digunakan
            
        Returns:
            Fungsi dataset representatif untuk TFLite converter
        """
        from tensorflow.keras.preprocessing.image import load_img, img_to_array
        
        self.logger.info(f"Membuat dataset representatif dari {folder_path}")
        
        # Mendapatkan file gambar
        image_files = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_files.append(os.path.join(root, file))
        
        if len(image_files) == 0:
            self.logger.error(f"Tidak ada gambar yang ditemukan di {folder_path}")
            return None
        
        # Membatasi jumlah sampel yang ditentukan
        if len(image_files) > num_samples:
            image_files = image_files[:num_samples]
        
        self.logger.info(f"Menggunakan {len(image_files)} gambar untuk dataset representatif")
        
        def representative_dataset():
            for img_path in image_files:
                try:
                    img = load_img(img_path)
                    img_array = img_to_array(img)
                    img_resized = tf.image.resize(img_array, (224, 224))
                    img_normalized = img_resized / 255.0
                    img_batch = np.expand_dims(img_normalized, axis=0).astype(np.float32)
                    yield [img_batch]
                except Exception as e:
                    self.logger.warning(f"Kesalahan memproses {img_path}: {str(e)}")
        
        return representative_dataset

# Contoh penggunaan
if __name__ == "__main__":
    optimizer = ModelOptimizer()
    
    # Path contoh - perbarui ini sesuai dengan lokasi model Anda
    model_path = "resnet50_pretrained_not-frozen.keras"
    
    # Konversi TFLite dasar
    optimizer.convert_to_tflite(model_path)
    
    # Konversi TFLite yang di-quantize (memerlukan gambar sampel)
    # rep_dataset = optimizer.generate_representative_dataset("sample_images")
    # optimizer.convert_to_tflite(model_path, quantize=True, representative_dataset=rep_dataset)
    
    # Konversi ONNX (memerlukan paket tf2onnx dan onnx)
    # optimizer.convert_to_onnx(model_path)
