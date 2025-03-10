from rembg import remove
from PIL import Image

# Define input and output paths
input_path = "Image.jpg"
output_path = "Removed_bashar.jpg"

try:
    # Open image
    img = Image.open(input_path)

    # Remove background
    output = remove(img)

    # Convert to RGB if needed
    if output.mode == "RGBA":
        white_bg = Image.new("RGB", output.size, (255, 255, 255))  # White background
        white_bg.paste(output, mask=output.split()[3])  # Apply transparency mask
        output = white_bg  # Replace the image with the new one

    # Save as JPG
    output.save(output_path, "JPEG")

    print(f"✅ Background removed and saved as: {output_path}")

except FileNotFoundError:
    print(f"❌ Error: The file '{input_path}' was not found.")
except Exception as e:
    print(f"❌ An error occurred: {e}")
