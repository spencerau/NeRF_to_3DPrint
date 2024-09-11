import os
import cv2
import torch
import requests
import argparse
import numpy as np
import pillow_heif
from PIL import Image
from tqdm import tqdm
from ultralytics import YOLO
from segment_anything import sam_model_registry, SamPredictor


SAM_MODEL_URL = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"
CHECKPOINT_NAME = "sam_vit_b_01ec64.pth"


# Function to download SAM checkpoint if it doesnt exist
def download_sam_checkpoint(checkpoint_path):
    if not os.path.exists(checkpoint_path):
        print(f"Checkpoint not found at {checkpoint_path}. Downloading SAM model...")
        
        response = requests.get(SAM_MODEL_URL, stream=True)
        total_size = int(response.headers.get('content-length', 0))

        # Download the model with progress
        with open(checkpoint_path, 'wb') as file, tqdm(
                desc=f"Downloading {CHECKPOINT_NAME}",
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)

        print(f"Downloaded checkpoint to {checkpoint_path}.")
    else:
        print(f"Checkpoint already exists at {checkpoint_path}.")


# Convert HEIC or unsupported image formats to PNG
def convert_to_png(image_path):
    # Check if the image format is HEIC or unsupported, and convert to PNG
    if image_path.lower().endswith(('.heic', '.heif')):
        heif_file = pillow_heif.read_heif(image_path)
        image = Image.frombytes(
            heif_file.mode, 
            heif_file.size, 
            heif_file.data, 
            "raw", 
            heif_file.mode, 
            heif_file.stride,
        )
        png_path = image_path.rsplit('.', 1)[0] + '.png'
        image.save(png_path, 'PNG')
        print(f"Converted {image_path} to {png_path}")
        return png_path
    return image_path  # If not HEIC/HEIF, return original path


# Function to downscale image to a given size (1920x1080)
def downscale_image(image, width=1920, height=1080):
    # Resize the image while maintaining aspect ratio
    original_height, original_width = image.shape[:2]
    scaling_factor = min(width / original_width, height / original_height)
    
    new_size = (int(original_width * scaling_factor), int(original_height * scaling_factor))
    resized_image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

    print(f"Resized image from {image.shape[:2]} to {resized_image.shape[:2]}")
    
    return resized_image


# Function to process images
def process_image(image_path, output_dir, use_segment):
    # Convert HEIC to PNG if necessary
    image_path = convert_to_png(image_path)

    # Load the image using OpenCV
    image = cv2.imread(image_path)
    if image is None:
        print(f"Could not read image {image_path}")
        return

    # Downscale the image to 1920x1080 resolution
    downscaled_image = downscale_image(image, 1920, 1080)

    # Save downscaled image
    downscaled_image_path = os.path.join(output_dir, f"{os.path.basename(image_path)}")
    cv2.imwrite(downscaled_image_path, downscaled_image)
    print(f"Saved downscaled image to {downscaled_image_path}")

    # Skip segmentation/detection if `--use_segment 0` is specified
    if not use_segment:
        return

    # Step 1: Use YOLOv8 for object detection
    model = YOLO('yolov8x.pt')  # Load pre-trained YOLOv8 model
    results = model(downscaled_image)
    boxes = results[0].boxes.xyxy  # Bounding boxes for detected objects

    if len(boxes) == 0:
        print(f"No objects detected in {image_path}")
        return

    # Step 2: Download SAM model checkpoint if not present
    sam_checkpoint = os.path.join(os.getcwd(), "models", CHECKPOINT_NAME)  # Path to save the checkpoint
    download_sam_checkpoint(sam_checkpoint)

    # Step 3: Load SAM model for segmentation
    sam = sam_model_registry["vit_b"](checkpoint=sam_checkpoint)
    sam.to(device='cuda' if torch.cuda.is_available() else 'cpu')

    predictor = SamPredictor(sam)
    predictor.set_image(downscaled_image)

    # Step 4: Iterate over detected bounding boxes, apply SAM, and remove background
    for i, bbox in enumerate(boxes):
        bbox_np = np.array(bbox.cpu())  # Convert the YOLO bounding box to a numpy array

        # Run SAM to get the segmentation mask for the object
        masks, _, _ = predictor.predict(box=bbox_np, multimask_output=False)
        mask = masks[0]

        # Convert the mask to a 3-channel image (for use with OpenCV)
        mask = (mask * 255).astype(np.uint8)
        mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        # Apply the mask to the original image to remove the background
        segmented_object = cv2.bitwise_and(downscaled_image, mask)

        # Save the segmented object
        output_image_path = os.path.join(output_dir, f"{i}_{os.path.basename(image_path)}")
        cv2.imwrite(output_image_path, segmented_object)

    print(f"Processed image {image_path}, results saved to {output_dir}")


# Process all images in a directory
def process_images_in_directory(input_dir, output_dir, use_segment):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for image_name in os.listdir(input_dir):
        if image_name.lower().endswith(('.jpg', '.jpeg', '.png', '.heic', '.heif')):  # Handle common formats and HEIC
            image_path = os.path.join(input_dir, image_name)
            process_image(image_path, output_dir, use_segment)


# Command-line argument parser
def parse_args():
    parser = argparse.ArgumentParser(description="Process images for object detection and segmentation.")
    parser.add_argument('--images', type=str, required=True, help="Path to the directory containing input images")
    parser.add_argument('--output', type=str, help="Path to the directory to save the processed images")
    parser.add_argument('--use_segment', type=int, default=1, help="Flag to use segmentation (1) or just downscale (0)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    input_dir = args.images 
    output_dir = args.output if args.output else input_dir
    use_segment = bool(args.use_segment)

    process_images_in_directory(input_dir, output_dir, use_segment)