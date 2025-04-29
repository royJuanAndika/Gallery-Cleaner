from PyInstaller.utils.hooks import collect_all

# Collect all TensorFlow related files
datas, binaries, hiddenimports = collect_all('tensorflow')

# Add additional related packages
hiddenimports += [
    'tensorflow_core',
    'astor',
    'termcolor',
    'tensorflow.python.keras.api._v2',
    'tensorflow.lite.python.lite',
    'tensorflow.python.keras.engine',
    'keras.api._v2.keras',
    'h5py'
]