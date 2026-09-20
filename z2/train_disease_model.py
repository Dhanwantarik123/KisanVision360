import os

# ============================================================
# LOW MEMORY SETTINGS - MUST BE BEFORE TENSORFLOW IMPORT
# ============================================================

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["TF_NUM_INTRAOP_THREADS"] = "2"
os.environ["TF_NUM_INTEROP_THREADS"] = "2"

import json
import numpy as np
import tensorflow as tf

from pathlib import Path

from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

from tensorflow.keras.callbacks import (
    ModelCheckpoint,
    EarlyStopping,
    ReduceLROnPlateau
)


# ============================================================
# KISANVISION360 - DISEASE MODEL TRAINING
# LOW MEMORY VERSION
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
# TRAINING SETTINGS
# ============================================================

IMG_SIZE = (160, 160)

# Important for your memory error
BATCH_SIZE = 2

EPOCHS = 15

VALIDATION_SPLIT = 0.20

SEED = 42


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("KISANVISION360 DISEASE MODEL TRAINING")
print("LOW MEMORY MOBILENETV2 VERSION")
print("=" * 70)

print("\nTensorFlow version:")
print(tf.__version__)


# ============================================================
# CPU THREAD LIMIT
# ============================================================

try:

    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.config.threading.set_inter_op_parallelism_threads(2)

except Exception as e:

    print("\nThread configuration warning:")
    print(e)


# ============================================================
# GPU CHECK
# ============================================================

gpus = tf.config.list_physical_devices("GPU")

if gpus:

    print("\nGPU detected:")

    for gpu in gpus:
        print("   ", gpu)

else:

    print("\nNo GPU detected.")
    print("Training will use CPU.")


# ============================================================
# DATASET CHECK
# ============================================================

dataset_path = Path(DATASET_DIR)

if not dataset_path.exists():

    raise FileNotFoundError(
        f"\nDataset folder not found:\n{DATASET_DIR}"
    )


# ============================================================
# FIND CLASS FOLDERS
# ============================================================

class_names = sorted(
    [
        folder.name
        for folder in dataset_path.iterdir()
        if folder.is_dir()
    ]
)


print("\nDataset path:")
print(DATASET_DIR)

print("\nNumber of classes:")
print(len(class_names))


# ============================================================
# PRINT CLASSES
# ============================================================

print("\nClasses:")

for index, class_name in enumerate(class_names):

    print(
        f"{index:02d} -> {class_name}"
    )


# ============================================================
# IMPORTANT:
# DO NOT HARD-CODE 52 / 53
# ============================================================

if len(class_names) < 2:

    raise ValueError(
        "At least 2 disease classes are required."
    )


print(
    f"\nUsing {len(class_names)} classes."
)


# ============================================================
# COUNT IMAGES
# ============================================================

valid_extensions = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".webp"
}

class_counts = {}

total_images = 0


print("\n" + "=" * 70)
print("IMAGE COUNT")
print("=" * 70)


for class_name in class_names:

    class_folder = dataset_path / class_name

    count = 0

    for file in class_folder.rglob("*"):

        if (
            file.is_file()
            and file.suffix.lower()
            in valid_extensions
        ):

            count += 1

    class_counts[class_name] = count

    total_images += count

    print(
        f"{class_name:<55} {count}"
    )


print("\nTotal images:")
print(total_images)


if total_images == 0:

    raise ValueError(
        "No images were found in the dataset."
    )


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# SAVE CLASS NAMES
# ============================================================

with open(
    CLASS_FILE,
    "w",
    encoding="utf-8"
) as f:

    for class_name in class_names:

        f.write(
            class_name + "\n"
        )


with open(
    CLASS_JSON,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        class_names,
        f,
        indent=4,
        ensure_ascii=False
    )


print("\nClass files created:")

print(CLASS_FILE)
print(CLASS_JSON)


# ============================================================
# LOAD TRAINING DATA
# ============================================================

print("\n" + "=" * 70)
print("LOADING TRAINING DATA")
print("=" * 70)


