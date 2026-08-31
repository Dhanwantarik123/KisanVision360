import os
import json
import tensorflow as tf

# =========================================================
# KISANVISION360
# DISEASE MODEL TRAINING - KAGGLE PLANTS DATASET
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Kaggle dataset copied/extracted into:
# D:\KisanVision360\dataset\plants\plant
DATASET_DIR = os.path.join(
    BASE_DIR,
    "dataset",
    "plants",
    "plant"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "ai_models"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "disease_model.keras"
)

CLASS_FILE = os.path.join(
    MODEL_DIR,
    "disease_classes.txt"
)

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 10
SEED = 42


# =========================================================
# CHECK DATASET
# =========================================================

print("=" * 60)
print("KisanVision360 - Disease Model Training")
print("=" * 60)

print("Dataset:")
print(DATASET_DIR)

if not os.path.exists(DATASET_DIR):

    print()
    print("ERROR: Dataset folder not found!")
    print()
    print("Expected structure:")
    print(r"D:\KisanVision360\dataset\plants\plant")
    print()
    exit()


# =========================================================
# LOAD TRAINING DATA
# =========================================================

train_data = tf.keras.utils.image_dataset_from_directory(

    DATASET_DIR,

    validation_split=0.2,

    subset="training",

    seed=SEED,

    image_size=IMAGE_SIZE,

    batch_size=BATCH_SIZE,

    label_mode="int"

)


# =========================================================
# LOAD VALIDATION DATA
# =========================================================

val_data = tf.keras.utils.image_dataset_from_directory(

    DATASET_DIR,

    validation_split=0.2,

    subset="validation",

    seed=SEED,

    image_size=IMAGE_SIZE,

    batch_size=BATCH_SIZE,

    label_mode="int"

)


# =========================================================
# CLASS NAMES
# =========================================================

class_names = train_data.class_names

print()
print("=" * 60)
print("DISEASE CLASSES")
print("=" * 60)

for i, name in enumerate(class_names):

    print(
        i,
        "=",
        name
    )

print()
print("Total classes:", len(class_names))


# =========================================================
# PERFORMANCE
# =========================================================

AUTOTUNE = tf.data.AUTOTUNE

train_data = train_data.prefetch(
    AUTOTUNE
)

val_data = val_data.prefetch(
    AUTOTUNE
)


# =========================================================
# CNN MODEL
# =========================================================

print()
print("=" * 60)
print("CNN MODEL")
print("=" * 60)

model = tf.keras.Sequential([

    tf.keras.layers.Input(
        shape=(224, 224, 3)
    ),

    # Normalization
    tf.keras.layers.Rescaling(
        1.0 / 255
    ),

    # Data augmentation
    tf.keras.layers.RandomFlip(
        "horizontal"
    ),

    tf.keras.layers.RandomRotation(
        0.15
    ),

    tf.keras.layers.RandomZoom(
        0.15
    ),

    # CNN Layer 1
    tf.keras.layers.Conv2D(
        32,
        (3, 3),
        activation="relu"
    ),

    tf.keras.layers.MaxPooling2D(),

    # CNN Layer 2
    tf.keras.layers.Conv2D(
        64,
        (3, 3),
        activation="relu"
    ),

    tf.keras.layers.MaxPooling2D(),

    # CNN Layer 3
    tf.keras.layers.Conv2D(
        128,
        (3, 3),
        activation="relu"
    ),

    tf.keras.layers.MaxPooling2D(),

    # CNN Layer 4
    tf.keras.layers.Conv2D(
        256,
        (3, 3),
        activation="relu"
    ),

    tf.keras.layers.MaxPooling2D(),

    # Classification
    tf.keras.layers.Flatten(),

    tf.keras.layers.Dense(
        256,
        activation="relu"
    ),

    tf.keras.layers.Dropout(
        0.5
    ),

    # OUTPUT = 49 classes
    tf.keras.layers.Dense(
        len(class_names),
        activation="softmax"
    )

])


# =========================================================
# COMPILE
# =========================================================

model.compile(

    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.001
    ),

    loss="sparse_categorical_crossentropy",

    metrics=["accuracy"]

)


model.summary()


# =========================================================
# TRAIN
# =========================================================

print()
print("=" * 60)
print("STARTING TRAINING")
print("=" * 60)

history = model.fit(

    train_data,

    validation_data=val_data,

    epochs=EPOCHS

)


# =========================================================
# CREATE AI MODEL FOLDER
# =========================================================

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)


# =========================================================
# SAVE MODEL
# =========================================================

model.save(
    MODEL_PATH
)


# =========================================================
# SAVE CLASS NAMES
# =========================================================

with open(
    CLASS_FILE,
    "w",
    encoding="utf-8"
) as f:

    for name in class_names:

        f.write(
            name + "\n"
        )


# =========================================================
# SAVE JSON TOO
# =========================================================

JSON_FILE = os.path.join(
    MODEL_DIR,
    "disease_classes.json"
)

with open(
    JSON_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        class_names,
        f,
        indent=4
    )


# =========================================================
# FINAL CHECK
# =========================================================

print()
print("=" * 60)
print("TRAINING COMPLETED")
print("=" * 60)

print()
print("Total classes:", len(class_names))

print()
print("Model saved:")
print(MODEL_PATH)

print()
print("Classes saved:")
print(CLASS_FILE)

print()
print("JSON saved:")
print(JSON_FILE)

print()
print("KisanVision360 Disease AI is ready.")