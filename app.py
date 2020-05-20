from flask import Flask, render_template, request, g
import sqlite3
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from pathlib import Path



app = Flask(__name__)
auth = HTTPBasicAuth()


@app.route('/')
@auth.login_required
def search_bar():
	cur, conn = get_db()
	all_images = cur.execute(f"SELECT image_id, image_path FROM Images").fetchall()
	return render_template("home.html", images=all_images) 



@app.route('/image', methods=["POST"])
@auth.login_required
def image_create():
	pass

@app.route('/image/<int:image_id>', methods=["GET", "DELETE"])
@auth.login_required
def image(image_id):
	cur, conn = get_db()
	
	if request.method == "GET":
		result = cur.execute(f"SELECT image_id, image_path FROM Images WHERE image_id={image_id}").fetchone()
		if result is None:
			return "Image not found", 500

		image_id, image_path = result
		return json.dumps({'image_id': image_id, 'image_path': image_path})
	
	elif request.method ==  "DELETE":
		r = cur.execute(f"DELETE FROM Images WHERE image_id={image_id}")
		if r.rowcount ==0:
			return "Nothing to delete", 500
		conn.commit()
		return "deleted"


@app.route('/label/<int:label_id>', methods=['GET', 'DELETE', 'POST'])
@auth.login_required
def label_get(label_id):
	cur, conn = get_db()

	if request.method == "GET":
		result = cur.execute(f"""
			SELECT image_id, image_path, first_name, last_name, annotation, geometry
			FROM Labels 
			JOIN Images USING(image_id) 
			JOIN Users ON labels.labelled_by = users.username 
			WHERE label_id={label_id}""").fetchone()
		if result is None:
			return "Label not found", 500

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
			return "Nothing to delete", 500
		conn.commit()
		return "Label deleted"

	elif request.method=='POST':
		data = request.form.to_dict()

		cur.execute(
			f"""INSERT INTO Labels (image_id, labelled_by, annotation, geometry) 
				VALUES ({image_id}, '{g.user}', '{data['annotation']}', '{data['geometry']}')"""
			)
		label_id = cur.execute(f"SELECT last_insert_rowid() FROM Labels").fetchone()
		conn.commit()

		return f"Label {label_id} created"





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
	print(f"logging in {username}, {password}")

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
