from deep_translator import GoogleTranslator
from PIL import ImageGrab, ImageDraw, ImageFont
import pytesseract
from googletrans import Translator
# Set the path to Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def capture_and_translate():
    # Capture the screen
    screenshot = ImageGrab.grab()
    translator = Translator()
    translator.translate('안녕하세요.')

    # # Extract text from the image
    # extracted_text = pytesseract.image_to_string(screenshot)
    #
    # if extracted_text.strip():
    #     print("Extracted Text:", extracted_text)
    #
    #     # Translate the extracted text to English
    #     translated_text = GoogleTranslator(source='auto', target='en').translate(extracted_text)
    #     print("Translated Text:", translated_text)
    # else:
    #     print("No text detected.")

if __name__ == "__main__":
    capture_and_translate()
