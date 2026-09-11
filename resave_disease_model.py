
import os
import shutil
import tensorflow as tf

SOURCE = r"ai_models\disease_model.keras"
BACKUP = r"ai_models\disease_model_backup.keras"
OUTPUT = r"ai_models\disease_model_render.keras"

print("=" * 70)
print("KISANVISION360 - DISEASE MODEL RE-SAVE")
print("=" * 70)

print("\nTensorFlow version:", tf.__version__)

if not os.path.exists(SOURCE):
    raise FileNotFoundError(f"Model not found: {SOURCE}")

print("\n[1] Creating backup...")

if not os.path.exists(BACKUP):
    shutil.copy2(SOURCE, BACKUP)
    print("Backup created:", BACKUP)
else:
    print("Backup already exists:", BACKUP)

print("\n[2] Loading original model...")

model = tf.keras.models.load_model(
    SOURCE,
    compile=False
)

print("Original model loaded successfully.")
print("Input shape :", model.input_shape)
print("Output shape:", model.output_shape)
print("Layers      :", len(model.layers))

if model.output_shape[-1] != 53:
    raise ValueError(
        f"Expected 53 output classes, got {model.output_shape[-1]}"
    )

if model.input_shape[1:] != (128, 128, 3):
    raise ValueError(
        f"Expected input (128,128,3), got {model.input_shape[1:]}"
    )

print("\n[3] Checking model weights...")

total_weights = 0

for layer in model.layers:
    weights = layer.get_weights()

    if weights:
        count = sum(w.size for w in weights)
        total_weights += count
        print(
            f"{layer.name:35s} "
            f"weights={len(weights):2d} "
            f"parameters={count}"
        )

print("\nTotal parameters:", total_weights)

if total_weights == 0:
    raise RuntimeError("Model contains no weights.")

print("\n[4] Saving fresh model...")

if os.path.exists(OUTPUT):
    os.remove(OUTPUT)

model.save(OUTPUT)

print("Fresh model saved:")
print(OUTPUT)

print("\n[5] Testing freshly saved model...")

test_model = tf.keras.models.load_model(
    OUTPUT,
    compile=False
)

print("Fresh model loaded successfully.")
print("Input shape :", test_model.input_shape)
print("Output shape:", test_model.output_shape)
print("Layers      :", len(test_model.layers))

if test_model.output_shape[-1] != 53:
    raise ValueError("Fresh model does not have 53 outputs.")

print("\n" + "=" * 70)
print("SUCCESS")
print("=" * 70)

print("\nNew model:")
print(OUTPUT)

print("\nNext step:")
print("Replace disease_model.keras with disease_model_render.keras")
print("only after this script completes successfully.")

