import argparse
import cv2
import sys
from paddleocr import PaddleOCR, draw_ocr
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import os
import pytesseract

def preprocess_image(image_path, scale=3.0):  # Increase scale to make text bigger
    """
    Preprocess the image to enhance OCR accuracy.
    """
    # Load the image using OpenCV
    image = cv2.imread(image_path)

    if image is None:
        print(f"Error: Unable to load image at {image_path}")
        sys.exit(1)

    # Resize the image to make text more readable
    image = resize_image(image, scale=scale)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Increase contrast to make text stand out
    gray = enhance_contrast(gray)

    # Deskew the image
    deskewed = deskew(image)
    gray_deskewed = cv2.cvtColor(deskewed, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding with adjusted parameters
    thresh = cv2.adaptiveThreshold(
        gray_deskewed, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 12  # Experiment with these values
    )

    # Morphological operations to keep text regions sharp and separate
    kernel = np.ones((2, 2), np.uint8)  # Smaller kernel size
    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)

    # Save the processed image for debugging
    processed_image_path = 'processed_image.png'
    cv2.imwrite(processed_image_path, processed)
    print(f"Processed image saved to {processed_image_path}")

    return processed



def resize_image(image, scale=2.0):
    """
    Resize the image by the given scale factor.
    """
    width = int(image.shape[1] * scale)
    height = int(image.shape[0] * scale)
    resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)
    return resized

def enhance_contrast(gray_image):
    """
    Enhance the contrast of the grayscale image using CLAHE.
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray_image)
    return enhanced

def deskew(image, max_angle=15.0):
    """
    Corrects the skew of an image, limiting the maximum deskew angle.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    coords = np.column_stack(np.where(gray > 0))
    if coords.size == 0:
        print("Warning: No text detected for deskewing.")
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    # Limit the deskew angle to avoid excessive rotation
    if abs(angle) > max_angle:
        angle = max_angle if angle > 0 else -max_angle
        print(f"Deskew angle {angle:.2f} exceeds maximum. Capped to {max_angle} degrees.")
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    print(f"Image deskewed by {angle:.2f} degrees.")
    return rotated


def perform_paddleocr(processed_image, ocr_model):
    """
    Perform OCR on the preprocessed image using PaddleOCR.
    """
    # Convert the processed OpenCV image to RGB format
    rgb_image = cv2.cvtColor(processed_image, cv2.COLOR_GRAY2RGB)

    # Perform OCR
    results = ocr_model.ocr(rgb_image, rec=True, cls=True)

    # Print the complete structure of results for debugging
    print("OCR Results Structure:")
    for result in results:
        print(result)

    # Initialize extracted_text as an empty string to accumulate results from each line
    extracted_text = ""

    # Loop through each detected line
    for idx, line in enumerate(results):
        print(f"\nProcessing Line {idx + 1}: {line}")

        # Check if the line has the nested structure we expect
        if len(line) > 0 and isinstance(line[0], list) and len(line[0]) >= 2:
            bounding_box, text_conf = line[0]  # Access the bounding box and text-confidence tuple

            # Extract the text and confidence if they are in the correct format
            if isinstance(text_conf, tuple) and len(text_conf) == 2:
                text = text_conf[0]
                confidence = text_conf[1]

                # Print for debugging
                print(f"Extracted Text: {text}, Confidence: {confidence}")

                # Append each line to extracted_text with a newline character
                extracted_text += text + '\n'
            else:
                print(f"Unexpected text-confidence structure for line {idx + 1}: {text_conf}")
        else:
            print(f"Unexpected structure for line {idx + 1}: {line}")

    return extracted_text.strip()  # Return all extracted text as a single string


def perform_tesseract_ocr(processed_image):
    """
    Perform OCR using Tesseract on the preprocessed image.
    """
    # Convert OpenCV image to PIL format
    pil_image = Image.fromarray(processed_image)

    # Perform OCR with Japanese language
    extracted_text = pytesseract.image_to_string(pil_image, lang='jpn')

    print("\nTesseract OCR - Extracted Text:\n")
    print(extracted_text)
    print("\n----------------------\n")

    return extracted_text.strip()

def visualize_ocr_results(original_image_path, processed_image, ocr_model, output_image_path, font_path):
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
    image_with_boxes = draw_ocr(image, boxes, txts, scores, font_path=font_path)
    image_with_boxes = Image.fromarray(image_with_boxes)

    # Save the visualized image
    image_with_boxes.save(output_image_path)
    print(f"OCR results visualized and saved to {output_image_path}")

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

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Extract Japanese text from an image using PaddleOCR and Tesseract.')
    parser.add_argument('-o', '--output', type=str, help='Path to save the extracted text. If not provided, text will be printed to the console.')
    parser.add_argument('-v', '--visualize', action='store_true', help='Visualize OCR results by drawing bounding boxes and text on the image.')
    parser.add_argument('-ov', '--output_image', type=str, help='Path to save the visualized OCR image. Required if --visualize is set.')
    parser.add_argument('--use_gpu', action='store_true', help='Use GPU for OCR (requires compatible GPU and proper setup).')
    parser.add_argument('--tesseract', action='store_true', help='Use Tesseract OCR in addition to PaddleOCR.')
    parser.add_argument('--font_path', type=str, help='Path to a Japanese-supporting .ttf or .ttc font for visualization.')

    args = parser.parse_args()


    # Initialize PaddleOCR Reader for Japanese
    print("Initializing PaddleOCR model...")
    try:
        ocr_model = PaddleOCR(lang='japan', cls=True)  # 'japan' is the language code for Japanese
    except Exception as e:
        print(f"Error initializing PaddleOCR: {e}")
        sys.exit(1)

    # Preprocess the image
    print("Preprocessing the image...")
    processed_image = preprocess_image('screenshot.png', scale=2.0)

    # Perform PaddleOCR
    print("Performing PaddleOCR...")
    extracted_text_paddle = perform_paddleocr(processed_image, ocr_model)

    # Perform Tesseract OCR if requested
    if args.tesseract:
        print("Performing Tesseract OCR...")
        extracted_text_tesseract = perform_tesseract_ocr(processed_image)
        # Combine both OCR results
        combined_text = extracted_text_paddle + '\n' + extracted_text_tesseract
    else:
        combined_text = extracted_text_paddle

    # Save or print the extracted text
    if args.output:
        save_extracted_text(combined_text, args.output)
    else:
        print("\n--- Extracted Text ---\n")
        print(combined_text)
        print("\n----------------------\n")

    # Visualize OCR results if requested
    if args.visualize:
        if not args.output_image:
            print("Error: --output_image must be specified when using --visualize.")
            sys.exit(1)
        if not args.font_path:
            print("Error: --font_path must be specified when using --visualize.")
            sys.exit(1)
        print("Visualizing OCR results...")
        visualize_ocr_results(args.image_path, processed_image, ocr_model, args.output_image, args.font_path)

if __name__ == '__main__':
    main()
