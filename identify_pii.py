from PIL import Image
import pytesseract
import string

suspicious_words = set(['name', 'dob', 'd.o.b.'])
with open('names.txt') as f:
	names = set([line.rstrip('\n').lower() for line in f])
suspicious_words.update(names)

def _extract_words(im_path):
	im = Image.open(im_path)
	text = pytesseract.image_to_string(im)
	clean_text = text.lower().translate(str.maketrans('', '', string.punctuation))
	words = set(clean_text.split())
	return words

def check_for_pii(im_path):
	words = _extract_words(im_path)

	if words is None:
		return False

	if (words & suspicious_words):
		return True

	return False
