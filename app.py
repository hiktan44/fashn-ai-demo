from flask import Flask, render_template, request, jsonify
import base64
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
API_URL = 'https://api.fashn.ai/v1/run'
API_KEY = os.getenv('API_KEY')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        model_image = request.files['model_image']
        garment_image = request.files['garment_image']
        category = request.form['category']
        
        # Dosyaları base64'e dönüştür
        model_image_bytes = model_image.read()
        garment_image_bytes = garment_image.read()

        model_image_base64 = base64.b64encode(model_image_bytes).decode('utf-8')
        garment_image_base64 = base64.b64encode(garment_image_bytes).decode('utf-8')

        model_mime = model_image.content_type or 'image/jpeg'
        garment_mime = garment_image.content_type or 'image/jpeg'

        model_image_data = f"data:{model_mime};base64,{model_image_base64}"
        garment_image_data = f"data:{garment_mime};base64,{garment_image_base64}"

        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }

        data = {
            'model_image': model_image_data,
            'garment_image': garment_image_data,
            'category': category
        }

        print("API isteği gönderiliyor...")
        response = requests.post(API_URL, json=data, headers=headers)
        response_data = response.json()
        print(f"API yanıtı: {response_data}")

        # İşlem durumunu kontrol et
        job_id = response_data.get('id')
        if job_id:
            status_response = requests.get(
                f"https://api.fashn.ai/v1/status/{job_id}",
                headers={'Authorization': f'Bearer {API_KEY}'}
            )
            status_data = status_response.json()
            
            # Eğer işlem tamamlandıysa, sonucu doğrudan döndür
            if status_data.get('status') == 'completed':
                return jsonify(status_data)
            
            # Değilse, işlem ID'sini döndür
            return jsonify(response_data)
        
        return jsonify({'error': 'İşlem ID alınamadı'}), 500

    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/check_status/<job_id>')
def check_status(job_id):
    try:
        headers = {'Authorization': f'Bearer {API_KEY}'}
        response = requests.get(f"https://api.fashn.ai/v1/status/{job_id}", headers=headers)
        status_data = response.json()
        print(f"Status kontrolü: {status_data}")
        
        # Eğer işlem tamamlandıysa ve çıktı varsa, HTML içinde görüntüyü döndür
        if status_data.get('status') == 'completed' and status_data.get('output'):
            return jsonify(status_data)
        
        return jsonify(status_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=4000, debug=True)
