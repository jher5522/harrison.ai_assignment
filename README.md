# Assignment

## Requirements
Python 3.7
see requirements.txt


## Routes
get_image
get_label
add_image
add_label
remove_image
remove_label
search_labels

REST

image - GET, POST, DELETE
label - GET, POST, DELETE, PUT
search - GET

## Data

Images: (image_id, image_path)
Users: (user_id, first_name, last_name)
Labels: (label_id, image_id, labelled_by, annotation, geometry)



## TODO:
Make geometry in labels table
Make class table which labels references
Log removal instead of actually delete
Parameterise tests
Check new images have image extension

don't use fstrings to create sql querys, use prepared statements and send tuple of args
Delete labels when you delete an image
Manage labelled_by when creating a new label

User registration
