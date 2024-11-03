import argparse
import cv2
import sys
from paddleocr import PaddleOCR, draw_ocr
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import os

def preprocess_image(image_path):
    """
    Preprocess the image to enhance OCR accuracy.
    Steps:
    1. Convert to grayscale
    2. Apply bilateral filter for noise reduction while keeping edges sharp
    3. Apply adaptive thresholding
    4. Perform morphological operations to enhance text regions
    """
    # Load the image using OpenCV
    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: Unable to load image at {image_path}")
        sys.exit(1)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter to reduce noise while keeping edges sharp
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        filtered, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 2
    )

    # Morphological operations to enhance text regions
    kernel = np.ones((3,3), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)

    return processed

def perform_ocr(processed_image, ocr_model):
    """
    Perform OCR on the preprocessed image using PaddleOCR.
    """
    # Convert the processed OpenCV image to RGB format
    rgb_image = cv2.cvtColor(processed_image, cv2.COLOR_GRAY2RGB)

    # Perform OCR
    results = ocr_model.ocr(rgb_image, rec=True, cls=False)

    extracted_text = ""
    for line in results:
        for word_info in line:
            extracted_text += word_info[1][0] + ' '

    return extracted_text.strip()

def save_extracted_text(extracted_text, output_path):
    """
    Save the extracted text to a file.
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        print(f"Extracted text saved to {output_path}")
    except Exception as e:
        print(f"Error writing to file {output_path}: {e}")

def visualize_ocr_results(original_image_path, processed_image, ocr_model, output_image_path):
    """
    Visualize OCR results by drawing bounding boxes and text on the original image.
    """
    # Perform OCR to get bounding boxes
    result = ocr_model.ocr(processed_image, rec=True, cls=False)

    # Load the original image
    image = Image.open(original_image_path).convert('RGB')

    # Draw OCR results
    boxes = [line[0] for line in result]
    txts = [line[1][0] for line in result]
    scores = [line[1][1] for line in result]
    im_show = draw_ocr(image, boxes, txts, scores, font_path='path_to_japanese_font.ttf')  # Replace with path to a Japanese font
    im_show = Image.fromarray(im_show)

    # Save the visualized image
    im_show.save(output_image_path)
    print(f"OCR results visualized and saved to {output_image_path}")

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Extract Japanese text from an image using PaddleOCR.')
    parser.add_argument('-o', '--output', type=str, help='Path to save the extracted text. If not provided, text will be printed to the console.')
    parser.add_argument('-v', '--visualize', action='store_true', help='Visualize OCR results by drawing bounding boxes and text on the image.')
    parser.add_argument('-ov', '--output_image', type=str, help='Path to save the visualized OCR image. Required if --visualize is set.')
    parser.add_argument('--use_gpu', action='store_true', help='Use GPU for OCR (requires compatible GPU and proper setup).')

    args = parser.parse_args()

    # Initialize PaddleOCR Reader for Japanese
    print("Initializing PaddleOCR model...")
    try:
        ocr_model = PaddleOCR(lang='japan')  # 'japan' is the language code for Japanese in PaddleOCR
    except Exception as e:
        print(f"Error initializing PaddleOCR: {e}")
        sys.exit(1)

    # Preprocess the image
    print("Preprocessing the image...")
    processed_image = preprocess_image('screenshot.png')

    # Perform OCR
    print("Performing OCR...")
    extracted_text = perform_ocr(processed_image, ocr_model)

    if not extracted_text:
        print("No text detected.")
    else:
        if args.output:
            save_extracted_text(extracted_text, args.output)
        else:
            print("\n--- Extracted Text ---\n")
            print(extracted_text)
            print("\n----------------------\n")

    # Visualize OCR results if requested
    if args.visualize:
        if not args.output_image:
            print("Error: --output_image must be specified when using --visualize.")
            sys.exit(1)
        print("Visualizing OCR results...")
        visualize_ocr_results(args.image_path, processed_image, ocr_model, args.output_image)

if __name__ == '__main__':
    main()
