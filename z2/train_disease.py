# ============================================================
# KisanVision360 - Lightweight Disease Classification Training
# Designed for low-RAM CPU systems
# ============================================================

import os

# ------------------------------------------------------------
# IMPORTANT: Set these BEFORE importing TensorFlow
# ------------------------------------------------------------
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

# Limit CPU threads to reduce RAM usage
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TF_NUM_INTRAOP_THREADS"] = "1"
os.environ["TF_NUM_INTEROP_THREADS"] = "1"

import gc
import json
from pathlib import Path

import numpy as np
import tensorflow as tf

from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import (
    ModelCheckpoint,
    EarlyStopping,
    ReduceLROnPlateau
)


# ============================================================
# 1. PATHS
# ============================================================

DATASET_DIR = r"D:\KisanVision360\dataset_filtered"

OUTPUT_DIR = r"D:\KisanVision360\ai_models"

MODEL_PATH = os.path.join(
    OUTPUT_DIR,
    "disease_model.keras"
)

CLASS_FILE = os.path.join(
    OUTPUT_DIR,
    "disease_classes.txt"
)

CLASS_JSON = os.path.join(
    OUTPUT_DIR,
    "disease_classes.json"
)


# ============================================================
# 2. TRAINING SETTINGS
# ============================================================

# VERY LOW MEMORY SETTINGS
IMG_SIZE = (128, 128)

BATCH_SIZE = 1

EPOCHS = 15

VALIDATION_SPLIT = 0.20

SEED = 123


# ============================================================
# 3. CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# 4. CONFIGURE TENSORFLOW
# ============================================================

print()
print("=" * 65)
print("KISANVISION360 DISEASE MODEL TRAINING")
print("=" * 65)

print()
print("TensorFlow version:", tf.__version__)

# CPU only
try:
    tf.config.set_visible_devices([], "GPU")
    print("GPU disabled: CPU training selected.")
except Exception:
    print("CPU training selected.")


# Configure TensorFlow threads
try:
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.threading.set_inter_op_parallelism_threads(1)
except Exception as e:
    print("Thread configuration:", e)


# ============================================================
# 5. CHECK DATASET
# ============================================================

dataset_path = Path(DATASET_DIR)

if not dataset_path.exists():

    print()
    print("ERROR: Dataset folder not found!")
    print()
    print("Expected:")
    print(DATASET_DIR)

    raise SystemExit(1)


# ============================================================
# 6. FIND CLASS FOLDERS
# ============================================================

class_dirs = sorted([
    folder
    for folder in dataset_path.iterdir()
    if folder.is_dir()
])


if len(class_dirs) == 0:

    print()
    print("ERROR: No class folders found.")
    print()
    print("Your dataset should look like:")
    print()
    print("dataset_filtered/")
    print("    bacterial_blight/")
    print("    curl_virus/")
    print("    fussarium_wilt/")
    print("    healthy/")
    print()

    raise SystemExit(1)


class_names = [
    folder.name
    for folder in class_dirs
]


# ============================================================
# 7. PRINT CLASSES
# ============================================================

print()
print("-" * 65)
print("DATASET INFORMATION")
print("-" * 65)

print()
print("Dataset:", DATASET_DIR)

print("Total Classes:", len(class_names))

print()
print("Classes:")

for index, class_name in enumerate(class_names):

    print(
        f"  {index}: {class_name}"
    )


# ============================================================
# 8. COUNT IMAGES
# ============================================================

valid_extensions = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".webp"
}


total_images = 0

print()
print("Image count per class:")
print()


for class_dir in class_dirs:

    count = 0

    for file in class_dir.rglob("*"):

        if (
            file.is_file()
            and file.suffix.lower() in valid_extensions
        ):
            count += 1

    total_images += count

    print(
        f"  {class_dir.name}: {count}"
    )


print()
print("Total images:", total_images)


if total_images == 0:

    print()
    print("ERROR: No images found!")

    raise SystemExit(1)


# ============================================================
# 9. SAVE CLASS NAMES
# ============================================================

with open(
    CLASS_FILE,
    "w",
    encoding="utf-8"
) as file:

    for class_name in class_names:

        file.write(
            class_name + "\n"
        )


