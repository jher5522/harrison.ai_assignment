import sqlite3
import os
from glob import glob
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash


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

def insert_image_data(cur):
	data_dir = Path(__file__).absolute().parent.parent.joinpath('static', 'images')
	for image_name in data_dir.rglob("*.jpeg"):
		image_path = image_name.relative_to(data_dir)
		cur.execute(f"INSERT INTO Images (image_path) VALUES ('{image_path}')")

def insert_users_data(cur):
	example_users = (
		('rock_god_9000', 'Jimi', 'Hendrix', generate_password_hash('voodoochild')),
		('marko', 'Mark', 'Twain', generate_password_hash('booksRgood')),
		('noot_noot', 'George', 'Bush', generate_password_hash('i_r_winner'))
		)
	for user_name, first, last, pwd_hash in example_users:
		cur.execute(f"""INSERT INTO Users (username, first_name, last_name, pwd_hash) 
			VALUES ('{user_name}', '{first}', '{last}', '{pwd_hash}')""")

def insert_labels_data(cur):
	example_labels = (
		(1, "rock_god_9000", 'Tumor', 'Top left'),
		(3, "rock_god_9000", 'Cyst', 'Middle'),
		(2, "noot_noot", 'Fracture', 'Bottom'),
		(1, "noot_noot", 'Toe', 'In stomach')
		)
	for example in example_labels:
		cur.execute(f"""INSERT INTO Labels (image_id, labelled_by, annotation, geometry) 
			VALUES ({example[0]}, '{example[1]}', '{example[2]}', '{example[3]}')""")

def create_db(db_file):
	# remove existing db file, create fresh one
	if os.path.exists(db_file):
		os.remove(db_file)

	conn = sqlite3.connect(db_file)
	cur = conn.cursor()

	create_tables(cur)
	insert_image_data(cur)
	insert_users_data(cur)
	insert_labels_data(cur)
	conn.commit()

if __name__ == '__main__':
	db_file = Path(__file__).absolute().parent.joinpath('image_db.sqlite')
	create_db(db_file)

	conn = sqlite3.connect(db_file)
	cur = conn.cursor()
	print(cur.execute('SELECT * FROM Images').fetchall())
	print(cur.execute('SELECT * FROM Users').fetchall())
	print(cur.execute('SELECT * FROM Labels').fetchall())
	print(cur.execute(f"SELECT pwd_hash FROM Users WHERE username='rock_god_9000'").fetchone()[0])