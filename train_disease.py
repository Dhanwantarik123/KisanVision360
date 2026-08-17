import os
import tensorflow as tf

DATASET_DIR = r"D:\KisanVision360\dataset"

IMAGE_SIZE = (224, 224)

BATCH_SIZE = 32

EPOCHS = 10


# Load training data

train_data = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="training",
    seed=42,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE
)


# Load validation data

val_data = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="validation",
    seed=42,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE
)


# Get class names

class_names = train_data.class_names

print()
print("Classes:")

for i, name in enumerate(class_names):
    print(i, name)


# Model

model = tf.keras.Sequential([

    tf.keras.layers.Input(
        shape=(224, 224, 3)
    ),

    tf.keras.layers.Rescaling(
        1.0 / 255
    ),

    tf.keras.layers.Conv2D(
        32,
        3,
        activation="relu"
    ),

    tf.keras.layers.MaxPooling2D(),

    tf.keras.layers.Conv2D(
        64,
        3,
        activation="relu"
    ),

    tf.keras.layers.MaxPooling2D(),

    tf.keras.layers.Conv2D(
        128,
        3,
        activation="relu"
    ),

    tf.keras.layers.MaxPooling2D(),

    tf.keras.layers.Flatten(),

    tf.keras.layers.Dense(
        128,
        activation="relu"
    ),

    tf.keras.layers.Dropout(0.5),

    tf.keras.layers.Dense(
        len(class_names),
        activation="softmax"
    )

])


# Compile

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)


# Train

model.fit(
    train_data,
    validation_data=val_data,
    epochs=EPOCHS
)


# Create model folder

os.makedirs(
    r"D:\KisanVision360\ai_models",
    exist_ok=True
)


# Save model

model.save(
    r"D:\KisanVision360\ai_models\disease_model.keras"
)


# Save classes

with open(
    r"D:\KisanVision360\ai_models\disease_classes.txt",
    "w"
) as f:

    for name in class_names:
        f.write(name + "\n")


print()
print("================================")
print("TRAINING COMPLETED")
print("================================")

print("Model saved:")
print(r"D:\KisanVision360\ai_models\disease_model.keras")