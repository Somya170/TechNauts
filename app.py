from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import random
import datetime
import math
import requests

app = Flask(__name__)
CORS(app)

# Indian cities with coordinates - All 25 cities
CITIES_DATA = {
    'Delhi': {'lat': 28.6139, 'lng': 77.2090},
    'Mumbai': {'lat': 19.0760, 'lng': 72.8777},
    'Hyderabad': {'lat': 17.3850, 'lng': 78.4867},
    'Bhopal': {'lat': 23.2599, 'lng': 77.4126},
    'Indore': {'lat': 22.7196, 'lng': 75.8577},
    'Ahmedabad': {'lat': 23.0225, 'lng': 72.5714},
    'Chennai': {'lat': 13.0827, 'lng': 80.2707},
    'Gwalior': {'lat': 26.2183, 'lng': 78.1828},
    'Jaipur': {'lat': 26.9124, 'lng': 75.7873},
    'Varanasi': {'lat': 25.3176, 'lng': 82.9739},
    'Nagpur': {'lat': 21.1458, 'lng': 79.0882},
    'Pune': {'lat': 18.5204, 'lng': 73.8567},
    'Lucknow': {'lat': 26.8467, 'lng': 80.9462},
    'Kanpur': {'lat': 26.4499, 'lng': 80.3319},
    'Patna': {'lat': 25.5941, 'lng': 85.1376},
    'Raipur': {'lat': 21.2514, 'lng': 81.6296},
    'Ranchi': {'lat': 23.3441, 'lng': 85.3096},
    'Bengaluru': {'lat': 12.9716, 'lng': 77.5946},
    'Kolkata': {'lat': 22.5726, 'lng': 88.3639},
    'Surat': {'lat': 21.1702, 'lng': 72.8311},
    'Kochi': {'lat': 9.9312, 'lng': 76.2673},
    'Thiruvananthapuram': {'lat': 8.5241, 'lng': 76.9366},
    'Coimbatore': {'lat': 11.0168, 'lng': 76.9558},
    'Madurai': {'lat': 9.9252, 'lng': 78.1198},
    'Visakhapatnam': {'lat': 17.6868, 'lng': 83.2185}
}

# Ambee API configuration
AMBEE_API_KEY = 
AMBEE_BASE_URL = "https://api.ambeedata.com/latest/by-lat-lng"

# Hugging Face API configuration
HF_API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
HF_HEADERS = {
    "Authorization": "Bearer 
}

def get_quality_from_aqi(aqi):
    if aqi <= 50:
        return 'Good'
    elif aqi <= 100:
        return 'Moderate'
    elif aqi <= 150:
        return 'Unhealthy for Sensitive Groups'
    elif aqi <= 200:
        return 'Unhealthy'
    elif aqi <= 300:
        return 'Very Unhealthy'
    else:
        return 'Hazardous'