with open(
    CLASS_JSON,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        {
            "classes": class_names
        },
        file,
        indent=4
    )


print()
print("Class files saved.")


# ============================================================
# 10. LOAD TRAINING DATA
# ============================================================

print()
print("-" * 65)
print("LOADING DATASET")
print("-" * 65)

print()
print("Image size:", IMG_SIZE)

print("Batch size:", BATCH_SIZE)

print("Validation split:", VALIDATION_SPLIT)


train_ds = tf.keras.utils.image_dataset_from_directory(

    DATASET_DIR,

    validation_split=VALIDATION_SPLIT,

    subset="training",

    seed=SEED,

    image_size=IMG_SIZE,

    batch_size=BATCH_SIZE,

    label_mode="int",

    shuffle=True
)


# ============================================================
# 11. LOAD VALIDATION DATA
# ============================================================

val_ds = tf.keras.utils.image_dataset_from_directory(

    DATASET_DIR,

    validation_split=VALIDATION_SPLIT,

    subset="validation",

    seed=SEED,

    image_size=IMG_SIZE,

    batch_size=BATCH_SIZE,

    label_mode="int",

    shuffle=False
)


# ============================================================
# 12. VERIFY CLASS ORDER
# ============================================================

loaded_class_names = train_ds.class_names


print()
print("TensorFlow detected classes:")

for i, name in enumerate(loaded_class_names):

    print(
        f"  {i}: {name}"
    )


# Check expected classes
if len(loaded_class_names) != len(class_names):

    print()
    print("WARNING:")
    print(
        "Number of detected classes changed."
    )


# ============================================================
# 13. DATASET PERFORMANCE SETTINGS
# ============================================================

# DO NOT use cache()
# because cache can consume large amounts of RAM.

AUTOTUNE = tf.data.AUTOTUNE


# Keep only ONE batch prefetched
train_ds = train_ds.prefetch(1)

val_ds = val_ds.prefetch(1)


# ============================================================
# 14. DATA AUGMENTATION
# ============================================================

data_augmentation = tf.keras.Sequential(

    [

        layers.RandomFlip(
            "horizontal"
        ),

        layers.RandomRotation(
            0.03
        ),

        layers.RandomZoom(
            0.05
        )

    ],

    name="data_augmentation"
)


# ============================================================
# 15. BUILD SMALL CNN MODEL
# ============================================================

print()
print("-" * 65)
print("BUILDING MODEL")
print("-" * 65)


model = models.Sequential(

    [

        layers.Input(
            shape=(128, 128, 3)
        ),


        # Data augmentation
        data_augmentation,


        # Normalize pixels
        layers.Rescaling(
            1.0 / 255.0
        ),


        # ----------------------------------------------------
        # Small CNN
        # ----------------------------------------------------

        layers.Conv2D(
            8,
            (3, 3),
            activation="relu",
            padding="same"
        ),

        layers.MaxPooling2D(
            (2, 2)
        ),


        layers.Conv2D(
            16,
            (3, 3),
            activation="relu",
            padding="same"
        ),

        layers.MaxPooling2D(
            (2, 2)
        ),


        layers.Conv2D(
            32,
            (3, 3),
            activation="relu",
            padding="same"
        ),

        layers.MaxPooling2D(
            (2, 2)
        ),


        layers.Conv2D(
            32,
            (3, 3),
            activation="relu",
            padding="same"
        ),

        layers.MaxPooling2D(
            (2, 2)
        ),


        # Reduce feature maps
        layers.GlobalAveragePooling2D(),


        layers.Dense(
            32,
            activation="relu"
        ),


        layers.Dropout(
            0.30
        ),


        # Output
        layers.Dense(
            len(loaded_class_names),
            activation="softmax"
        )

    ],

    name="KisanVision360_Disease_Model"
)


# ============================================================
# 16. COMPILE MODEL
# ============================================================

model.compile(

    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.001
    ),

    loss="sparse_categorical_crossentropy",

    metrics=[
        "accuracy"
    ]
)


# ============================================================
# 17. SHOW MODEL
# ============================================================

print()

model.summary()


# ============================================================
# 18. CALLBACKS
# ============================================================

