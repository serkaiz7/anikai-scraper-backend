from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)
CORS(app)

GOGO_BASE = "https://gogoanime3.co"

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

@app.route('/api/search', methods=['GET'])
def search_anime():
    query = request.args.get('keyword', '').strip()
    if not query:
        return jsonify([])
    
    encoded_query = urllib.parse.quote(query)
    search_url = f"{GOGO_BASE}/search.html?keyword={encoded_query}"
    
    try:
        r = requests.get(search_url, headers=get_headers(), timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        
        items_container = soup.find('ul', class_='items')
        if items_container:
            for li in items_container.find_all('li'):
                name_p = li.find('p', class_='name')
                img_tag = li.find('img')
                a_tag = li.find('a')
                
                if name_p and img_tag and a_tag:
                    results.append({
                        'title': name_p.text.strip(),
                        'image': img_tag.get('src', ''),
                        'id': a_tag.get('href', '').replace('/category/', '')
                    })
                    
        if not results:
            results.append({'title': query.title(), 'image': 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600', 'id': query.lower().replace(' ', '-')})
        return jsonify(results)
    except Exception:
        return jsonify([{'title': query.title(), 'image': 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600', 'id': query.lower().replace(' ', '-')}])

@app.route('/api/anime/<alias>', methods=['GET'])
def get_anime_details(alias):
    url = f"{GOGO_BASE}/category/{alias}"
    try:
        r = requests.get(url, headers=get_headers(), timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        ep_page = soup.find('ul', id='episode_page')
        total_eps = 12
        if ep_page and ep_page.find_all('li'):
            a_tag = ep_page.find_all('li')[-1].find('a')
            if a_tag and a_tag.get('ep_end'):
                total_eps = int(a_tag.get('ep_end'))
        return jsonify({'title': alias.replace('-', ' ').title(), 'total_episodes': total_eps})
    except Exception:
        return jsonify({'title': alias.replace('-', ' ').title(), 'total_episodes': 24})

@app.route('/api/stream', methods=['GET'])
def get_stream():
    alias = request.args.get('id', '').strip()
    episode = request.args.get('ep', '1').strip()
    
    # Clean up names to get standard streaming IDs
    clean_id = alias.replace("-sub", "").replace("-dub", "")
    
    # Use a premium direct-embed player index that explicitly allows third-party websites to play streams without loading blocks
    direct_stream_url = f"https://vidsrc.me/embed/anime/{clean_id}/{episode}"
    
    return jsonify({
        'stream_url': direct_stream_url,
        'type': 'iframe'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
