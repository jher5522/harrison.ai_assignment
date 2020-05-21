from unittest import TestCase
from image_db.create_db import create_db
import pytest
import requests
from requests.auth import HTTPBasicAuth
import os
import json
from pathlib import Path
from app import get_db
import sqlite3
import shutil

class TestApis(TestCase):
	def setUp(self):
		db_path = Path(__file__).absolute().parent.joinpath('image_db', 'test_db.sqlite')
		create_db(db_path)

	def get_request(self, url, usr='rock_god_9000', pwd='voodoochild'):
		return requests.get(f"http://127.0.0.1:5000/{url}", auth=HTTPBasicAuth('rock_god_9000', pwd))

	def delete_request(self, url, usr='rock_god_9000', pwd='voodoochild'):
		return requests.delete(f"http://127.0.0.1:5000/{url}", auth=HTTPBasicAuth('rock_god_9000', pwd))

	def post_request(self, url, data, usr='rock_god_9000', pwd='voodoochild'):
		return requests.post(f"http://127.0.0.1:5000/{url}", data=data, auth=HTTPBasicAuth('rock_god_9000', pwd))


class TestGetImage(TestApis):
	def test_invalid_auth(self):
		r = self.get_request('image/1', pwd='invalidpwd')
		self.assertEqual(r.status_code, 401)

	def test_get_image_1(self):
		r = self.get_request('image/1')
		self.assertEqual(r.status_code, 200)
		self.assertEqual(json.loads(r.content), {'image_id': 1, 'image_path': 'brain_jeff.jpeg'})
		
	def test_get_image_2(self):
		r = self.get_request('image/2')
		self.assertEqual(r.status_code, 200)
		self.assertEqual(json.loads(r.content), {'image_id': 2, 'image_path': 'jemmas_ribs.jpeg'})

	def test_get_deleted(self):
		r = self.get_request('image/6')
		self.assertEqual(r.status_code, 410)

	def test_get_image_nonexistant(self):
		invalid_image_id = 9999999
		r = self.get_request(f'image/{invalid_image_id}')
		self.assertEqual(r.status_code, 410)


class TestDeleteImage(TestApis):
	def test_invalid_auth(self):
		r = self.delete_request('image/1', pwd='invalidpwd')
		self.assertEqual(r.status_code, 401)

	def test_delete_image_2(self):
		r = self.delete_request('image/2')
		self.assertEqual(r.status_code, 200)

		r = self.get_request('image/2')
		self.assertEqual(r.status_code, 410)

	def test_delete_nonexistant(self):
		invalid_image_id = 9999999
		r = self.delete_request(f'image/{invalid_image_id}')
		self.assertEqual(r.status_code, 410)


class TestCreateImage(TestApis):
	def test_invalid_auth(self):
		r = self.post_request('image', data={'image_path': 'new_image.jpeg'}, pwd='invalidpwd')
		self.assertEqual(r.status_code, 401)

	def test_create_image(self):
		# duplicate an existing image
		image_dir = Path(__file__).absolute().parent.joinpath('static', 'images')
		original_image_path = image_dir.joinpath('brain_jeff.jpeg')
		new_image_path = image_dir.joinpath('new_brain_jeff.jpeg')
		if not os.path.exists(new_image_path):
			shutil.copyfile(original_image_path, new_image_path)

		# call API to insert into db
		r = self.post_request('image', data={'image_dir': 'new_brain_jeff.jpeg'})
		image_id = int(json.loads(r.content)['image_id'][0])

		r = self.get_request(f'image/{image_id}')
		self.assertEqual(r.status_code, 200)

		# remove the dupicate image
		os.remove(new_image_path)

	def test_create_image_nonexistant(self):
		r = self.post_request('image', data={'image_dir': 'new_brain_jeff.jpeg'})
		self.assertEqual(r.status_code, 400)


class TestGetLabel(TestApis):
	def test_invalid_auth(self):
		r = self.get_request('label/1', pwd='invalidpwd')
		self.assertEqual(r.status_code, 401)

	def test_get_label_1(self):
		r = self.get_request('label/1')
		self.assertEqual(r.status_code, 200)
		self.assertDictEqual(json.loads(r.content), 
			{'label_id': 1, 
			'image_path': 'brain_jeff.jpeg', 
			'class_id': 1, 
			'first_name': 'Jimi', 
			'last_name': 'Hendrix', 
			'image_id': 1, 
			'geometry': 'MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 45 20, 30 5, 10 10, 10 30, 20 35), (30 20, 20 25, 20 15, 30 20)))'})
		
	def test_get_label_2(self):
		r = self.get_request('label/2')
		self.assertEqual(r.status_code, 200)
		self.assertDictEqual(json.loads(r.content), 
			{'class_id': 2,
			'first_name': 'Jimi',
			'geometry': 'MULTIPOLYGON (((10 10, 20 25, 15 30, 10 10)))',
			'image_id': 3,
			'image_path': 'posture_image.jpeg',
			'label_id': 2,
			'last_name': 'Hendrix'})

	def test_get_label_nonexistant(self):
		invalid_label_id = 9999999
		r = self.get_request(f'label/{invalid_label_id}')
		self.assertEqual(r.status_code, 410)

class TestDeleteLabel(TestApis):
	def test_invalid_auth(self):
		r = self.delete_request('label/1', pwd='invalidpwd')
		self.assertEqual(r.status_code, 401)

	def test_delete_label_2(self):
		r = self.delete_request('label/2')
		self.assertEqual(r.status_code, 200)

		r = self.get_request('label/2')
		self.assertEqual(r.status_code, 410)

	def test_delete_nonexistant(self):
		invalid_label_id = 9999999
		r = self.delete_request(f'label/{invalid_label_id}')
		self.assertEqual(r.status_code, 410)

class TestCreateLabel(TestApis):
	def test_invalid_auth(self):
		r = self.post_request('label', data={'image_id': 2, 'label_id': 1, 'class_id': 1, 'geometry': 'MULTIPOLYGON (((10 10, 20 25, 15 30, 10 10)))'}, pwd='invalidpwd')
		self.assertEqual(r.status_code, 401)

	def test_create_label(self):
		r = self.post_request('label', data={'image_id': 2, 'label_id': 1, 'class_id': 1, 'geometry': 'MULTIPOLYGON (((10 10, 20 25, 15 30, 10 10)))'})
		self.assertEqual(r.status_code, 200)
		label_id = int(json.loads(r.content)['label_id'][0])

		r = self.get_request(f'label/{label_id}')
		self.assertEqual(r.status_code, 200)

