import os
import datetime
import json
from unittest import TestCase

from pathlib import Path
import pytest
import requests
from requests.auth import HTTPBasicAuth
import shutil
import sqlite3

from image_db.create_db import create_db
from app import get_db, STATUS_OK, STATUS_BAD_REQUEST, STATUS_NOT_FOUND, STATUS_INTERNAL_ERROR

from identify_pii import _check_words_suspect, _extract_words

STATUS_UNAUTHORISED = 401


class TestApis(TestCase):
    def setUp(self):
        db_path = Path(__file__).absolute().parent.joinpath('image_db', 'test_db.sqlite')
        create_db(db_path)

    def get_request(self, url, usr='rock_god_9000', pwd='voodoochild'):
        return requests.get(f"http://localhost:5000/{url}", auth=HTTPBasicAuth('rock_god_9000', pwd))

    def delete_request(self, url, usr='rock_god_9000', pwd='voodoochild'):
        return requests.delete(f"http://localhost:5000/{url}", auth=HTTPBasicAuth('rock_god_9000', pwd))

    def post_request(self, url, data, usr='rock_god_9000', pwd='voodoochild'):
        return requests.post(f"http://localhost:5000/{url}", data=data, auth=HTTPBasicAuth('rock_god_9000', pwd))

    def put_request(self, url, data, usr='rock_god_9000', pwd='voodoochild'):
        return requests.put(f"http://localhost:5000/{url}", data=data, auth=HTTPBasicAuth('rock_god_9000', pwd))


class TestGetImage(TestApis):
    def test_invalid_auth(self):
        r = self.get_request('image/1', pwd='invalidpwd')
        self.assertEqual(r.status_code, STATUS_UNAUTHORISED)

    def test_get_image_1(self):
        r = self.get_request('image/1')
        self.assertEqual(r.status_code, STATUS_OK)
        self.assertEqual(json.loads(r.content), {'image_id': 1, 'image_path': 'brain_jeff.jpeg', 'contains_pii': 0})
        
    def test_get_image_2(self):
        r = self.get_request('image/2')
        self.assertEqual(r.status_code, STATUS_OK)
        self.assertEqual(json.loads(r.content), {'image_id': 2, 'image_path': 'jemmas_ribs.jpeg', 'contains_pii': 0})

    def test_get_deleted(self):
        r = self.get_request('image/7')
        self.assertEqual(r.status_code, STATUS_NOT_FOUND)

    def test_get_image_nonexistant(self):
        invalid_image_id = 9999999
        r = self.get_request(f'image/{invalid_image_id}')
        self.assertEqual(r.status_code, STATUS_NOT_FOUND)


class TestDeleteImage(TestApis):
    def test_invalid_auth(self):
        r = self.delete_request('image/1', pwd='invalidpwd')
        self.assertEqual(r.status_code, STATUS_UNAUTHORISED)

    def test_delete_image_2(self):
        r = self.delete_request('image/2')
        self.assertEqual(r.status_code, STATUS_OK)

        r = self.get_request('image/2')
        self.assertEqual(r.status_code, STATUS_NOT_FOUND)

    def test_delete_nonexistant(self):
        invalid_image_id = 9999999
        r = self.delete_request(f'image/{invalid_image_id}')
        self.assertEqual(r.status_code, STATUS_NOT_FOUND)


class TestCreateImage(TestApis):
    def test_invalid_auth(self):
        r = self.post_request('image', data={'image_path': 'new_image.jpeg'}, pwd='invalidpwd')
        self.assertEqual(r.status_code, STATUS_UNAUTHORISED)

    def test_create_image(self):
        # duplicate an existing image
        image_dir = Path(__file__).absolute().parent.joinpath('static', 'images')
        original_image_path = image_dir.joinpath('brain_jeff.jpeg')
        new_image_path = image_dir.joinpath('new_brain_jeff.jpeg')
        if not os.path.exists(new_image_path):
            shutil.copyfile(original_image_path, new_image_path)

        # call API to insert into db
        r = self.post_request('image', data={'image_path': 'new_brain_jeff.jpeg'})
        self.assertEqual(r.status_code, STATUS_OK)
        image_id = int(json.loads(r.content)['image_id'])

        r = self.get_request(f'image/{image_id}')
        self.assertEqual(r.status_code, STATUS_OK)

        # remove the dupicate image
        os.remove(new_image_path)

    def test_create_image_nonexistant(self):
        r = self.post_request('image', data={'image_path': 'this_doesnt_exist.jpeg'})
        self.assertEqual(r.status_code, STATUS_BAD_REQUEST)


