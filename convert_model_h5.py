
import tensorflow as tf
import os

INPUT_MODEL = "ai_models/disease_model.keras"
OUTPUT_MODEL = "ai_models/disease_model.h5"

print("=" * 60)
print("DISEASE MODEL -> H5 CONVERSION")
print("=" * 60)

print("TensorFlow:", tf.__version__)

print("\nLoading original model...")
model = tf.keras.models.load_model(
    INPUT_MODEL,
    compile=False
)

print("INPUT :", model.input_shape)
print("OUTPUT:", model.output_shape)
print("LAYERS:", len(model.layers))

print("\nSaving H5 model...")
model.save(
    OUTPUT_MODEL,
    save_format="h5"
)

print("Saved:", OUTPUT_MODEL)
print("Size:", round(os.path.getsize(OUTPUT_MODEL) / (1024 * 1024), 2), "MB")

print("\nTesting H5 model...")
test_model = tf.keras.models.load_model(
    OUTPUT_MODEL,
    compile=False
)

print("H5 INPUT :", test_model.input_shape)
print("H5 OUTPUT:", test_model.output_shape)
print("H5 LAYERS:", len(test_model.layers))

print("\nSUCCESS - H5 MODEL LOADS CORRECTLY")