def fetch_real_aqi_ambee(city_name, lat, lng):
    """Fetch real-time AQI data from Ambee API"""
    try:
        headers = {
            "x-api-key": AMBEE_API_KEY
        }
        params = {
            "lat": lat,
            "lng": lng
        }
        
        response = requests.get(AMBEE_BASE_URL, headers=headers, params=params, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and 'stations' in data and len(data['stations']) > 0:
            station_data = data['stations'][0]
            aqi = station_data.get('AQI', 0)
            
            # Extract pollutant data if available
            pollutants = {
                'pm25': station_data.get('PM25', 0) or 0,
                'pm10': station_data.get('PM10', 0) or 0,
                'o3': station_data.get('OZONE', 0) or 0,
                'no2': station_data.get('NO2', 0) or 0,
                'so2': station_data.get('SO2', 0) or 0,
                'co': station_data.get('CO', 0) or 0
            }
            
            return {
                'aqi': aqi,
                'quality': get_quality_from_aqi(aqi),
                'pollutants': pollutants,
                'time': station_data.get('updatedAt', datetime.datetime.now().isoformat()),
                'source': 'Ambee API'
            }
    except Exception as e:
        print(f"Error fetching Ambee data for {city_name}: {e}")
    
    # Fallback to mock data if API fails
    base_aqi = random.randint(50, 200)
    return {
        'aqi': base_aqi,
        'quality': get_quality_from_aqi(base_aqi),
        'pollutants': {
            'pm25': int(base_aqi * 0.6),
            'pm10': int(base_aqi * 0.8),
            'o3': int(base_aqi * 0.4),
            'no2': int(base_aqi * 0.3),
            'so2': int(base_aqi * 0.2),
            'co': int(base_aqi * 0.1)
        },
        'time': datetime.datetime.now().isoformat(),
        'source': 'Mock Data'
    }

def calculate_aqi_from_pollutants(pm25, pm10, o3, no2, so2, co):
    """Calculate AQI from individual pollutant concentrations"""
    # Simplified AQI calculation (US EPA standard)
    
    # PM2.5 breakpoints (μg/m³)
    pm25_breakpoints = [(0, 12, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150), 
                        (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 500.4, 301, 500)]
    
    # PM10 breakpoints (μg/m³)
    pm10_breakpoints = [(0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150), 
                        (255, 354, 151, 200), (355, 424, 201, 300), (425, 604, 301, 500)]
    
    def calculate_individual_aqi(concentration, breakpoints):
        for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
            if bp_lo <= concentration <= bp_hi:
                return ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + aqi_lo
        return 500  # Hazardous
    
    pm25_aqi = calculate_individual_aqi(pm25, pm25_breakpoints)
    pm10_aqi = calculate_individual_aqi(pm10, pm10_breakpoints)
    
    # Simplified calculation for other pollutants
    o3_aqi = min(500, o3 * 1.5)
    no2_aqi = min(500, no2 * 2)
    so2_aqi = min(500, so2 * 3)
    co_aqi = min(500, co * 10)
    
    # Return the maximum AQI (worst pollutant determines overall AQI)
    return max(pm25_aqi, pm10_aqi, o3_aqi, no2_aqi, so2_aqi, co_aqi)

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AQI Monitor - Flask Backend with Ambee API</title>
    </head>
    <body>
        <h1>AQI Monitor Flask API - Real-time Data</h1>
        <p>Available endpoints:</p>
        <ul>
            <li>GET /api/cities - Get all 25 cities data (Ambee API)</li>
            <li>GET /api/city/<city_name> - Get specific city data</li>
            <li>GET /api/forecast/<city_name> - Get 7-day forecast</li>
            <li>GET /api/hourly/<city_name>/<date> - Get 24-hour data</li>
            <li>POST /api/calculate-aqi - Calculate AQI from pollutants</li>
            <li>POST /api/chatbot - AI Chatbot for AQI queries</li>
        </ul>
        <h2>Supported Cities (25):</h2>
        <p>Delhi, Mumbai, Hyderabad, Bhopal, Indore, Ahmedabad, Chennai, Gwalior, Jaipur, Varanasi, Nagpur, Pune, Lucknow, Kanpur, Patna, Raipur, Ranchi, Bengaluru, Kolkata, Surat, Kochi, Thiruvananthapuram, Coimbatore, Madurai, Visakhapatnam</p>
    </body>
    </html>
    """)

@app.route('/api/cities')
def get_cities():
    cities = []
    print("🔄 Fetching AQI for 25 Indian cities using Ambee API...")
    
    for name, coords in CITIES_DATA.items():
        aqi_data = fetch_real_aqi_ambee(name, coords['lat'], coords['lng'])
        cities.append({
            'name': name,
            'lat': coords['lat'],
            'lng': coords['lng'],
            'aqi': aqi_data['aqi'],
            'quality': aqi_data['quality'],
            'pm25': aqi_data['pollutants']['pm25'],
            'pm10': aqi_data['pollutants']['pm10'],
            'o3': aqi_data['pollutants']['o3'],
            'no2': aqi_data['pollutants']['no2'],
            'so2': aqi_data['pollutants']['so2'],
            'co': aqi_data['pollutants']['co'],
            'temperature': random.randint(25, 40),
            'humidity': random.randint(30, 80),
            'lastUpdated': aqi_data['time'],
            'source': aqi_data['source']
        })
        print(f"{name:20s} ➤ AQI: {aqi_data['aqi']} ({aqi_data['source']})")
    
    return jsonify(cities)

@app.route('/api/city/<city_name>')
def get_city_data(city_name):
    if city_name not in CITIES_DATA:
        return jsonify({'error': 'City not found'}), 404
    
    coords = CITIES_DATA[city_name]
    aqi_data = fetch_real_aqi_ambee(city_name, coords['lat'], coords['lng'])
    
    return jsonify({
        'city': city_name,
        'aqi': aqi_data['aqi'],
        'quality': aqi_data['quality'],
        'lat': coords['lat'],
        'lng': coords['lng'],
        'pollutants': aqi_data['pollutants'],
        'weather': {
            'temperature': random.randint(25, 40),
            'humidity': random.randint(30, 80),
            'windSpeed': random.randint(5, 25),
            'pressure': random.randint(990, 1020)
        },
        'lastUpdated': aqi_data['time'],
        'source': aqi_data['source']
    })

@app.route('/api/forecast/<city_name>')
def get_forecast(city_name):
    if city_name not in CITIES_DATA:
        return jsonify({'error': 'City not found'}), 404
    
    # Get current real AQI as base
    coords = CITIES_DATA[city_name]
    current_data = fetch_real_aqi_ambee(city_name, coords['lat'], coords['lng'])
    base_aqi = current_data['aqi']
    
    forecast = []
    
    for i in range(7):
        date = datetime.datetime.now() + datetime.timedelta(days=i)
        variation = random.randint(-30, 30)
        day_aqi = max(20, min(300, base_aqi + variation))
        
        forecast.append({
            'date': date.strftime('%Y-%m-%d'),
            'dayName': date.strftime('%A'),
            'aqi': day_aqi,
            'quality': get_quality_from_aqi(day_aqi),
            'temperature': random.randint(25, 40),
            'humidity': random.randint(30, 80),
            'pm25': int(day_aqi * 0.6),
            'pm10': int(day_aqi * 0.8),
            'o3': int(day_aqi * 0.4),
            'no2': int(day_aqi * 0.3),
            'so2': int(day_aqi * 0.2),
            'co': int(day_aqi * 0.1)
        })
    
    return jsonify(forecast)

@app.route('/api/hourly/<city_name>/<date>')
def get_hourly_data(city_name, date):
    if city_name not in CITIES_DATA:
        return jsonify({'error': 'City not found'}), 404
    
    # Get current real AQI as base
    coords = CITIES_DATA[city_name]
    current_data = fetch_real_aqi_ambee(city_name, coords['lat'], coords['lng'])
    base_aqi = current_data['aqi']
    
    hourly_data = []
    
    for hour in range(24):
        # Simulate daily AQI variation (higher during rush hours)
        time_factor = 1.0
        if 7 <= hour <= 10 or 17 <= hour <= 20:  # Rush hours
            time_factor = 1.3
        elif 2 <= hour <= 6:  # Early morning (cleaner)
            time_factor = 0.7
        
        hour_aqi = int(base_aqi * time_factor + random.randint(-15, 15))
        hour_aqi = max(20, min(300, hour_aqi))
        
        hourly_data.append({
            'hour': f"{hour:02d}:00",
            'aqi': hour_aqi,
            'quality': get_quality_from_aqi(hour_aqi),
            'pm25': int(hour_aqi * 0.6),
            'pm10': int(hour_aqi * 0.8),
            'o3': int(hour_aqi * 0.4),
            'no2': int(hour_aqi * 0.3),
            'so2': int(hour_aqi * 0.2),
            'co': int(hour_aqi * 0.1),
            'temperature': random.randint(25, 40),
            'humidity': random.randint(30, 80)
        })
    
    return jsonify(hourly_data)

@app.route('/api/calculate-aqi', methods=['POST'])
def calculate_aqi():
    data = request.get_json()
    
    try:
        pm25 = float(data.get('pm25', 0))
        pm10 = float(data.get('pm10', 0))
        o3 = float(data.get('o3', 0))
        no2 = float(data.get('no2', 0))
        so2 = float(data.get('so2', 0))
        co = float(data.get('co', 0))
        
        calculated_aqi = calculate_aqi_from_pollutants(pm25, pm10, o3, no2, so2, co)
        
        return jsonify({
            'aqi': round(calculated_aqi),
            'quality': get_quality_from_aqi(calculated_aqi),
            'pollutants': {
                'pm25': pm25,
                'pm10': pm10,
                'o3': o3,
                'no2': no2,
                'so2': so2,
                'co': co
            },
            'calculation_time': datetime.datetime.now().isoformat()
        })
    
    except (ValueError, TypeError) as e:
        return jsonify({'error': 'Invalid pollutant values provided'}), 400

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Prepare the prompt with AQI context
        prompt = f"""You are an AI assistant specialized in air quality and environmental health. 
        Answer questions about AQI (Air Quality Index), pollution, health effects, and environmental protection.
        Keep responses concise and helpful.
        
        User question: {user_message}
        
        Assistant:"""
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 0.7,
                "return_full_text": False
            }
        }
        
        response = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=30)
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            bot_response = result[0].get('generated_text', 'Sorry, I could not process your request.')
        else:
            bot_response = 'Sorry, I could not process your request.'
        
        return jsonify({
            'response': bot_response.strip(),
            'timestamp': datetime.datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({
            'response': 'Sorry, I am currently unavailable. Please try again later.',
            'timestamp': datetime.datetime.now().isoformat()
        })

if __name__ == '__main__':
    print("🚀 Starting AQI Monitor with Ambee API integration...")
    print("📍 Monitoring 25 Indian cities with real-time data")
    app.run(debug=True, port=5000)