class TestGetLabel(TestApis):
    def test_invalid_auth(self):
        r = self.get_request('label/1', pwd='invalidpwd')
        self.assertEqual(r.status_code, STATUS_UNAUTHORISED)

    def test_get_label_1(self):
        r = self.get_request('label/1')
        self.assertEqual(r.status_code, STATUS_OK)
        self.assertDictEqual(json.loads(r.content), 
            {'label_id': 1, 
            'image_path': 'brain_jeff.jpeg',
            'username': 'rock_god_9000', 
            'class_id': 1, 
            'first_name': 'Jimi', 
            'last_name': 'Hendrix', 
            'image_id': 1, 
            # multipolygon is the WKT string for describing a set of polygons. These are the end points.
            'geometry': 'MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 45 20, 30 5, 10 10, 10 30, 20 35), (30 20, 20 25, 20 15, 30 20)))'})
        
    def test_get_label_2(self):
        r = self.get_request('label/2')
        self.assertEqual(r.status_code, STATUS_OK)
        self.assertDictEqual(json.loads(r.content), 
            {'class_id': 2,
            'first_name': 'Jimi',
            # multipolygon is the WKT string for describing a set of polygons. These are the end points.
            'geometry': 'MULTIPOLYGON (((10 10, 20 25, 15 30, 10 10)))',
            'image_id': 3,
            'image_path': 'posture_image.jpeg',
            'label_id': 2,
            'last_name': 'Hendrix',
            'username': 'rock_god_9000'})

    def test_get_label_nonexistant(self):
        invalid_label_id = 9999999
        r = self.get_request(f'label/{invalid_label_id}')
        self.assertEqual(r.status_code, STATUS_NOT_FOUND)

class TestDeleteLabel(TestApis):
    def test_invalid_auth(self):
        r = self.delete_request('label/1', pwd='invalidpwd')
        self.assertEqual(r.status_code, STATUS_UNAUTHORISED)

    def test_delete_label_2(self):
        r = self.delete_request('label/2')
        self.assertEqual(r.status_code, STATUS_OK)

        r = self.get_request('label/2')
        self.assertEqual(r.status_code, STATUS_NOT_FOUND)

    def test_delete_nonexistant(self):
        invalid_label_id = 9999999
        r = self.delete_request(f'label/{invalid_label_id}')
        self.assertEqual(r.status_code, STATUS_NOT_FOUND)

class TestCreateLabel(TestApis):
    def test_invalid_auth(self):
        r = self.post_request('label', 
            data={'image_id': 2, 'class_id': 1, 'geometry': 'MULTIPOLYGON (((10 10, 20 25, 15 30, 10 10)))'}, 
            pwd='invalidpwd')
        self.assertEqual(r.status_code, STATUS_UNAUTHORISED)

    def test_create_label(self):
        r = self.post_request('label', 
            data={'image_id': 2, 'class_id': 1, 'geometry': 'MULTIPOLYGON (((10 10, 20 25, 15 30, 10 10)))'})
        self.assertEqual(r.status_code, STATUS_OK)
        label_id = int(json.loads(r.content)['label_id'])

        r = self.get_request(f'label/{label_id}')
        self.assertEqual(r.status_code, STATUS_OK)

