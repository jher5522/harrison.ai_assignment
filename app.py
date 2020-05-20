from flask import Flask, render_template, request, g
import sqlite3
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash



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

@app.route('/image/<int:image_id>', methods=["GET"])
@auth.login_required
def image_get(image_id):
	cur, conn = get_db()
	all_images = cur.execute(f"SELECT image_id, image_path FROM Images WHERE image_id={image_id}").fetchall()
	return render_template("image.html", image=all_images[0]) 

@app.route('/image_delete/<int:image_id>', methods=["GET"])
@auth.login_required
def image_delete(image_id):
	cur, conn = get_db()
	cur.execute(f"DELETE FROM Images WHERE image_id={image_id}")
	conn.commit()
	return "Image deleted"



@app.route('/label/<int:label_id>', methods=['GET'])
@auth.login_required
def label_get(label_id):
	cur, conn = get_db()
	result = cur.execute(f"""
		SELECT image_id, image_path, first_name, last_name, annotation, geometry
		FROM Labels 
		JOIN Images USING(image_id) 
		JOIN Users ON labels.labelled_by = users.username 
		WHERE label_id={label_id}""").fetchone()
	if result is None:
		return f"No data for label_id {label_id}"

	image_id, image_path, first_name, last_name, annotation, geometry = result
	return render_template("label.html", 
		label_id=label_id,
		image_id=image_id, 
		image_path=image_path, 
		first_name=first_name, 
		last_name=last_name, 
		annotation=annotation, 
		geometry=geometry)


@app.route('/label_delete/<int:label_id>', methods=["GET"])
@auth.login_required
def label_delete(label_id):
	cur, conn = get_db()
	cur.execute(f"DELETE FROM Labels WHERE label_id={label_id}")
	conn.commit()
	return "Label deleted"


@app.route('/label_create/<int:image_id>', methods=['POST'])
@auth.login_required
def label_create(image_id):
	data = request.form.to_dict()

	cur, conn = get_db()
	cur.execute(f"""
		INSERT INTO Labels (image_id, labelled_by, annotation, geometry) 
			VALUES ({image_id}, '{g.user}', '{data['annotation']}', '{data['geometry']}')
		""")
	label_id = cur.execute(f"SELECT last_insert_rowid() FROM Labels").fetchone()
	conn.commit()

	return f"Label {label_id} created"





def get_db():
	"""Opens a new database connection if there is none yet for the
	current application context.
	"""
	if not hasattr(g, 'conn'):
		g.conn = sqlite3.connect('image_db/image_db.sqlite')
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
