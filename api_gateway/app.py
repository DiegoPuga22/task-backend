import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
import time
import logging
import os
from functools import wraps
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
CORS(app)

# Ruta absoluta a la carpeta raíz del proyecto (un nivel arriba)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Carpeta de logs en la raíz del proyecto
log_dir = os.path.join(root_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)

# Configuración del logger con rotación de archivos
log_file = os.path.join(log_dir, 'api_gateway.log')
handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def log_middleware(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        usuario = request.headers.get('X-User', 'anonymous')
        servicio_api = request.path
        metodo_http = request.method
        ip_origen = request.remote_addr

        result = f(*args, **kwargs)

        if isinstance(result, tuple):
            _, status_code = result
        else:
            status_code = getattr(result, 'status_code', 200)

        response_time = time.time() - start_time

        logger.info(
            f'User: {usuario}, IP: {ip_origen}, Method: {metodo_http}, '
            f'Service: {servicio_api}, Status: {status_code}, Response Time: {response_time:.2f}s'
        )

        return result
    return wrapper

# URLs de microservicios
AUTH_SERVICE_URL = 'http://localhost:5001'
USER_SERVICE_URL = 'http://localhost:5002'
TASK_SERVICE_URL = 'http://localhost:5003'

@app.route('/auth/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@log_middleware
def proxy_auth(path):
    method = request.method
    url = f'{AUTH_SERVICE_URL}/{path}'
    resp = requests.request(
        method=method,
        url=url,
        json=request.get_json(silent=True),
        headers={key: value for key, value in request.headers if key.lower() != 'host'}
    )
    return jsonify(resp.json()), resp.status_code

@app.route('/user/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@log_middleware
def proxy_user(path):
    method = request.method
    url = f'{USER_SERVICE_URL}/{path}'
    resp = requests.request(
        method=method,
        url=url,
        json=request.get_json(silent=True),
        headers={key: value for key, value in request.headers if key.lower() != 'host'}
    )
    return jsonify(resp.json()), resp.status_code

@app.route('/task/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@log_middleware
def proxy_task(path):
    method = request.method
    url = f'{TASK_SERVICE_URL}/{path}'
    resp = requests.request(
        method=method,
        url=url,
        json=request.get_json(silent=True),
        headers={key: value for key, value in request.headers if key.lower() != 'host'}
    )
    return jsonify(resp.json()), resp.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