class TestUpdateLabel(TestApis):
    def test_invalid_auth(self):
        r = self.put_request('label/1', data={'class_id': 2}, pwd='invalidpwd')
        self.assertEqual(r.status_code, STATUS_UNAUTHORISED)

    def test_update_classid(self):
        r = self.put_request('label/1', data={'class_id': 2})
        self.assertEqual(r.status_code, STATUS_OK)

        r = self.get_request(f'label/1')
        self.assertEqual(r.status_code, STATUS_OK)
        self.assertDictEqual(json.loads(r.content), 
            {'label_id': 1, 
            'image_path': 'brain_jeff.jpeg', 
            'class_id': 2, 
            'first_name': 'Jimi', 
            'last_name': 'Hendrix', 
            'username': 'rock_god_9000',
            'image_id': 1, 
            'geometry': 'MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 45 20, 30 5, 10 10, 10 30, 20 35), (30 20, 20 25, 20 15, 30 20)))'})
        
    def test_update_geometry(self):
        r = self.put_request('label/1', data={'geometry': 'MULTIPOLYGON (((10 10, 20 25, 15 30, 10 10)))'})
        self.assertEqual(r.status_code, STATUS_OK)

        r = self.get_request(f'label/1')
        self.assertEqual(r.status_code, STATUS_OK)
        self.assertDictEqual(json.loads(r.content), 
            {'label_id': 1, 
            'image_path': 'brain_jeff.jpeg', 
            'class_id': 1, 
            'first_name': 'Jimi', 
            'last_name': 'Hendrix', 
            'username': 'rock_god_9000',
            'image_id': 1, 
            'geometry': 'MULTIPOLYGON (((10 10, 20 25, 15 30, 10 10)))'})
        
