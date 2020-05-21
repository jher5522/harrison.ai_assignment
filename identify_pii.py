import string

from PIL import Image


# list of suspicious words. 
suspicious_words = {'name', 'dob', 'd.o.b.', 'address'} # headers for ppi
with open('names.txt') as f:  # common names
    names = {line.rstrip('\n').lower() for line in f}
suspicious_words.update(names)

def _extract_words(im_path):
    try:
        import pytesseract
    except ModuleNotFoundError:
        return True

    # get words from image using tesseract
    im = Image.open(im_path)
    text = pytesseract.image_to_string(im)

    # remove punctutation and split into set of words
    clean_text = text.lower().translate(str.maketrans('', '', string.punctuation))
    words = set(clean_text.split())
    return words

def _check_words_suspect(words):
    if words is None:
        # if there are no words, its fine
        return False

    if (set(words) & suspicious_words):
        # if there are any suspicious words report it
        return True

    # if none of the words are suspicious, its fine
    return False

def check_for_pii(im_path):
    # check if there are any words on the image
    words = _extract_words(im_path)

    return _check_words_suspect(words)
