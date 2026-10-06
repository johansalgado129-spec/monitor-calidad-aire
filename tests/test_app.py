import os
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.app import app
from backend.src import history
from backend.src.openaq_client import OpenAQClient


class TestApplication(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = patch.object(history, 'HISTORY_PATH', Path(self.tmp.name) / 'history.csv')
        self.path.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.path.stop()
        self.tmp.cleanup()

    def test_public_files_and_private_files(self):
        for route in ['/', '/script.js', '/config.js', '/styles.css', '/salud']:
            self.assertEqual(self.client.get(route).status_code, 200)
        for route in ['/.env', '/backend/app.py', '/data/historial_calidad_aire.csv']:
            self.assertEqual(self.client.get(route).status_code, 404)

    def test_city_history_and_csv(self):
        location = {'name': 'Estacion de prueba', 'locality': 'Bogota',
                    'sensors': [{'id': 1, 'parameter': {'name': 'pm25', 'units': 'µg/m³'}}]}
        rows = [{'value': 9, 'parameter': {'units': 'µg/m³'},
                 'period': {'datetimeTo': {'utc': f'2026-10-05T{hour:02}:00:00Z'}}}
                for hour in range(24)]
        with patch.dict(os.environ, {'OPENAQ_API_KEY': 'test-only-not-a-real-key'}), \
             patch.object(OpenAQClient, 'find_locations_by_city', return_value=[location]), \
             patch.object(OpenAQClient, 'get_sensor_hours', return_value=rows):
            response = self.client.get('/api/ciudad/Bogota')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['aqi'], 50)
        self.assertIsNone(response.json()['mediciones']['no2_1h_ppb'])
        self.assertEqual(len(self.client.get('/api/historial').json()['historial']), 1)
        csv = self.client.get('/api/historial.csv')
        self.assertIn('attachment;', csv.headers['content-disposition'])
        self.assertIn('Bogota', csv.content.decode('utf-8-sig'))

    def test_concurrent_history(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda i: history.save_record({'ciudad': str(i), 'aqi': i}), range(50)))
        self.assertEqual(len(history.read_history()), 50)
        self.assertEqual(len({r['ciudad'] for r in history.read_history()}), 50)

    def test_missing_key(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(self.client.get('/salud').json()['openaq_configurada'])
            self.assertEqual(self.client.get('/api/ciudad/Bogota').status_code, 500)

    def test_empty_csv_schema(self):
        response = self.client.get('/api/historial.csv')
        self.assertEqual(response.content.decode('utf-8-sig').strip(), ','.join(history.FIELDS))
