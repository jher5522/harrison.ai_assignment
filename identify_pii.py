from PIL import Image
import pytesseract
import string

# list of suspicious words. 
suspicious_words = set(['name', 'dob', 'd.o.b.', 'address']) # headers for ppi
with open('names.txt') as f:  # common names
	names = set([line.rstrip('\n').lower() for line in f])
suspicious_words.update(names)

def _extract_words(im_path):
	# get words from image using tesseract
	im = Image.open(im_path)
	text = pytesseract.image_to_string(im)

	# remove punctutation and split into set of words
	clean_text = text.lower().translate(str.maketrans('', '', string.punctuation))
	words = set(clean_text.split())
	return words

def check_for_pii(im_path):
	# check if there are any words on the image
	words = _extract_words(im_path)

	if words is None:
		# if there are no words, its fine
		return False

	if (words & suspicious_words):
		# if there are any suspicious words report it
		return True

	# if none of the words are suspicious, its fine
	return False
