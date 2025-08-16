from flask import Flask, jsonify, request
import os
from werkzeug.security import generate_password_hash
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://task-frontend-beta-five.vercel.app"], "allow_headers": ["Content-Type", "Authorization"], "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})

# Configuración de MongoDB
client = MongoClient(os.environ.get('MONGO_URI', 'mongodb+srv://2023171060:85df2Bs9aVBi6VpH@cluster0.qyf53xx.mongodb.net/users_db?retryWrites=true&w=majority&appName=Cluster0'))
db = client['users_db']
users_collection = db['users']

limiter = Limiter(get_remote_address, default_limits=["100 per minute"])

# Manejador global de errores
@app.errorhandler(Exception)
def handle_error(error):
    return jsonify({"error": "Error interno del servidor", "details": str(error)}), 500

# Ruta raíz para evitar errores 404
@app.route('/', methods=['GET', 'HEAD'])
@limiter.limit("100 per minute")
def home():
    return jsonify({"message": "Bienvenido a la API de Servicio de Usuarios"}), 200

@app.route('/users', methods=['GET'])
@limiter.limit("100 per minute")
def get_users():
    users = list(users_collection.find({}, {"_id": 1, "username": 1}))
    # Convertir ObjectId a string para JSON
    for user in users:
        user['id'] = str(user['_id'])
        del user['_id']
    return jsonify({"users": users}), 200

@app.route('/users_id/<user_id>', methods=['GET'])
@limiter.limit("100 per minute")
def get_user(user_id):
    try:
        user = users_collection.find_one({"_id": ObjectId(user_id)}, {"_id": 1, "username": 1})
        if not user:
            return jsonify({"error": "Usuario con ID no encontrado"}), 404
        user['id'] = str(user['_id'])
        del user['_id']
        return jsonify({"user": user}), 200
    except ValueError:
        return jsonify({"error": "ID de usuario inválido"}), 400

@app.route('/create_user', methods=['POST'])
@limiter.limit("100 per minute")
def create_user():
    if not request.json or 'username' not in request.json or 'password' not in request.json:
        return jsonify({"error": "Username y password son requeridos"}), 400
    username = request.json['username']
    password = request.json['password']
    
    # Validaciones de entrada
    if len(username) < 3:
        return jsonify({"error": "El nombre de usuario debe tener al menos 3 caracteres"}), 400
    if len(password) < 8:
        return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400
    
    hashed_password = generate_password_hash(password)
    if users_collection.find_one({"username": username}):
        return jsonify({"error": "Username ya existe"}), 400
    
    user = {"username": username, "password": hashed_password}
    result = users_collection.insert_one(user)
    return jsonify({"user": {"id": str(result.inserted_id), "username": username}}), 201

@app.route('/update_user/<user_id>', methods=['PUT'])
@limiter.limit("100 per minute")
def update_user(user_id):
    try:
        if not request.json or ('username' not in request.json and 'password' not in request.json):
            return jsonify({"error": "Username o password requeridos para actualizar"}), 400
        if not users_collection.find_one({"_id": ObjectId(user_id)}):
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        update_data = {}
        if 'username' in request.json:
            username = request.json['username']
            if len(username) < 3:
                return jsonify({"error": "El nombre de usuario debe tener al menos 3 caracteres"}), 400
            if users_collection.find_one({"username": username, "_id": {"$ne": ObjectId(user_id)}}):
                return jsonify({"error": "El nombre de usuario ya existe"}), 400
            update_data['username'] = username
        if 'password' in request.json:
            password = request.json['password']
            if len(password) < 8:
                return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400
            update_data['password'] = generate_password_hash(password)
        
        if update_data:
            users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
        return jsonify({"message": "Usuario actualizado exitosamente"}), 200
    except ValueError:
        return jsonify({"error": "ID de usuario inválido"}), 400

@app.route('/delete_user/<user_id>', methods=['DELETE'])
@limiter.limit("100 per minute")
def delete_user(user_id):
    try:
        if not users_collection.find_one({"_id": ObjectId(user_id)}):
            return jsonify({"error": "Usuario no encontrado"}), 404
        users_collection.delete_one({"_id": ObjectId(user_id)})
        return jsonify({"message": "Usuario eliminado exitosamente"}), 200
    except ValueError:
        return jsonify({"error": "ID de usuario inválido"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)