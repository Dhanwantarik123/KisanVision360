import os
import shutil
import re

SOURCE = r"D:\KisanVision360\dataset"
DESTINATION = r"D:\KisanVision360\dataset_clean"

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".webp"
}


def safe_name(name):
    """
    Convert folder/file name to ASCII-safe name.
    """
    name = name.encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


print("=" * 70)
print("KISANVISION360 - CLEAN DATASET CREATION")
print("=" * 70)

if not os.path.exists(SOURCE):
    print("\nERROR: Source dataset not found:")
    print(SOURCE)
    raise SystemExit(1)

os.makedirs(DESTINATION, exist_ok=True)

class_folders = [
    folder
    for folder in os.listdir(SOURCE)
    if os.path.isdir(os.path.join(SOURCE, folder))
]

class_folders.sort()

print("\nOriginal classes found:", len(class_folders))

if len(class_folders) != 53:
    print("\nWARNING: Expected 53 classes.")
    print("Found:", len(class_folders))

total_images = 0
copied_images = 0
failed_images = 0

print("\n" + "=" * 70)
print("COPYING DATASET")
print("=" * 70)

for index, original_class in enumerate(class_folders):

    source_class_path = os.path.join(
        SOURCE,
        original_class
    )

    clean_class = safe_name(original_class)

    destination_class_path = os.path.join(
        DESTINATION,
        clean_class
    )

    os.makedirs(
        destination_class_path,
        exist_ok=True
    )

    class_count = 0

    for root, dirs, files in os.walk(source_class_path):

        for filename in files:

            extension = os.path.splitext(
                filename
            )[1].lower()

            if extension not in IMAGE_EXTENSIONS:
                continue

            total_images += 1

            source_file = os.path.join(
                root,
                filename
            )

            clean_filename = safe_name(filename)

            if not clean_filename:
                clean_filename = f"image_{class_count}.jpg"

            destination_file = os.path.join(
                destination_class_path,
                clean_filename
            )

            # Avoid duplicate filenames
            base, ext = os.path.splitext(
                destination_file
            )

            counter = 1

            while os.path.exists(destination_file):

                destination_file = (
                    f"{base}_{counter}{ext}"
                )

                counter += 1

            try:

                shutil.copy2(
                    source_file,
                    destination_file
                )

                copied_images += 1
                class_count += 1

            except Exception as error:

                failed_images += 1

                print(
                    "\nFAILED:",
                    source_file
                )

                print(
                    "ERROR:",
                    error
                )

    print(
        f"{index + 1:02d}/"
        f"{len(class_folders):02d} "
        f"{original_class} -> "
        f"{clean_class} : "
        f"{class_count} images"
    )


print("\n" + "=" * 70)
print("CLEAN DATASET COMPLETED")
print("=" * 70)

clean_classes = [
    folder
    for folder in os.listdir(DESTINATION)
    if os.path.isdir(
        os.path.join(DESTINATION, folder)
    )
]

clean_classes.sort()

print("\nOriginal classes :", len(class_folders))
print("Clean classes    :", len(clean_classes))
print("Images found     :", total_images)
print("Images copied    :", copied_images)
print("Failed images    :", failed_images)

print("\nClean dataset:")
print(DESTINATION)

print("\nClasses:")

for index, class_name in enumerate(clean_classes):

    print(
        f"{index:02d} -> {class_name}"
    )

if len(clean_classes) == 53:

    print("\nSUCCESS: 53 classes created.")

else:

    print(
        "\nWARNING: Clean dataset does not contain 53 classes."
    )

print("\n" + "=" * 70)
