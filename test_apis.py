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

class TestApis(TestCase):
	def setUp(self):
		print('running set up')
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

	def test_get_image_nonexistant(self):
		invalid_image_id = 9999999
		r = self.get_request(f'image/{invalid_image_id}')
		self.assertEqual(r.status_code, 500)


class TestDeleteImage(TestApis):
	def test_invalid_auth(self):
		r = self.delete_request('image/1', pwd='invalidpwd')
		self.assertEqual(r.status_code, 401)

	def test_delete_image_2(self):
		r = self.delete_request('image/2')
		self.assertEqual(r.status_code, 200)

		r = self.get_request('image/2')
		self.assertEqual(r.status_code, 500)

	def test_delete_nonexistant(self):
		invalid_image_id = 9999999
		r = self.delete_request(f'image/{invalid_image_id}')
		self.assertEqual(r.status_code, 500)


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
			'annotation': 'Tumor', 
			'first_name': 'Jimi', 
			'last_name': 'Hendrix', 
			'image_id': 1, 
			'geometry': 'Top left'})
		
	def test_get_label_2(self):
		r = self.get_request('label/2')
		self.assertEqual(r.status_code, 200)
		self.assertDictEqual(json.loads(r.content), 
			{'annotation': 'Cyst',
			'first_name': 'Jimi',
			'geometry': 'Middle',
			'image_id': 3,
			'image_path': 'posture_image.jpeg',
			'label_id': 2,
			'last_name': 'Hendrix'})

	def test_get_label_nonexistant(self):
		invalid_label_id = 9999999
		r = self.get_request(f'label/{invalid_label_id}')
		self.assertEqual(r.status_code, 500)

class TestDeleteLabel(TestApis):
	def test_invalid_auth(self):
		r = self.delete_request('label/1', pwd='invalidpwd')
		self.assertEqual(r.status_code, 401)

	def test_delete_label_2(self):
		r = self.delete_request('label/2')
		self.assertEqual(r.status_code, 200)

		r = self.get_request('label/2')
		self.assertEqual(r.status_code, 500)

	def test_delete_nonexistant(self):
		invalid_label_id = 9999999
		r = self.delete_request(f'label/{invalid_label_id}')
		self.assertEqual(r.status_code, 500)

# class TestCreateLabel(TestApis):
# 	def test_invalid_auth(self):
# 		r = self.post_request('label', data={'annotation': 'cancer', 'geometry': 'right'}, pwd='invalidpwd')
# 		self.assertEqual(r.status_code, 401)

# 	def test_create_label(self):
# 		r = self.post_request('label', data={'annotation': 'cancer', 'geometry': 'right'}, pwd='invalidpwd')
# 		self.assertEqual(r.status_code, 401)
