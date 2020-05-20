from unittest import TestCase
from image_db.create_db import create_db
import pytest
import requests
from requests.auth import HTTPBasicAuth
import os

class test_apis(TestCase):
	def setUp(self):
		create_db('test_db.sqlite')

	def test_get_image(self):
		r = requests.get('http://127.0.0.1:5000/', auth=HTTPBasicAuth('rock_god_9000', 'voodoochild'))
		self.assertEqual(r.status_code, 200)
		