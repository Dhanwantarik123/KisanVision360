import tensorflow as tf

from tensorflow.keras.preprocessing.image import ImageDataGenerator

from tensorflow.keras.models import Sequential

from tensorflow.keras.layers import (
    Conv2D,
    MaxPooling2D,
    Flatten,
    Dense,
    Dropout
)

import json
import os



# DATASET PATH

dataset_path = "/home/dhanwantari/KisanVision360/dataset"



IMG_SIZE = 224

BATCH_SIZE = 32




# IMAGE AUGMENTATION


datagen = ImageDataGenerator(

    rescale=1./255,

    validation_split=0.2,

    rotation_range=25,

    zoom_range=0.2,

    horizontal_flip=True

)





# TRAIN DATA


train_data = datagen.flow_from_directory(

    dataset_path,

    target_size=(IMG_SIZE,IMG_SIZE),

    batch_size=BATCH_SIZE,

    class_mode="categorical",

    subset="training"

)






# VALIDATION DATA


val_data = datagen.flow_from_directory(

    dataset_path,

    target_size=(IMG_SIZE,IMG_SIZE),

    batch_size=BATCH_SIZE,

    class_mode="categorical",

    subset="validation"

)






print("\nDisease Classes:")

print(train_data.class_indices)







# CNN MODEL


model = Sequential()



model.add(
Conv2D(
32,
(3,3),
activation="relu",
input_shape=(224,224,3)
)
)


model.add(MaxPooling2D())



model.add(
Conv2D(
64,
(3,3),
activation="relu"
)
)


model.add(MaxPooling2D())



model.add(
Conv2D(
128,
(3,3),
activation="relu"
)
)


model.add(MaxPooling2D())



model.add(Flatten())



model.add(
Dense(
128,
activation="relu"
)
)


model.add(
Dropout(0.5)
)



model.add(
Dense(
len(train_data.class_indices),
activation="softmax"
)
)






model.compile(

optimizer="adam",

loss="categorical_crossentropy",

metrics=["accuracy"]

)







# TRAIN


model.fit(

train_data,

validation_data=val_data,

epochs=20

)








# SAVE MODEL


os.makedirs(
"ai_models",
exist_ok=True
)



model.save(
"ai_models/disease_model.h5"
)






# SAVE LABELS


labels = train_data.class_indices



with open(
"ai_models/classes.json",
"w"
) as f:

    json.dump(
        labels,
        f
    )




print("\nMODEL TRAINING COMPLETED")

print("Saved:")
print("ai_models/disease_model.h5")
print("ai_models/classes.json")
