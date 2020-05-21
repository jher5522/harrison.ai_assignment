# Harrison API Assignment
This is a set of APIs for managing the storage of medical images, and segmentation labels on those images.


## Main Features
 - Provides APIs for reading, inserting, deleting and updating images and labels
 - Logs changes (delete, insert, update) to images and labels in the database
 - Detects the presence of text based personal identifiable information (pii) in images, and logs the presense of ppi with the image
 - All APIs are password protected. Passwords are hashed and stored in the db.

## Dependencies
 - Python 3.7
 - Tesseract4
 - packages listed in requirements.txt

### Tesseract4
This package is used to identify text within an image. It is used for identifying personal information inside the images.

You need to install Tesseract4, as well as the python interface.

Ubuntu 18.0.0+ :
`sudo apt install tesseract-oct`

Older Ubuntu: 
`sudo add-apt-repository ppa:alex-p/tesseract-ocr
sudo apt-get update
sudo apt install tesseract-ocr`

Mac:
`brew install tesseract --HEAD` on mac. 

Python interface: 
`pip install pytesseract`


## Routes
image - GET, POST, DELETE

label - GET, POST, DELETE, PUT

## Data Storage
Data is stored in an SQLite database. The database contains the following tables

 - Images: (image_id, image_path, deleted)
 - Users: (user_id, first_name, last_name, pwd_hash)
 - Classes: (class_id, name)
 - Labels: (label_id, image_id, labelled_by, class_id, geometry, deleted)
 - Log: (user_id, method, image_id, label_id, modified_at)

The API does not handle the storage of images, it only mantains a path to their location. New images need to be added to the `static/images` folder before adding the image to the db.

A label is a multipolygon associated with a single class. You can have multiple labels for a single image. Labels are stored in the database in well-known text (wkt) format. This label storage is independent of hte coordinate system used for defining the labels. 

The `Log` table tracks insertions, deletions and updates to labels or images. It only stores when the change occured, who performed it, and what type of update it was on which table. This is insufficient information to revert changes, but it is enough to track problems to a user. For the purpose of logging, nothing is ever deleted from the db. When you make a delete request, the image/label is marked as 'deleted', and won't be returned on a get request, but still exists in the db for future reference.

Each user has a password which allows them access to the APIs. The hash of their password is stored in the database.

## TODO:
Parameterise tests
Check new images have image extension
Add more constraints to db structure. Eg NOT NULL
Delete labels when you delete an image