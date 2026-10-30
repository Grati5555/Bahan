import os
import urllib.request
import re

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

def parse_m3u_with_options(content):
    """Memecah playlist m3u secara lengkap beserta baris EXTINF, EXTVLCOPT, dan URL-nya."""
    channels = []
    lines = content.splitlines()
    current_extinf = ""
    current_opts = []
    
    for line in lines:
        line_str = line.strip()
        if line_str.startswith("#EXTINF:"):
            if current_extinf:
                # Simpan channel sebelumnya jika ada
                channels.append({'extinf': current_extinf, 'opts': current_opts, 'url': ''})
                current_opts = []
            current_extinf = line_str
        elif line_str.startswith("#EXTVLCOPT:"):
            current_opts.append(line_str)
        elif line_str.startswith("http") and current_extinf:
            channels.append({'extinf': current_extinf, 'opts': current_opts, 'url': line_str})
            current_extinf = ""
            current_opts = []
    return channels

def clean_filename(name):
    """Membersihkan nama kategori agar aman dijadikan nama file."""
    return re.sub(r'[\\/*?:"<>|(),\s]+', '_', name).strip('_').lower()

def main():
    print("Memulai bot pemrosesan IPTV presisi tinggi...")
    data_dir = 'data'
    master_dir = os.path.join(data_dir, 'master')
    categories_dir = os.path.join(data_dir, 'categories')
    
    os.makedirs(master_dir, exist_ok=True)
    os.makedirs(categories_dir, exist_ok=True)
    
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
                        
                all_channels.extend(parse_m3u_with_options(content))
        except Exception as e:
            print(f"Gagal mengambil {url}: {e}")
            
    # 1. Simpan file master utuh
    for filename in ['all.m3u', 'master.m3u']:
        out_path = os.path.join(master_dir, filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(raw_content)
    print("File master berhasil disimpan dengan format lengkap.")

    # 2. Kelompokkan dan simpan perkategori berdasarkan group-title asli
    categories_dict = {}
    for ch in all_channels:
        # Cari group-title di dalamEXTINF menggunakan Regex
        match = re.search(r'group-title="([^"]+)"', ch['extinf'])
        if match:
            group_name = match.group(1)
        else:
            group_name = "Uncategorized"
            
        file_key = clean_filename(group_name)
        if file_key not in categories_dict:
            categories_dict[file_key] = {"title": group_name, "content": "#EXTM3U\n"}
            
        # Susun kembali baris channel lengkap dengan EXTVLCOPT jika ada
        ch_block = ch['extinf'] + "\n"
        for opt in ch['opts']:
            ch_block += opt + "\n"
        ch_block += ch['url'] + "\n"
        
        categories_dict[file_key]["content"] += ch_block

    # Tulis ke file-file m3u di folder categories/
    for file_key, data in categories_dict.items():
        cat_file_path = os.path.join(categories_dir, f"{file_key}.m3u")
        with open(cat_file_path, 'w', encoding='utf-8') as f:
            f.write(data["content"])
        print(f"Kategori '{data['title']}' disimpan ke {file_key}.m3u")

if __name__ == '__main__':
    main()
