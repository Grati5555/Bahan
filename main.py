import os
import urllib.request

def read_txt(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

def parse_m3u(content):
    channels = []
    lines = content.splitlines()
    current_meta = ""
    for line in lines:
        if line.startswith("#EXTINF:"):
            current_meta = line
        elif line.startswith("http") and current_meta:
            channels.append({'meta': current_meta, 'url': line})
            current_meta = ""
    return channels

def main():
    print("Memulai bot pemrosesan IPTV...")
    data_dir = 'data'
    master_dir = os.path.join(data_dir, 'master')
    categories_dir = os.path.join(data_dir, 'categories')
    
    os.makedirs(master_dir, exist_ok=True)
    os.makedirs(categories_dir, exist_ok=True)
    
    # 1. Baca sumber playlist
    sources = read_txt(os.path.join(data_dir, 'sources.txt')) + read_txt(os.path.join(data_dir, 'playlists.txt'))
    
    all_channels = []
    raw_content = "#EXTM3U\n"
    
    for url in sources:
        try:
            print(f"Mengunduh: {url}")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as res:
                content = res.read().decode('utf-8', errors='ignore')
                raw_content += "\n".join([l for l in content.splitlines() if l.strip() != "#EXTM3U"]) + "\n"
                all_channels.extend(parse_m3u(content))
        except Exception as e:
            print(f"Gagal mengambil {url}: {e}")
            
    # Simpan all.m3u
    all_path = os.path.join(master_dir, 'all.m3u')
    with open(all_path, 'w', encoding='utf-8') as f:
        f.write(raw_content)
    
    # Simpan master.m3u utama
    master_path = os.path.join(master_dir, 'master.m3u')
    with open(master_path, 'w', encoding='utf-8') as f:
        f.write(raw_content)
    print("File master berhasil diperbarui.")

    # 2. Pecah ke folder categories/ berdasarkan nama file
    for cat_file in os.listdir(categories_dir):
        if cat_file.endswith('.m3u'):
            cat_name = os.path.splitext(cat_file)[0].lower()
            cat_content = "#EXTM3U\n"
            
            for ch in all_channels:
                if cat_name in ch['meta'].lower():
                    cat_content += f"{ch['meta']}\n{ch['url']}\n"
            
            with open(os.path.join(categories_dir, cat_file), 'w', encoding='utf-8') as f:
                f.write(cat_content)
            print(f"Memperbarui kategori: {cat_file}")

if __name__ == '__main__':
    main()
