import os
from PIL import Image

# ==============================
# PATHS
# ==============================
SOURCE_DIR = r"D:\KisanVision360\dataset_clean"
OUTPUT_DIR = r"D:\KisanVision360\dataset_filtered"

# ==============================
# SETTINGS
# ==============================
IMAGE_SIZE = (160, 160)
MIN_WIDTH = 50
MIN_HEIGHT = 50

VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

# ==============================
# CREATE OUTPUT FOLDER
# ==============================
os.makedirs(OUTPUT_DIR, exist_ok=True)

total = 0
processed = 0
skipped = 0

print("=" * 60)
print("DATASET FILTERING STARTED")
print("=" * 60)
print("Source :", SOURCE_DIR)
print("Output :", OUTPUT_DIR)
print("Size   :", IMAGE_SIZE)
print("=" * 60)

# ==============================
# PROCESS CLASS FOLDERS
# ==============================
for class_name in os.listdir(SOURCE_DIR):

    class_path = os.path.join(SOURCE_DIR, class_name)

    if not os.path.isdir(class_path):
        continue

    output_class_path = os.path.join(OUTPUT_DIR, class_name)
    os.makedirs(output_class_path, exist_ok=True)

    print("\nClass:", class_name)

    files = os.listdir(class_path)

    for filename in files:

        total += 1

        input_path = os.path.join(class_path, filename)
        output_name = os.path.splitext(filename)[0] + ".jpg"
        output_path = os.path.join(output_class_path, output_name)

        # Check extension
        if not filename.lower().endswith(VALID_EXTENSIONS):
            skipped += 1
            print("SKIP unsupported:", filename)
            continue

        try:
            # Open image
            with Image.open(input_path) as img:

                # Check image
                img.verify()

            # Open again because verify() closes image
            with Image.open(input_path) as img:

                # Convert to RGB
                img = img.convert("RGB")

                width, height = img.size

                # Remove extremely small images
                if width < MIN_WIDTH or height < MIN_HEIGHT:
                    skipped += 1
                    print("SKIP too small:", filename, img.size)
                    continue

                # Resize
                img = img.resize(
                    IMAGE_SIZE,
                    Image.Resampling.LANCZOS
                )

                # Save as compressed JPEG
                img.save(
                    output_path,
                    "JPEG",
                    quality=90,
                    optimize=True
                )

                processed += 1

        except Exception as e:
            skipped += 1
            print("SKIP bad image:", filename)
            print("Reason:", e)

    print(
        "Processed:",
        processed,
        "| Skipped:",
        skipped
    )

# ==============================
# FINAL RESULT
# ==============================
print("\n" + "=" * 60)
print("FILTERING COMPLETED")
print("=" * 60)

print("Total files :", total)
print("Processed   :", processed)
print("Skipped     :", skipped)
print("Output      :", OUTPUT_DIR)

print("=" * 60)
print("IMPORTANT:")
print("Your original dataset_clean was NOT changed.")
print("=" * 60)
