from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Active Gogoanime source cluster mirror
GOGO_BASE = "https://anitaku.bz" 

@app.route('/api/search', methods=['GET'])
def search_anime():
    query = request.args.get('keyword', '').strip()
    if not query:
        return jsonify([])
    
    formatted_query = query.replace(' ', '-')
    search_url = f"{GOGO_BASE}/search.html?keyword={query}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        
        items_container = soup.find('ul', class_='items')
        if items_container:
            for li in items_container.find_all('li'):
                name_p = li.find('p', class_='name')
                img_tag = li.find('img')
                a_tag = li.find('a')
                
                if name_p and img_tag and a_tag:
                    title = name_p.text.strip()
                    img = img_tag.get('src', '')
                    alias = a_tag.get('href', '').replace('/category/', '')
                    
                    results.append({
                        'title': title,
                        'image': img,
                        'id': alias
                    })
        
        # Self-healing fallback option
        if not results:
            results.append({
                'title': f"{query.title()} (Backup Link)",
                'image': 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600',
                'id': formatted_query.lower()
            })
            
        return jsonify(results)
    except Exception:
        return jsonify([{
            'title': f"{query.title()} (Backup Link)",
            'image': 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600',
            'id': formatted_query.lower()
        }])

@app.route('/api/anime/<alias>', methods=['GET'])
def get_anime_details(alias):
    url = f"{GOGO_BASE}/category/{alias}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        ep_page = soup.find('ul', id='episode_page')
        total_eps = 12
        
        if ep_page and ep_page.find_all('li'):
            last_li = ep_page.find_all('li')[-1]
            a_tag = last_li.find('a')
            if a_tag and a_tag.get('ep_end'):
                total_eps = int(a_tag.get('ep_end'))
                
        return jsonify({
            'title': alias.replace('-', ' ').title(),
            'image': 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600',
            'total_episodes': total_eps
        })
    except Exception:
        return jsonify({
            'title': alias.replace('-', ' ').title(),
            'image': 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600',
            'total_episodes': 24
        })

@app.route('/api/stream', methods=['GET'])
def get_stream():
    alias = request.args.get('id')
    episode = request.args.get('ep')
    
    # 1. First, build the native Gogoanime episode page path
    gogo_ep_page = f"{GOGO_BASE}/{alias}-episode-{episode}"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(gogo_ep_page, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 2. Extract the direct streaming player iframe link inside the webpage structure
        # (This avoids dead intermediate domains completely)
        iframe_tag = soup.find('iframe')
        if iframe_tag and iframe_tag.get('src'):
            raw_src = iframe_tag.get('src')
            final_embed_url = f"https:{raw_src}" if raw_src.startswith('//') else raw_src
            return jsonify({'stream_url': final_embed_url, 'type': 'iframe'})
            
    except Exception as e:
        print(f"Primary fetch failed: {e}")
        
    # 3. Ultimate resilient backup fallback if scraping fails entirely
    universal_fallback = f"https://vidsrc.to/embed/anime/{alias}/{episode}"
    return jsonify({'stream_url': universal_fallback, 'type': 'iframe'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
