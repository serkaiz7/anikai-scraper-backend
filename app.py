from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import base64

app = Flask(__name__)
CORS(app)  # Allows your GitHub Pages site to talk to this API

GOGO_BASE = "https://anitaku.pe" # Primary Gogoanime mirror used by anipy-cli

@app.route('/api/search', methods=['GET'])
def search_anime():
    query = request.args.get('keyword', '')
    if not query:
        return jsonify([])
    
    search_url = f"{GOGO_BASE}/filter.html?keyword={query}"
    try:
        r = requests.get(search_url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        
        items = soup.find_all('ul', class_='items')
        if items:
            for li in items[0].find_all('li'):
                title = li.find('p', class_='name').text.strip()
                img = li.find('img')['src']
                alias = li.find('a')['href'].replace('/category/', '')
                results.append({'title': title, 'image': img, 'id': alias})
                
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/anime/<alias>', methods=['GET'])
def get_anime_details(alias):
    url = f"{GOGO_BASE}/category/{alias}"
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Get total episode count
        ep_num = soup.find('ul', id='episode_page').find_all('li')[-1].find('a')['ep_end']
        title = soup.find('div', class_='anime_info_body_bg').find('h1').text.strip()
        img = soup.find('div', class_='anime_info_body_bg').find('img')['src']
        
        return jsonify({
            'title': title,
            'image': img,
            'total_episodes': int(ep_num)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream', methods=['GET'])
def get_stream():
    alias = request.args.get('id')
    episode = request.args.get('ep')
    
    # Gogoanime episode page naming convention
    ep_url = f"{GOGO_BASE}/{alias}-episode-{episode}"
    try:
        r = requests.get(ep_url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Extract the embedded video player iframe (Vidstreaming/Gogo_CDN link)
        iframe = soup.find('iframe')
        if iframe:
            iframe_url = "https:" + iframe['src'] if iframe['src'].startswith('//') else iframe['src']
            
            # Note: Directly playing standard iframes avoids CORS errors inside HTML5 players
            return jsonify({'stream_url': iframe_url, 'type': 'iframe'})
            
        return jsonify({'error': 'Stream not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
