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
    channels = []
    lines = content.splitlines()
    current_extinf = ""
    current_opts = []
    
    for line in lines:
        line_str = line.strip()
        if line_str.startswith("#EXTINF:"):
            if current_extinf:
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
    return re.sub(r'[\\/*?:"<>|(),\s]+', '_', name).strip('_').lower()

def process_sources_to_folder(sources_list, folder_name, categories_base_dir):
    """Mengunduh dan memecah kategori untuk setiap sumber spesifik ke dalam folder terpisah."""
    folder_path = os.path.join(categories_base_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    channels = []
    for url in sources_list:
        try:
            print(f"Mengunduh [{folder_name}]: {url}")
            req = urllib.request.Request(url, headers={'User-Agent': 'VLC/3.0.16'})
            with urllib.request.urlopen(req, timeout=15) as res:
                content = res.read().decode('utf-8', errors='ignore')
                channels.extend(parse_m3u_with_options(content))
        except Exception as e:
            print(f"Gagal mengambil {url} untuk {folder_name}: {e}")
            
    # Kelompokkan perkategori untuk sumber ini
    categories_dict = {}
    for ch in channels:
        match = re.search(r'group-title="([^"]+)"', ch['extinf'])
        group_name = match.group(1) if match else "Uncategorized"
            
        file_key = clean_filename(group_name)
        if file_key not in categories_dict:
            categories_dict[file_key] = {"title": group_name, "content": "#EXTM3U\n"}
            
        ch_block = ch['extinf'] + "\n"
        for opt in ch['opts']:
            ch_block += opt + "\n"
        ch_block += ch['url'] + "\n"
        
        categories_dict[file_key]["content"] += ch_block

    # Simpan file M3U perkategori ke dalam sub-folder sumber (misal: categories/Akma/)
    for file_key, data in categories_dict.items():
        cat_file_path = os.path.join(folder_path, f"{file_key}.m3u")
        with open(cat_file_path, 'w', encoding='utf-8') as f:
            f.write(data["content"])
    print(f"Folder kategori '{folder_name}' berhasil diperbarui.")

def main():
    print("Memulai bot pemrosesan IPTV multi-folder...")
    data_dir = 'data'
    master_dir = os.path.join(data_dir, 'master')
    categories_dir = os.path.join(data_dir, 'categories')
    
    os.makedirs(master_dir, exist_ok=True)
    os.makedirs(categories_dir, exist_ok=True)
    
    # 1. Definisikan Sumber Anda
    sumber_akma = read_txt(os.path.join(data_dir, 'sources.txt')) + read_txt(os.path.join(data_dir, 'playlists.txt'))
    sumber_tambahan = read_txt(os.path.join(data_dir, 'sources_tambahan.txt'))
    
    all_channels_combined = []
    raw_combined_content = "#EXTM3U\n"
    
    # 2. Proses Folder Spesifik "Akma" (dari sumber utama)
    if sumber_akma:
        process_sources_to_folder(sumber_akma, "Akma", categories_dir)
        for url in sumber_akma:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'VLC/3.0.16'})
                with urllib.request.urlopen(req, timeout=15) as res:
                    content = res.read().decode('utf-8', errors='ignore')
                    for line in content.splitlines():
                        l = line.strip()
                        if l and l != "#EXTM3U":
                            raw_combined_content += l + "\n"
            except:
                pass

    # 3. Proses Folder Spesifik "Tambahan" (dari sources_tambahan.txt)
    if sumber_tambahan:
        process_sources_to_folder(sumber_tambahan, "Tambahan", categories_dir)
        for url in sumber_tambahan:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'VLC/3.0.16'})
                with urllib.request.urlopen(req, timeout=15) as res:
                    content = res.read().decode('utf-8', errors='ignore')
                    for line in content.splitlines():
                        l = line.strip()
                        if l and l != "#EXTM3U":
                            raw_combined_content += l + "\n"
            except:
                pass

    # 4. Simpan Hasil Gabungan Semua Sumber ke Master (Tetap Dipertahankan)
    for filename in ['all.m3u', 'master.m3u']:
        out_path = os.path.join(master_dir, filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(raw_combined_content)
    print("File master gabungan keseluruhan berhasil diperbarui.")

if __name__ == '__main__':
    main()
