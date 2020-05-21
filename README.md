# harrison.ai API Assignment
This is a set of APIs for managing the storage of medical images, and segmentation labels on those images. There is no front end for this application, just APIs. 


## Main Features
 - Provides APIs for reading, inserting, deleting and updating images and labels
 - Logs changes (delete, insert, update) to images and labels in the database
 - Detects the presence of text based personal identifiable information (pii) in images, and logs the presense of ppi with the image
 - All APIs are password protected. Passwords are hashed and stored in the db.

## Installation
Install the following dependencies

 - Python 3.7
 - Tesseract4 (futher info on installation below)
 - packages listed in requirements.txt

Clone this repo

`git clone https://github.com/jher5522/harrison_assignment.git`

### Tesseract4 Installation
This package is used to identify text within an image. It is used for identifying personal information inside the images. To install Tesseract4 check out their docs at https://github.com/tesseract-ocr/tesseract.

Ubuntu 18.0.0+ :
`sudo apt install tesseract-oct`

Mac:
`brew install tesseract --HEAD`

On older versions of Ubuntu (eg. my own machine): 
```
sudo add-apt-repository ppa:alex-p/tesseract-ocr
sudo apt-get update
sudo apt install tesseract-ocr
```

You also need to install the python interface: 
`pip install pytesseract`

If you are unable to install tesseral be unable to detect PII. It should fail the `TestCreateImage`, and `TestCheckForPII` but everything else will work. 

## How to run backend
Before calling any of the APIs, or running the test you need to have the backend running. For this it is assumed that its always running locally. To run the backend: 

`flask run`

Or you can run it in debug mode with:

`python app.py`


## Example data
You can populate the db with example data by running `python image_db/create_db.py`. This includes any images which are in the `static/images` folder, as well as a few example users. Testing makes use of the example user:

- name:  `Jimi Hendrix` 
- username: `rock_god_9000` 
- password: `voodoochild`. 

New users would need to added to the database directly, there is currently no API for that. 

## Usage
The available routes are:

image - GET, POST, DELETE

label - GET, POST, DELETE, PUT

All API requests return a json data package and a status code.

### Get image
Fetch data about a specific image. Fetch by image_id. Eg.

`curl --user [username]:[pwd] localhost:5000/image/1`

The expected result of this would be:

`{"image_id": 1, "image_path": "brain_jeff.jpeg", "contains_pii": 0}`

This `image_path` is always relative to the root images directory `static/images`. It does not return the image itself, but it points you to the location where the image is stored. You could get the image directly if you have access to the file system, or you could download it over the sever. Eg.

`wget localhost:5000/static/images/brain_jeff.jpeg`

`contains_pii` is the indicator as to whether this image has personal identification information present. It is `1` if it is present, `0` otherwise. 

### Delete image
Delete an image by image_id. Eg. 

`curl -X DELETE --user [username]:[pwd] localhost:5000/image/1`

This should return the deleted message Eg.

`{"message": "Image deleted"}`

You will no longer be able to fetch this image however it will still exist in the database with the `deleted` flag set to `1`.


### Insert image
This API does not accept the actual image, you need to put the image into the `static/images` directory yourself. This API inserts the reference to the image into the database so that it can tracked and labelled. Eg.

`curl -X POST -d "{'image_path': 'xray_image.jpeg'}" -H "Content-Type: application/json" --user [username]:[pwd] localhost:5000/image`

This should return the `image_id` which is automatically associated with this image. Eg.
`{"image_id": 8}`


### Get label
Fetch data about a specific label. Fetch by label_id. Currently not supported to get all the labels for a given image. Eg. 
`curl  --user [username]:[pwd] localhost:5000/label/1`

The expected result is:

`{"image_id": 1, "label_id": 1, "image_path": "brain_jeff.jpeg", "first_name": "Jimi", "last_name": "Hendrix", "username": "rock_god_9000", "class_id": 1, "geometry": "MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 45 20, 30 5, 10 10, 10 30, 20 35), (30 20, 20 25, 20 15, 30 20)))"}`

This contains information about the image which it was labelled on, and the user who did the labelling. In terms of the label itself, we have a `class_id` and `geometry`. The `class_id` tells us what has been labelled in a particular region. The name of the class is defined in the `Classes` table, which does not currently have API access. The `geometry` field tells us which region has been labelled. It is defined in wkt format, and can describe a collection of polygons. 


### Delete label
Delete a label by label_id. Eg. 

`curl -X DELETE --user [username]:[pwd] localhost:5000/label/1`

This should return the deleted message Eg.

`{"message": "Label deleted"}`

You will no longer be able to fetch this label however it will still exist in the database with the `deleted` flag set to `1`.


### Modify label
Change the class and/or geometry of a label. Access by label_id. Eg. 

`curl -X PUT --user [username]:[pwd] -d '{"geometry": "MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)))", "class_id":2}' -H "Content-Type: application/json" localhost:5000/label/1
'`

This will modify this label, to change the `geometry` and/or `class_id`.


### Insert label
Insert a new label. You need to specify the `class_id`, `geometry` and `image_id`. Eg.

`curl -X POST --user [username]:[pwd] -d "{'image_id': 2, 'class_id': 1, 'geometry': 'MULTIPOLYGON (((10 10, 20 25, 15 30, 10 10)))'}" -H "Content-Type application/json" localhost:5000/label`

When it's successful it'll return the new `label_id` with which its associated.Eg. 

`{'label_id': 6}` 


## How to run tests
There are test for all the API routes as well as some of the helper functions. These are all located in `test_apis.py`. They can be run with `pytest -v` or `python -m unittest test_apis.py`.

If you failed to install Tesseract4, then the tests for inserting images, and checking PII will fail, but everything else should still pass. 


## Data Storage
Data is stored in an SQLite database. The database contains the following tables

 - Images: (image_id, image_path, deleted)
 - Users: (user_id, first_name, last_name, pwd_hash)
 - Classes: (class_id, name)
 - Labels: (label_id, image_id, labelled_by, class_id, geometry, deleted)
 - Log: (user_id, method, image_id, label_id, modified_at)

The API does not handle the storage of images, it only mantains a path to their location. New images need to be added to the `static/images` folder before adding the image to the db.

A label is a a set of polygons associated with a single class. You can have multiple labels for a single image. Labels are stored in the database in well-known text (wkt) format as 'MULTIPOLYGON'. These strings can easily be interpretted as shapely.MultiPolygon (https://shapely.readthedocs.io/en/latest/manual.html#collections-of-polygons). This label storage is independent of the coordinate system used for defining the labels. 

The `Log` table tracks insertions, deletions and updates to labels or images. It only stores when the change occured, who performed it, and what type of update it was on which table. This is insufficient information to revert changes, but it is enough to track problems to a user. For the purpose of logging, nothing is ever deleted from the db. When you make a delete request, the image/label is marked as 'deleted', and won't be returned on a get request, but still exists in the db for future reference.

Each user has a password which allows them access to the APIs. The hash of their password is stored in the database.

## Personal Identifiable Information Detection
This detects pii by finding any text in the image, then searching for particular keywords in that text. Finding the words is performed using Tesseract4. The keywords are those which you would expect to indicate the presence of personal information such as 'name', or 'dob'. In addition the set of keywords includes a list of about 5000 common names. In general this aims to prefer flagging too many images, than to let pii slip through undetected. 