train_ds = tf.keras.utils.image_dataset_from_directory(

    DATASET_DIR,

    labels="inferred",

    label_mode="int",

    class_names=class_names,

    validation_split=VALIDATION_SPLIT,

    subset="training",

    seed=SEED,

    image_size=IMG_SIZE,

    batch_size=BATCH_SIZE,

    shuffle=True

)


# ============================================================
# LOAD VALIDATION DATA
# ============================================================

print("\n" + "=" * 70)
print("LOADING VALIDATION DATA")
print("=" * 70)


val_ds = tf.keras.utils.image_dataset_from_directory(

    DATASET_DIR,

    labels="inferred",

    label_mode="int",

    class_names=class_names,

    validation_split=VALIDATION_SPLIT,

    subset="validation",

    seed=SEED,

    image_size=IMG_SIZE,

    batch_size=BATCH_SIZE,

    shuffle=False

)


# ============================================================
# DATASET INFORMATION
# ============================================================

print("\nTraining batches:")

print(
    tf.data.experimental
    .cardinality(train_ds)
    .numpy()
)


print("\nValidation batches:")

print(
    tf.data.experimental
    .cardinality(val_ds)
    .numpy()
)


# ============================================================
# DATA AUGMENTATION
# ============================================================

data_augmentation = tf.keras.Sequential(

    [

        layers.RandomFlip(
            "horizontal"
        ),

        layers.RandomRotation(
            0.05
        ),

        layers.RandomZoom(
            0.10
        ),

    ],

    name="data_augmentation"

)


# ============================================================
# MEMORY-SAFE DATA PIPELINE
# ============================================================

# DO NOT USE AUTOTUNE HERE
train_ds = train_ds.prefetch(1)

val_ds = val_ds.prefetch(1)


# ============================================================
# CREATE MOBILENETV2
# ============================================================

print("\n" + "=" * 70)
print("CREATING MOBILENETV2 MODEL")
print("=" * 70)


base_model = MobileNetV2(

    input_shape=(
        IMG_SIZE[0],
        IMG_SIZE[1],
        3
    ),

    include_top=False,

    weights="imagenet"

)


# Freeze MobileNetV2
base_model.trainable = False


print("\nMobileNetV2 created.")

print("Input size:")
print(IMG_SIZE)

print("Base model trainable:")
print(base_model.trainable)


# ============================================================
# CREATE FINAL MODEL
# ============================================================

inputs = layers.Input(

    shape=(
        IMG_SIZE[0],
        IMG_SIZE[1],
        3
    ),

    name="image_input"

)


# Augmentation
x = data_augmentation(inputs)


# MobileNetV2 preprocessing
x = layers.Lambda(

    preprocess_input,

    name="mobilenet_preprocessing"

)(x)


# MobileNetV2
x = base_model(

    x,

    training=False

)


# Global average pooling
x = layers.GlobalAveragePooling2D()(x)


# Dropout
x = layers.Dropout(
    0.30
)(x)


# Smaller dense layer
x = layers.Dense(

    128,

    activation="relu"

)(x)


x = layers.Dropout(
    0.20
)(x)


# ============================================================
# OUTPUT
# ============================================================

outputs = layers.Dense(

    len(class_names),

    activation="softmax",

    name="disease_output"

)(x)


# ============================================================
# COMPLETE MODEL
# ============================================================

model = models.Model(

    inputs,

    outputs,

    name="KisanVision360_Disease_Model"

)


# ============================================================
# COMPILE
# ============================================================

model.compile(

    optimizer=tf.keras.optimizers.Adam(

        learning_rate=0.0001

    ),

    loss="sparse_categorical_crossentropy",

    metrics=[
        "accuracy"
    ]

)


# ============================================================
# MODEL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("MODEL SUMMARY")
print("=" * 70)

model.summary()


print("\nModel input shape:")

print(
    model.input_shape
)


print("\nModel output shape:")

print(
    model.output_shape
)


