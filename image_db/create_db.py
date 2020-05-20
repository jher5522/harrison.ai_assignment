import sqlite3
import os
import csv
from glob import glob
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash





## insert data

def csv_to_list_dicts(data_csv):
	with open(data_csv, 'r') as f:
		data = [{k: v for k, v in row.items()}
			for row in csv.DictReader(f, skipinitialspace=True)]
	return data

def insert_test_data(cur, users_csv, labels_csv):
	insert_image_data(cur)
	insert_users_data(cur, users_csv=users_csv)
	insert_labels_data(cur, labels_csv=labels_csv)

def insert_image_data(cur):
	# Insert every jpeg in the static/images folder into the db
	data_dir = Path(__file__).absolute().parent.parent.joinpath('static', 'images')
	for image_name in sorted(data_dir.rglob("*.jpeg")):
		image_path = image_name.relative_to(data_dir)
		cur.execute(f"INSERT INTO Images (image_path) VALUES ('{image_path}')")

def insert_users_data(cur, users_csv):
	data = csv_to_list_dicts(users_csv)
	
	for row in data:
		cur.execute(f"""INSERT INTO Users (username, first_name, last_name, pwd_hash) 
			VALUES (
			'{row['user_name']}', 
			'{row['first_name']}', 
			'{row['last_name']}', 
			'{generate_password_hash(row['password'])}'
			)""")

def insert_labels_data(cur, labels_csv):
	data = csv_to_list_dicts(labels_csv)

	for row in data:
		cur.execute(f"""INSERT INTO Labels (image_id, labelled_by, annotation, geometry) 
			VALUES ({int(row['image_id'])}, '{row['labelled_by']}', '{row['annotation']}', '{row['geometry']}')""")



### Create the DB

def create_tables(cur):
	cur.execute('''
		CREATE TABLE Images 
		(image_id INTEGER PRIMARY KEY AUTOINCREMENT, 
		image_path text)
		''')
	cur.execute('''
		CREATE TABLE Users 
		(username text PRIMARY KEY,
		first_name text, 
		last_name text,
		pwd_hash text)
		''')
	cur.execute('''CREATE TABLE Labels 
		(label_id INTEGER PRIMARY KEY AUTOINCREMENT, 
		image_id INTEGER, 
		labelled_by int,
		annotation text,
		geometry text,
		FOREIGN KEY(image_id) REFERENCES Images(image_id),
		FOREIGN KEY(labelled_by) REFERENCES Users(username)
		)''')
	return


def create_db(db_file):
	# remove existing db file, create fresh one
	if os.path.exists(db_file):
		os.remove(db_file)

	conn = sqlite3.connect(db_file)
	cur = conn.cursor()

	create_tables(cur)
	insert_test_data(cur, 
		users_csv=Path(__file__).absolute().parent.joinpath('test_users.csv'),
		labels_csv=Path(__file__).absolute().parent.joinpath('test_labels.csv')
		)
	conn.commit()


if __name__ == '__main__':
	db_file = Path(__file__).absolute().parent.joinpath('test_db.sqlite')
	create_db(db_file)

	conn = sqlite3.connect(db_file)
	cur = conn.cursor()
	print(cur.execute('SELECT * FROM Images').fetchall())
	print(cur.execute('SELECT * FROM Users').fetchall())
	print(cur.execute('SELECT * FROM Labels').fetchall())