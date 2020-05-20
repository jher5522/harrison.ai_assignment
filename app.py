from flask import Flask, render_template, request, g
import sqlite3
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from pathlib import Path


STATUS_OK = 200
STATUS_BAD_REQUEST = 400
STATUS_NOT_FOUND = 410
STATUS_INTERNAL_ERROR = 500


app = Flask(__name__)
auth = HTTPBasicAuth()


@app.route('/')
@auth.login_required
def search_bar():
	cur, conn = get_db()
	all_images = cur.execute(f"SELECT image_id, image_path FROM Images").fetchall()
	return render_template("home.html", images=all_images) 



@app.route('/image/<int:image_id>', methods=["GET", "DELETE"])
@app.route('/image', methods=["POST"])
@auth.login_required
def image(image_id=None):
	print("in image")
	cur, conn = get_db()
	
	if request.method == "GET":
		result = cur.execute(f"SELECT image_id, image_path FROM Images WHERE image_id={image_id}").fetchone()
		if result is None:
			return "Image not found", 410

		image_id, image_path = result
		return json.dumps({'image_id': image_id, 'image_path': image_path})
	

	elif request.method ==  "DELETE":
		r = cur.execute(f"DELETE FROM Images WHERE image_id={image_id}")
		if r.rowcount ==0:
			return "Nothing to delete", STATUS_NOT_FOUND
		conn.commit()
		return "deleted"


	elif request.method == 'POST':
		print(request.values)
		# To insert a new image into the db, you should copy the image into the 'static/images' directory
		# and use this API to insert it into the db
		image_path = request.values.to_dict()['image_dir']
		print(image_path)

		# check its in static/images
		images_dir = Path(__file__).absolute().parent.joinpath('static', 'images')
		provided_path = Path(image_path).absolute()
		if not images_dir in provided_path.parents:
			return "Image should be in a direcotry within static/images", STATUS_BAD_REQUEST

		# check this file exists
		if os.path.exists(image_path):
			return "Image does not exist at specified path", STATUS_BAD_REQUEST

		# insert row
		rel_image_path = str(image_path.relative_to(images_dir))
		r = cur.execute(f"INSERT INTO Images (image_path) VALUES ('{image_path}')")

		# check it worked
		if r.rowcount == 0:
			return "Problem inserting new image", STATUS_INTERNAL_ERROR

		image_id = cur.execute(f"SELECT last_insert_rowid() FROM Images").fetchone()
		conn.commit()

		return json.dumps({'image_id': image_id}), STATUS_OK


@app.route('/label/<int:label_id>', methods=['GET', 'DELETE'])
@app.route('/label', methods=["POST"])
@auth.login_required
def label(label_id=None):
	cur, conn = get_db()

	if request.method == "GET":
		result = cur.execute(f"""
			SELECT image_id, image_path, first_name, last_name, annotation, geometry
			FROM Labels 
			JOIN Images USING(image_id) 
			JOIN Users ON labels.labelled_by = users.username 
			WHERE label_id={label_id}""").fetchone()
		if result is None:
			return "Label not found", STATUS_NOT_FOUND

		image_id, image_path, first_name, last_name, annotation, geometry = result

		return json.dumps(
			dict( 
				label_id=label_id,
				image_id=image_id, 
				image_path=image_path, 
				first_name=first_name, 
				last_name=last_name, 
				annotation=annotation, 
				geometry=geometry
				)
			)


	elif request.method=='DELETE':
		cur, conn = get_db()
		r = cur.execute(f"DELETE FROM Labels WHERE label_id={label_id}")
		if r.rowcount == 0:
			return "Nothing to delete", STATUS_NOT_FOUND
		conn.commit()
		return "Label deleted"


	elif request.method=='POST':
		data = request.form.to_dict()

		r = cur.execute(
			f"""INSERT INTO Labels (image_id, labelled_by, annotation, geometry) 
				VALUES ({data['image_id']}, '{g.user}', '{data['annotation']}', '{data['geometry']}')"""
			)
		if r.rowcount == 0:
			return "Problem inserting new label", STATUS_INTERNAL_ERROR

		label_id = cur.execute(f"SELECT last_insert_rowid() FROM Labels").fetchone()
		conn.commit()

		return json.dumps({'label_id': label_id}), STATUS_OK


def contains_sensitive():
	"""
	Check whether a particular image contains sensitive information. 
	"""




def get_db():
	"""Opens a new database connection if there is none yet for the
	current application context.
	"""
	db_path = str(Path(__file__).absolute().parent.joinpath('image_db', 'test_db.sqlite'))
	if not hasattr(g, 'conn'):
		g.conn = sqlite3.connect(db_path)
		g.cur = g.conn.cursor()
	return g.cur, g.conn


@app.teardown_appcontext
def cleanup(error):
	"""Closes the database again at the end of the request."""
	if hasattr(g, 'conn'):
		g.conn.close()
	g.pop('conn', None)
	g.pop('user', None)		



@auth.verify_password
def verify_password(username, password):
	# don't allow anonymous users
	if username is '':
		return False

	# get pwd hash from db
	cur, conn = get_db()
	result = cur.execute(f"SELECT pwd_hash FROM Users WHERE username='{username}'").fetchone()
	if result is None:
		return False
	pwd_hash = result[0]

	# validate it against hash
	if check_password_hash(pwd_hash, password):
		g.user = username
		return True
	return False


if __name__ == '__main__':
	app.run(debug=True)
