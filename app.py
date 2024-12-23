from flask import Flask, render_template, request, jsonify
import base64
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
API_URL = 'https://api.fashn.ai/v1/run'
API_KEY = os.getenv('API_KEY')

VALID_CATEGORIES = ['tops', 'bottoms', 'one-pieces']

if not API_KEY:
    raise ValueError("API_KEY bulunamadı! .env dosyasını kontrol edin.")
else:
    print(f"API Key yüklendi: {API_KEY[:20]}...")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        model_image = request.files.get('model_image')
        if not model_image:
            return jsonify({'error': 'Model fotoğrafı gerekli'}), 400
        
        garment_image = request.files.get('garment_image')
        if not garment_image:
            return jsonify({'error': 'Giysi fotoğrafı gerekli'}), 400

        category = request.form.get('category', 'tops')
        if category not in VALID_CATEGORIES:
            category = 'tops'

        def get_base64_image(file):
            try:
                file.seek(0)
                file_data = file.read()
                base64_data = base64.b64encode(file_data).decode('utf-8')
                return f"data:image/jpeg;base64,{base64_data}"
            except Exception as e:
                print(f"Base64 dönüşüm hatası: {str(e)}")
                raise

        payload = {
            "model_image": get_base64_image(model_image),
            "garment_image": get_base64_image(garment_image),
            "category": category
        }

        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'Authorization': API_KEY
        }

        print(f"Gönderilen kategori: {category}")

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            print(f"API Yanıt Kodu: {response.status_code}")
            print(f"API Yanıt İçeriği: {response.text}")
            return jsonify({'error': f'API hatası: {response.text}'}), response.status_code

        response_data = response.json()
        print("API Yanıtı:", response_data)

        job_id = response_data.get('id')
        if not job_id:
            return jsonify({'error': 'API yanıtında job_id bulunamadı'}), 500

        return jsonify({
            'status': 'success',
            'job_id': job_id,
            'message': 'İşlem başlatıldı'
        })

    except Exception as e:
        print(f"Genel hata: {str(e)}")
        return jsonify({'error': f'Bir hata oluştu: {str(e)}'}), 500

@app.route('/check_status/<job_id>')
def check_status(job_id):
    try:
        headers = {'Authorization': API_KEY}
        response = requests.get(f"https://api.fashn.ai/v1/status/{job_id}", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'completed':
                return jsonify({
                    'status': 'completed',
                    'output': result.get('output')
                })
            return jsonify(result)
        return jsonify({'error': 'API hatası'}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=4000)