# ============================================================
# VERIFY OUTPUT
# ============================================================

if model.output_shape[-1] != len(class_names):

    raise ValueError(

        f"Model output has "
        f"{model.output_shape[-1]} classes, "
        f"but dataset has "
        f"{len(class_names)} classes."

    )


print(
    f"\nOutput correctly configured for "
    f"{len(class_names)} classes."
)


# ============================================================
# CALLBACKS
# ============================================================

checkpoint = ModelCheckpoint(

    MODEL_PATH,

    monitor="val_accuracy",

    save_best_only=True,

    verbose=1

)


early_stopping = EarlyStopping(

    monitor="val_accuracy",

    patience=4,

    restore_best_weights=True,

    verbose=1

)


reduce_lr = ReduceLROnPlateau(

    monitor="val_loss",

    factor=0.5,

    patience=2,

    min_lr=1e-7,

    verbose=1

)


# ============================================================
# TRAIN
# ============================================================

print("\n" + "=" * 70)
print("STARTING TRAINING")
print("=" * 70)

print("\nSettings:")

print(
    "Image size:",
    IMG_SIZE
)

print(
    "Batch size:",
    BATCH_SIZE
)

print(
    "Epochs:",
    EPOCHS
)

print(
    "Number of classes:",
    len(class_names)
)

print(
    "Total images:",
    total_images
)

print("\nPlease wait...")


history = model.fit(

    train_ds,

    validation_data=val_ds,

    epochs=EPOCHS,

    callbacks=[
        checkpoint,
        early_stopping,
        reduce_lr
    ]

)


# ============================================================
# LOAD BEST MODEL
# ============================================================

print("\n" + "=" * 70)
print("LOADING BEST MODEL")
print("=" * 70)


best_model = tf.keras.models.load_model(

    MODEL_PATH,

    compile=False

)


# ============================================================
# FINAL MODEL CHECK
# ============================================================

print("\nFinal model input shape:")

print(
    best_model.input_shape
)


print("\nFinal model output shape:")

print(
    best_model.output_shape
)


if (
    best_model.output_shape[-1]
    != len(class_names)
):

    raise ValueError(

        "Model class count does not "
        "match class file."

    )


# ============================================================
# SAVE FINAL MODEL
# ============================================================

best_model.save(
    MODEL_PATH
)


print("\nModel saved successfully:")

print(
    MODEL_PATH
)


# ============================================================
# TEST PREDICTION
# ============================================================

print("\n" + "=" * 70)
print("TESTING MODEL")
print("=" * 70)


for images, labels in val_ds.take(1):

    predictions = best_model.predict(

        images,

        verbose=0

    )


    print("\nPrediction tensor shape:")

    print(
        predictions.shape
    )


    predicted_indexes = np.argmax(

        predictions,

        axis=1

    )


    for i in range(
        min(10, len(predicted_indexes))
    ):

        predicted_index = (
            predicted_indexes[i]
        )


        actual_index = (
            labels[i].numpy()
        )


        predicted_class = (
            class_names[predicted_index]
        )


        actual_class = (
            class_names[actual_index]
        )


        confidence = (

            float(
                predictions[
                    i
                ][
                    predicted_index
                ]
            )

            * 100

        )


        print(
            f"\nImage {i + 1}"
        )


        print(
            "Actual    :",
            actual_class
        )


        print(
            "Predicted :",
            predicted_class
        )


        print(
            "Confidence:",
            f"{confidence:.2f}%"
        )


# ============================================================
# FINAL INFORMATION
# ============================================================

print("\n" + "=" * 70)
print("TRAINING COMPLETED")
print("=" * 70)


print("\nModel:")

print(
    MODEL_PATH
)


print("\nClass file:")

print(
    CLASS_FILE
)


print("\nClass JSON:")

print(
    CLASS_JSON
)


print("\nNumber of classes:")

print(
    len(class_names)
)


print("\nImage size:")

print(
    IMG_SIZE
)


print("\nKisanVision360 disease model is ready.")

print("=" * 70)
