import os
import csv

from glob import glob
from pathlib import Path
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


## insert data
def psv_to_list_dicts(data_psv):
    with open(data_psv, 'r') as f:
        data = list(map(dict, csv.DictReader(f, skipinitialspace=True, delimiter="|")))
    return data

def insert_test_data(cur, users_psv, labels_psv, classes_psv):
    insert_image_data(cur)
    insert_users_data(cur, users_psv=users_psv)
    insert_classes_data(cur, classes_psv=classes_psv)
    insert_labels_data(cur, labels_psv=labels_psv)

def insert_image_data(cur):
    insertion_query = """
        INSERT INTO Images (image_path, deleted, contains_pii) 
        VALUES (:im_path, :deleted, 0)
    """

    # Insert every jpeg in the static/images folder into the db
    data_dir = Path(__file__).absolute().parent.parent.joinpath('static', 'images')
    for image_name in sorted(data_dir.rglob("*.jpeg")):
        image_path = image_name.relative_to(data_dir)
        cur.execute(insertion_query, {'im_path': str(image_path), 'deleted': 0})
    cur.execute(insertion_query, {'im_path': str(image_path), 'deleted': 1})


def insert_users_data(cur, users_psv):
    data = psv_to_list_dicts(users_psv)
    insert_users_query = """
        INSERT INTO Users (username, first_name, last_name, pwd_hash) 
            VALUES (:username, :first_name, :last_name, :hash)
        """

    for row in data:
        pwd_hash = generate_password_hash(row['password'])
        row.update({'hash': pwd_hash})
        cur.execute(insert_users_query, row)

def insert_classes_data(cur, classes_psv):
    data = psv_to_list_dicts(classes_psv)
    insert_class_query = """
        INSERT INTO Classes (name)
        VALUES (:name)
        """

    for row in data:
        cur.execute(insert_class_query, row)

def insert_labels_data(cur, labels_psv):
    data = psv_to_list_dicts(labels_psv)
    insert_label_query = """
        INSERT INTO Labels (image_id, labelled_by, class_id, geometry, deleted) 
        VALUES (:image_id, :labelled_by, :class_id, :geometry, :deleted)
        """

    for row in data:
        cur.execute(insert_label_query, row)



### Create the DB
def create_tables(cur):
    cur.execute('''
        CREATE TABLE Images 
        (image_id INTEGER PRIMARY KEY AUTOINCREMENT, 
        image_path TEXT,
        deleted INTEGER,
        contains_pii INTEGER)
        ''')
    cur.execute('''
        CREATE TABLE Users 
        (username TEXT PRIMARY KEY,
        first_name TEXT, 
        last_name TEXT,
        pwd_hash TEXT)
        ''')
    cur.execute('''CREATE TABLE Classes
        (class_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT)
        ''')
    cur.execute('''CREATE TABLE Labels 
        (label_id INTEGER PRIMARY KEY AUTOINCREMENT, 
        image_id INTEGER, 
        labelled_by INTEGER,
        class_id INTEGER,
        geometry TEXT,
        deleted INTEGER,
        FOREIGN KEY(image_id) REFERENCES Images(image_id),
        FOREIGN KEY(labelled_by) REFERENCES Users(username),
        FOREIGN KEY(class_id) REFERENCES Classes(class_id))
        ''')
    cur.execute('''CREATE TABLE Logs
        (log_id INTEGER PRIMARY KEY AUTOINCREMENT, 
        object TEXT,
        updated_by TEXT, 
        method TEXT, 
        image_id INTEGER, 
        label_id INTEGER, 
        modified_at TEXT,
        FOREIGN KEY(image_id) REFERENCES Images(image_id),
        FOREIGN KEY(label_id) REFERENCES Labels(label_id),
        FOREIGN KEY(updated_by) REFERENCES Users(username)
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
        users_psv=Path(__file__).absolute().parent.joinpath('test_users.psv'),
        labels_psv=Path(__file__).absolute().parent.joinpath('test_labels.psv'),
        classes_psv=Path(__file__).absolute().parent.joinpath('test_classes.psv')
        )
    conn.commit()


if __name__ == '__main__':
    db_file = Path(__file__).absolute().parent.joinpath('test_db.sqlite')
    create_db(db_file)

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    print(cur.execute('SELECT * FROM Images').fetchall())
    print(cur.execute('SELECT * FROM Users').fetchall())
    print(cur.execute('SELECT * FROM Classes').fetchall())
    print(cur.execute('SELECT * FROM Labels').fetchall())