class TestLog(TestApis):
    def get_log(self):
        db_path = str(Path(__file__).absolute().parent.joinpath('image_db', 'test_db.sqlite'))
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        result = cur.execute(
            '''SELECT object, updated_by, method, image_id, label_id, modified_at FROM Logs
            ORDER BY modified_at desc
            LIMIT 1
            ''').fetchone()
        if result is None:
            return None

        obj, updated_by, method, image_id, label_id, modified_at = result
        return dict(obj=obj, updated_by=updated_by, method=method, image_id=image_id, label_id=label_id, modified_at=modified_at)


    def test_log_insert_image(self):
        # duplicate an existing image
        image_dir = Path(__file__).absolute().parent.joinpath('static', 'images')
        original_image_path = image_dir.joinpath('brain_jeff.jpeg')
        new_image_path = image_dir.joinpath('new_brain_jeff.jpeg')
        if not os.path.exists(new_image_path):
            shutil.copyfile(original_image_path, new_image_path)

        # call API to insert into db
        r = self.post_request('image', data={'image_path': 'new_brain_jeff.jpeg'})
        image_id = int(json.loads(r.content)['image_id'])

        # check that a log was made
        log = self.get_log()
        self.assertFalse(log is None)

        # check the time is very recent
        modified_at = datetime.datetime.strptime(log.pop('modified_at'), '%Y-%m-%d %H:%M:%S')
        self.assertTrue(abs(modified_at - datetime.datetime.now()) < datetime.timedelta(seconds=5))
        
        # check other properties
        self.assertEqual(log, {
            'obj': 'Image',
            'updated_by': 'rock_god_9000', 
            'method': 'INSERTION', 
            'image_id': image_id, 
            'label_id': None
            })

        # remove the dupicate image
        os.remove(new_image_path)

    def test_log_insert_label(self):
        r = self.post_request('label', data={'image_id': 2, 'class_id': 1, 'geometry': 'MULTIPOLYGON (((10 10, 20 25, 15 30, 10 10)))'})
        label_id = int(json.loads(r.content)['label_id'])

        # check that a log was made
        log = self.get_log()
        self.assertFalse(log is None)

        # check the time is very recent
        modified_at = datetime.datetime.strptime(log.pop('modified_at'), '%Y-%m-%d %H:%M:%S')
        self.assertTrue(abs(modified_at - datetime.datetime.now()) < datetime.timedelta(seconds=5))
        
        # check other properties
        self.assertEqual(log, {
            'obj': 'Label',
            'updated_by': 'rock_god_9000', 
            'method': 'INSERTION', 
            'image_id': None, 
            'label_id': label_id
            })


    def test_log_update_labels(self):
        r = self.put_request('label/1', data={'class_id': 2})

        # check that a log was made
        log = self.get_log()
        self.assertFalse(log is None)

        # check the time is very recent
        modified_at = datetime.datetime.strptime(log.pop('modified_at'), '%Y-%m-%d %H:%M:%S')
        self.assertTrue(abs(modified_at - datetime.datetime.now()) < datetime.timedelta(seconds=5))
        
        # check other properties
        self.assertEqual(log, {
            'obj': 'Label',
            'updated_by': 'rock_god_9000', 
            'method': 'UPDATE', 
            'image_id': None, 
            'label_id': 1
            })

    def test_log_delete_labels(self):
        r = self.delete_request('label/1')

        # check that a log was made
        log = self.get_log()
        self.assertFalse(log is None)

        # check the time is very recent
        modified_at = datetime.datetime.strptime(log.pop('modified_at'), '%Y-%m-%d %H:%M:%S')
        self.assertTrue(abs(modified_at - datetime.datetime.now()) < datetime.timedelta(seconds=5))
        
        # check other properties
        self.assertEqual(log, {
            'obj': 'Label',
            'updated_by': 'rock_god_9000', 
            'method': 'DELETE', 
            'image_id': None, 
            'label_id': 1
            })

    def test_log_delete_labels(self):
        r = self.delete_request('label/1')
        self.assertEqual(r.status_code, STATUS_OK)

        # check that a log was made
        log = self.get_log()
        self.assertFalse(log is None)

        # check the time is very recent
        modified_at = datetime.datetime.strptime(log.pop('modified_at'), '%Y-%m-%d %H:%M:%S')
        self.assertTrue(abs(modified_at - datetime.datetime.now()) < datetime.timedelta(seconds=5))
        
        # check other properties
        self.assertEqual(log, {
            'obj': 'Label',
            'updated_by': 'rock_god_9000', 
            'method': 'DELETE', 
            'image_id': None, 
            'label_id': 1
            })

    def test_log_delete_image(self):
        r = self.delete_request('image/1')
        self.assertEqual(r.status_code, STATUS_OK)

        # check that a log was made
        log = self.get_log()
        self.assertFalse(log is None)

        # check the time is very recent
        modified_at = datetime.datetime.strptime(log.pop('modified_at'), '%Y-%m-%d %H:%M:%S')
        self.assertTrue(abs(modified_at - datetime.datetime.now()) < datetime.timedelta(seconds=5))
        
        # check other properties
        self.assertEqual(log, {
            'obj': 'Image',
            'updated_by': 'rock_god_9000', 
            'method': 'DELETE', 
            'image_id': 1, 
            'label_id': None
            })

class TestCheckForPII(TestApis):
    def test_has_keyword(self):
        has_keyword = ['name', 'tumor', 'is', 'vas2348agnas123']
        self.assertTrue(_check_words_suspect(has_keyword))

    def test_not_sus(self):
        not_sus = ['tumor', 'cyst', 'doctor', 'hospital', 'asddf234asfk!asd']
        self.assertFalse(_check_words_suspect(not_sus))

    def test_empty(self):
        empty1 = None
        self.assertFalse(_check_words_suspect(empty1))
        
        empty2 = []
        self.assertFalse(_check_words_suspect(empty2))

    def test_has_name(self):
        has_name_1 = ['tumor', 'bad', 'john', 'smith', '22/7/1994']
        self.assertTrue(_check_words_suspect(has_name_1))

        has_name_2 = ['mary']
        self.assertTrue(_check_words_suspect(has_name_1))

class TestExtractWords(TestApis):
    def test_no_words(self):
        image_dir = Path(__file__).absolute().parent.joinpath('static', 'images', 'brain_jeff.jpeg')
        words = _extract_words(str(image_dir))
        self.assertEqual(len(words), 0)

    def test_has_words(self):
        image_dir = Path(__file__).absolute().parent.joinpath('static', 'images', 'ribs_contains_identity_1.jpeg')
        words = _extract_words(str(image_dir))
        self.assertTrue('john' in words)
