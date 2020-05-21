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

## Data

Images: (image_id, image_path)
Users: (user_id, first_name, last_name)
Classes: (class_id, name)
Labels: (label_id, image_id, labelled_by, class_id, geometry)

## Geometries
Shapely multipolygons. Stored in db as multipolygon wkt. Pixel coordinates. Would need to be updated if image size or resolution was changed. Can be easily read in with shapely (eg. ` shapely.wkt.loads('MULTIPOLYGON (((1234 0, 1222 5, 1000 10, 1234 0)), ((9 4, 3 9, 1 4, 0 1, 9 4)))')`).


## TODO:
Log removal instead of actually delete
Parameterise tests
Check new images have image extension
Add more constraints to db structure. Eg NOT NULL

don't use fstrings to create sql querys, use prepared statements and send tuple of args
Delete labels when you delete an image