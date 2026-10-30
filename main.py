import os
import urllib.request

def read_txt(file_path):
    if not os.path.exists(file_path):
        return []
    urls = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                parts = line.split('=', 1)
                url = parts[1].strip()
            else:
                url = line
            if url.startswith('http'):
                urls.append(url)
    return urls

def parse_m3u(content):
    channels = []
    lines = content.splitlines()
    current_meta = ""
    for line in lines:
        line_str = line.strip()
        if line_str.startswith("#EXTINF:"):
            current_meta = line_str
        elif line_str.startswith("http") and current_meta:
            channels.append({'meta': current_meta, 'url': line_str})
            current_meta = ""
    return channels

def main():
    print("Memulai bot pemrosesan IPTV & Kategori...")
    data_dir = 'data'
    master_dir = os.path.join(data_dir, 'master')
    categories_dir = os.path.join(data_dir, 'categories')
    
    os.makedirs(master_dir, exist_ok=True)
    os.makedirs(categories_dir, exist_ok=True)
    
    # 1. Pertahankan proses utama (sources & playlists)
    sources = read_txt(os.path.join(data_dir, 'sources.txt')) + read_txt(os.path.join(data_dir, 'playlists.txt'))
    print(f"Ditemukan {len(sources)} tautan sumber.")
    
    all_channels = []
    raw_content = "#EXTM3U\n"
    
    for url in sources:
        try:
            print(f"Mengunduh: {url}")
            req = urllib.request.Request(url, headers={'User-Agent': 'VLC/3.0.16'})
            with urllib.request.urlopen(req, timeout=15) as res:
                content = res.read().decode('utf-8', errors='ignore')
                
                for line in content.splitlines():
                    l = line.strip()
                    if l and l != "#EXTM3U":
                        raw_content += l + "\n"
                        
                all_channels.extend(parse_m3u(content))
        except Exception as e:
            print(f"Gagal mengambil {url}: {e}")
            
    # Simpan hasil master yang sudah ada
    for filename in ['all.m3u', 'master.m3u']:
        out_path = os.path.join(master_dir, filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(raw_content)
    print("File master berhasil dipertahankan dan diperbarui.")

    # 2. Tambahkan hasil M3U perkategori secara otomatis
    # Daftar kategori default yang sering dicari (bisa Anda tambah atau sesuaikan)
    default_categories = [
        "rcti", "sctv", "indosiar", "antv", "transtv", "trans7", 
        "metrotv", "tvri", "kompastv", "gtv", "inews", "rtv"
    ]
    
    # Ambil juga file kategori tambahan jika Anda sudah membuat filenya di folder categories/
    existing_files = [os.path.splitext(f)[0].lower() for f in os.listdir(categories_dir) if f.endswith('.m3u')]
    all_categories = list(set(default_categories + existing_files))

    for cat_name in all_categories:
        cat_content = "#EXTM3U\n"
        match_count = 0
        
        for ch in all_channels:
            if cat_name in ch['meta'].lower():
                cat_content += f"{ch['meta']}\n{ch['url']}\n"
                match_count += 1
        
        # Simpan file kategori meskipun filenya belum pernah dibuat manual sebelumnya
        cat_file_path = os.path.join(categories_dir, f"{cat_name}.m3u")
        with open(cat_file_path, 'w', encoding='utf-8') as f:
            f.write(cat_content)
        print(f"Kategori {cat_name}.m3u: menyimpan {match_count} channel.")

if __name__ == '__main__':
    main()
