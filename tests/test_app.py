import pytest
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestAppRoutes:
    def test_index(self, client):
        response = client.get('/')
        assert response.status_code == 200

    def test_health_endpoint(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert 'components' in data

    def test_block_ip_invalid_json(self, client):
        response = client.post('/api/block', data='invalid')
        assert response.status_code in [400, 415]

    def test_block_ip_missing_ip(self, client):
        response = client.post('/api/block', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_block_ip_invalid_ip_format(self, client):
        response = client.post('/api/block', json={'ip': 'not-an-ip'})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_unblock_ip_invalid_json(self, client):
        response = client.post('/api/unblock', data='invalid')
        assert response.status_code in [400, 415]

    def test_unblock_ip_missing_ip(self, client):
        response = client.post('/api/unblock', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_unblock_ip_invalid_ip_format(self, client):
        response = client.post('/api/unblock', json={'ip': 'invalid-ip'})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_404_endpoint(self, client):
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_alerts_rate_limit(self, client):
        for _ in range(35):
            response = client.get('/api/alerts')
            if response.status_code == 429:
                break
        assert response.status_code == 429

    def test_stats_endpoint(self, client):
        response = client.get('/api/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_alerts' in data
        assert 'blocked_ips' in data
        assert 'suricata_status' in data
