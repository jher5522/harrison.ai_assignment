from flask import Flask, render_template, request, g
import sqlite3
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from pathlib import Path
import shapely.wkt
from identify_pii import check_for_pii


STATUS_OK = 200
STATUS_BAD_REQUEST = 400
STATUS_NOT_FOUND = 410
STATUS_INTERNAL_ERROR = 500


app = Flask(__name__)
auth = HTTPBasicAuth()



@app.route('/image/<int:image_id>', methods=["GET", "DELETE"])
@app.route('/image', methods=["POST"])
@auth.login_required
def image(image_id=None):
	cur, conn = get_db()
	
	if request.method == "GET":
		get_image_query = """SELECT image_id, image_path, contains_pii 
						FROM Images 
						WHERE image_id=:image_id
						AND NOT images.deleted"""
		row = cur.execute(get_image_query, {'image_id': image_id}).fetchone()
		
		# check that it found the requested image
		if row is None:
			return "Image not found", STATUS_NOT_FOUND

		# return the image data and success
		return json.dumps(dict(row)), STATUS_OK
	

	elif request.method ==  "DELETE":
		delete_image_query = """
			UPDATE Images 
			SET deleted=1 
			WHERE image_id=:image_id
			"""
		r = cur.execute(delete_image_query, {'image_id': image_id})
		
		# check that it deleted something
		if r.rowcount != 1:
			return "Nothing to delete", STATUS_NOT_FOUND
		
		# log the deletion
		log_success = add_log('Image', 'DELETE', image_id, None)
		conn.commit()
		return "deleted", STATUS_OK


	elif request.method == 'POST':
		# To insert a new image into the db, you should copy the image into the 'static/images' directory
		# and use this API to insert it into the db
		image_path = request.values.to_dict()['image_dir']

		# check its in static/images
		images_dir = Path(__file__).absolute().parent.joinpath('static', 'images')
		provided_path = Path(images_dir).joinpath(image_path)
		if not images_dir in provided_path.parents:
			return "Image should be in a direcotry within static/images", STATUS_BAD_REQUEST

		# check this file exists
		if not os.path.exists(provided_path.absolute()):
			return "Image does not exist at specified path", STATUS_BAD_REQUEST

		# check whether it contains pii
		contains_pii = check_for_pii(provided_path)

		# insert row
		rel_image_path = str(provided_path.relative_to(images_dir))
		insert_image_query = """
			INSERT INTO Images (image_path, deleted, contains_pii) 
			VALUES (':image_path', 0, :contains_pii)
			"""
		r = cur.execute(insert_image_query, {'image_path': rel_image_path, 'contains_pii': contains_pii})

		# check it worked
		if r.rowcount != 1:
			return "Problem inserting new image", STATUS_INTERNAL_ERROR
		image_id = cur.execute(f"SELECT last_insert_rowid() FROM Images").fetchone()[0]

		# log the update
		add_log('Image', 'INSERTION', int(image_id), None)
		conn.commit()
		return json.dumps({'image_id': image_id}), STATUS_OK


@app.route('/label/<int:label_id>', methods=['GET', 'DELETE', 'PUT'])
@app.route('/label', methods=["POST"])
@auth.login_required
def label(label_id=None):
	cur, conn = get_db()

	if request.method == "GET":
		get_label_query = """
			SELECT image_id, label_id, image_path, first_name, last_name, class_id, geometry
			FROM Labels 
			JOIN Images USING(image_id) 
			JOIN Users ON labels.labelled_by = users.username 
			WHERE label_id=:label_id
			AND not labels.deleted
			"""

		row = cur.execute(get_label_query, {'label_id': label_id}).fetchone()
		if row is None:
			return "Label not found", STATUS_NOT_FOUND

		return json.dumps(dict(row))


	elif request.method=='DELETE':
		delete_label_query = """
			UPDATE Labels 
			SET deleted=1 
			WHERE label_id=:label_id
			"""
		r = cur.execute(delete_label_query, {'label_id': label_id})

		# check something was deleted
		if r.rowcount != 1:
			return "Nothing to delete", STATUS_NOT_FOUND

		# log and return success
		add_log('Label', 'DELETE', None, int(label_id))
		conn.commit()
		return "Label deleted", STATUS_OK


	elif request.method=='POST':
		data = request.values.to_dict()

		# ensure geometry is wkt
		try:
			shapely.wkt.loads(data['geometry'])
		except shapely.errors.WKTReadingError:
			return "Geometry is not a valid wkt", STATUS_BAD_REQUEST

		# insert new label
		insert_label_query = """
			INSERT INTO Labels (image_id, labelled_by, class_id, geometry, deleted) 
			VALUES (:image_id, :usr, :class_id, :geom, 0)
			"""
		query_data = {
			'image_id': int(data['image_id']), 
			'usr': g.user,
			'class_id': int(data['class_id']),
			'geom': data['geometry']
			}
		r = cur.execute(insert_label_query, query_data)
		
		# ensure something was inserted
		if r.rowcount != 1:
			return "Problem inserting new label", STATUS_INTERNAL_ERROR
		label_id = cur.execute(f"SELECT last_insert_rowid() FROM Labels").fetchone()[0]
		
		# log and return success
		add_log('Label', 'INSERTION', None, int(label_id))
		conn.commit()
		return json.dumps({'label_id': label_id}), STATUS_OK

	elif request.method=='PUT':
		data = request.values.to_dict()

		# change class_id and/or geometry if its specified
		update_label_query = f"""
			UPDATE Labels
			SET 
			{'class_id=:class_id' if 'class_id' in data.keys() else ''}
			{'geometry=:geometry' if 'geometry' in data.keys() else ''}
			WHERE label_id=:label_id
			"""
		r = cur.execute(update_label_query, {'label_id': label_id, **data})
		
		# ensure something was updated
		if r.rowcount != 1:
			return "Nothing to update", STATUS_NOT_FOUND

		# log and return success
		add_log('Label', 'UPDATE', None, int(label_id))
		conn.commit()
		return "Label updated", STATUS_OK


def add_log(obj, method, image_id, label_id):
	cur, conn = get_db()

	insert_log_query = """
		INSERT INTO Logs (object, updated_by, method, image_id, label_id, modified_at) 
		VALUES (:obj, :usr, :method, :im_id, :lab_id, datetime('now', 'localtime'))
		"""
	log_data = {
		'obj': obj,
		'usr': g.user, 
		'method': method, 
		'im_id': image_id, 
		'lab_id': label_id
		}
	r = cur.execute(insert_log_query, log_data)
	
	# ensure it logged properly. Otherwise raise error, will which return 500
	if r.rowcount != 1:
		raise ValueError('Logging was unsucessful')


def get_db():
	db_path = str(Path(__file__).absolute().parent.joinpath('image_db', 'test_db.sqlite'))
	if not hasattr(g, 'conn'):
		# only open new connection if it doesn't already exist. Otherwise return existing
		g.conn = sqlite3.connect(db_path)
		g.conn.row_factory = sqlite3.Row
		g.cur = g.conn.cursor()
	return g.cur, g.conn


@app.teardown_appcontext
def cleanup(error):
	# close db connection and clear g variables
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