checkpoint = ModelCheckpoint(

    MODEL_PATH,

    monitor="val_accuracy",

    save_best_only=True,

    mode="max",

    verbose=1
)


early_stopping = EarlyStopping(

    monitor="val_accuracy",

    patience=3,

    restore_best_weights=True,

    mode="max",

    verbose=1
)


reduce_lr = ReduceLROnPlateau(

    monitor="val_loss",

    factor=0.5,

    patience=1,

    min_lr=0.000001,

    verbose=1
)


# ============================================================
# 19. PRINT TRAINING INFORMATION
# ============================================================

print()
print("=" * 65)
print("TRAINING STARTED")
print("=" * 65)

print()
print("Image size       :", IMG_SIZE)
print("Batch size       :", BATCH_SIZE)
print("Epochs           :", EPOCHS)
print("Classes          :", len(loaded_class_names))
print("Total images     :", total_images)

print()
print("IMPORTANT:")
print("This version is designed to minimize RAM usage.")
print("Do NOT use cache() during training.")
print()


# ============================================================
# 20. TRAIN MODEL
# ============================================================

try:

    history = model.fit(

        train_ds,

        validation_data=val_ds,

        epochs=EPOCHS,

        callbacks=[
            checkpoint,
            early_stopping,
            reduce_lr
        ],

        verbose=1
    )


except tf.errors.ResourceExhaustedError:

    print()
    print("=" * 65)
    print("MEMORY ERROR")
    print("=" * 65)

    print()
    print("Your computer does not have enough RAM")
    print("even for the current configuration.")

    print()
    print("Current settings:")
    print("Image size :", IMG_SIZE)
    print("Batch size :", BATCH_SIZE)

    print()
    print("Close Chrome, VS Code and other applications")
    print("and run the training again.")

    gc.collect()

    raise SystemExit(1)


except KeyboardInterrupt:

    print()
    print("Training stopped by user.")

    gc.collect()

    raise SystemExit(0)


# ============================================================
# 21. GARBAGE COLLECTION
# ============================================================

gc.collect()


# ============================================================
# 22. LOAD BEST MODEL
# ============================================================

print()
print("-" * 65)
print("LOADING BEST MODEL")
print("-" * 65)


if os.path.exists(MODEL_PATH):

    try:

        best_model = tf.keras.models.load_model(
            MODEL_PATH
        )

        print()
        print(
            "Best model loaded successfully."
        )

    except Exception as e:

        print()
        print(
            "Could not reload best model:"
        )

        print(e)

        best_model = model

else:

    print()
    print(
        "Checkpoint not found."
    )

    best_model = model


# ============================================================
# 23. VALIDATION EVALUATION
# ============================================================

print()
print("=" * 65)
print("FINAL VALIDATION")
print("=" * 65)


try:

    loss, accuracy = best_model.evaluate(

        val_ds,

        verbose=1
    )

    print()
    print(
        f"Validation Loss     : {loss:.4f}"
    )

    print(
        f"Validation Accuracy : {accuracy * 100:.2f}%"
    )


except tf.errors.ResourceExhaustedError:

    print()
    print(
        "Validation also caused a memory error."
    )


# ============================================================
# 24. SAVE CLASS FILES AGAIN
# ============================================================

with open(
    CLASS_FILE,
    "w",
    encoding="utf-8"
) as file:

    for class_name in loaded_class_names:

        file.write(
            class_name + "\n"
        )


with open(
    CLASS_JSON,
    "w",
    encoding="utf-8"
) as file:

    json.dump(

        {
            "classes": loaded_class_names
        },

        file,

        indent=4
    )


# ============================================================
# 25. FINAL INFORMATION
# ============================================================

print()
print("=" * 65)
print("TRAINING COMPLETED")
print("=" * 65)

print()

print(
    "Model file:"
)

print(
    MODEL_PATH
)

print()

print(
    "Class file:"
)

print(
    CLASS_FILE
)

print()

print(
    "JSON file:"
)

print(
    CLASS_JSON
)

print()

print(
    "Classes:"
)

for i, class_name in enumerate(
    loaded_class_names
):

    print(
        f"{i} -> {class_name}"
    )

print()

print(
    "KisanVision360 disease model is ready."
)

print("=" * 65)
