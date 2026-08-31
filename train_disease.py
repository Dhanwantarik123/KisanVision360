import os
import tensorflow as tf
from tensorflow.keras import layers, models

# =========================================================
# DATASET PATH
# =========================================================

DATASET_DIR = r"D:\KisanVision360\kaggle_data\datasets\seroshkarim\cotton-leaf-disease-dataset\versions\1\cotton"

# =========================================================
# MODEL OUTPUT PATH
# =========================================================

MODEL_PATH = r"D:\KisanVision360\ai_models\disease_model.keras"

# =========================================================
# SETTINGS
# =========================================================

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 15

# =========================================================
# LOAD TRAINING DATA
# =========================================================

train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

# =========================================================
# LOAD VALIDATION DATA
# =========================================================

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

# =========================================================
# CLASS NAMES
# =========================================================

class_names = train_ds.class_names

print("\n========================================")
print("DISEASE CLASSES")
print("========================================")

for i, name in enumerate(class_names):
    print(i, "=", name)

print("Total Classes:", len(class_names))

# =========================================================
# SAVE CLASS NAMES
# =========================================================

os.makedirs(
    r"D:\KisanVision360\ai_models",
    exist_ok=True
)

with open(
    r"D:\KisanVision360\ai_models\disease_classes.txt",
    "w",
    encoding="utf-8"
) as f:

    for name in class_names:
        f.write(name + "\n")

# =========================================================
# PERFORMANCE
# =========================================================

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.prefetch(
    AUTOTUNE
)

val_ds = val_ds.prefetch(
    AUTOTUNE
)

# =========================================================
# CNN MODEL
# =========================================================

model = models.Sequential([

    layers.Input(
        shape=(224, 224, 3)
    ),

    # Image normalization
    layers.Rescaling(
        1.0 / 255
    ),

    # CNN Layer 1
    layers.Conv2D(
        32,
        (3, 3),
        activation="relu"
    ),

    layers.MaxPooling2D(
        (2, 2)
    ),

    # CNN Layer 2
    layers.Conv2D(
        64,
        (3, 3),
        activation="relu"
    ),

    layers.MaxPooling2D(
        (2, 2)
    ),

    # CNN Layer 3
    layers.Conv2D(
        128,
        (3, 3),
        activation="relu"
    ),

    layers.MaxPooling2D(
        (2, 2)
    ),

    # Flatten
    layers.Flatten(),

    # Dense
    layers.Dense(
        128,
        activation="relu"
    ),

    layers.Dropout(
        0.5
    ),

    # OUTPUT = 4 CLASSES
    layers.Dense(
        len(class_names),
        activation="softmax"
    )
])

# =========================================================
# COMPILE
# =========================================================

model.compile(

    optimizer="adam",

    loss="sparse_categorical_crossentropy",

    metrics=[
        "accuracy"
    ]
)

# =========================================================
# MODEL SUMMARY
# =========================================================

print("\n========================================")
print("MODEL SUMMARY")
print("========================================")

model.summary()

# =========================================================
# TRAIN
# =========================================================

print("\n========================================")
print("TRAINING STARTED")
print("========================================")

history = model.fit(

    train_ds,

    validation_data=val_ds,

    epochs=EPOCHS

)

# =========================================================
# SAVE MODEL
# =========================================================

model.save(
    MODEL_PATH
)

print("\n========================================")
print("TRAINING COMPLETED")
print("========================================")

print(
    "Model saved at:",
    MODEL_PATH
)

print(
    "Classes:",
    len(class_names)
)

print(
    "Class names:",
    class_names
)