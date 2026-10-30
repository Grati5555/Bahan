import os
import urllib.request
import re

def read_sources_with_names(file_path):
    if not os.path.exists(file_path):
        return []
    sources = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                name, url = line.split('=', 1)
                sources.append((name.strip(), url.strip()))
            else:
                sources.append((f"sumber_{idx+1}", line.strip()))
    return sources

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

def is_channel_active(url):
    """Pengecekan yang lebih aman untuk link streaming IPTV."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'VLC/3.0.16'})
        # Menggunakan timeout sedikit lebih lama agar server merespons
        with urllib.request.urlopen(req, timeout=8) as res:
            # Dianggap aktif jika status 200 (OK) atau ada pengalihan (301/302)
            return res.status in [200, 301, 302, 307, 308]
    except urllib.error.HTTPError as e:
        # Beberapa server memberikan error 403/401 tapi link aslinya tetap bisa diputar di player
        if e.code in [401, 403]:
            return True
        return False
    except Exception:
        return False

def main():
    print("Memulai bot pemrosesan IPTV dengan filter aktif yang disempurnakan...")
    data_dir = 'data'
    master_dir = os.path.join(data_dir, 'master')
    os.makedirs(master_dir, exist_ok=True)
    
    all_sources = []
    for txt_file in ['sources.txt', 'playlists.txt', 'sources_tambahan.txt']:
        file_path = os.path.join(data_dir, txt_file)
        all_sources.extend(read_sources_with_names(file_path))
        
    raw_combined_content = "#EXTM3U\n"
    active_channels_list = []
    
    for folder_name, url in all_sources:
        if not url.startswith('http'):
            continue
            
        print(f"Memproses sumber '{folder_name}' dari {url}")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'VLC/3.0.16'})
            with urllib.request.urlopen(req, timeout=15) as res:
                content = res.read().decode('utf-8', errors='ignore')
                
                for line in content.splitlines():
                    l = line.strip()
                    if l and l != "#EXTM3U":
                        raw_combined_content += l + "\n"
                        
                channels = parse_m3u_with_options(content)
                
                # 1. Folder reguler per sumber (tetap dipertahankan normal)
                source_folder_path = os.path.join(data_dir, folder_name)
                os.makedirs(source_folder_path, exist_ok=True)
                
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
                    
                    # Cek aktif untuk folder khusus Aktif
                    if is_channel_active(ch['url']):
                        active_channels_list.append(ch)

                for file_key, data in categories_dict.items():
                    with open(os.path.join(source_folder_path, f"{file_key}.m3u"), 'w', encoding='utf-8') as f:
                        f.write(data["content"])
                        
        except Exception as e:
            print(f"Gagal memproses sumber {folder_name}: {e}")

    # 2. Simpan Master Gabungan
    for filename in ['all.m3u', 'master.m3u']:
        with open(os.path.join(master_dir, filename), 'w', encoding='utf-8') as f:
            f.write(raw_combined_content)

    # 3. Buat Folder Khusus "Aktif"
    active_folder_path = os.path.join(data_dir, "Aktif")
    os.makedirs(active_folder_path, exist_ok=True)
    
    active_categories_dict = {}
    for ch in active_channels_list:
        match = re.search(r'group-title="([^"]+)"', ch['extinf'])
        group_name = match.group(1) if match else "Uncategorized"
        file_key = clean_filename(group_name)
        
        if file_key not in active_categories_dict:
            active_categories_dict[file_key] = {"title": group_name, "content": "#EXTM3U\n"}
            
        ch_block = ch['extinf'] + "\n"
        for opt in ch['opts']:
            ch_block += opt + "\n"
        ch_block += ch['url'] + "\n"
        
        active_categories_dict[file_key]["content"] += ch_block

    for file_key, data in active_categories_dict.items():
        with open(os.path.join(active_folder_path, f"{file_key}.m3u"), 'w', encoding='utf-8') as f:
            f.write(data["content"])
            
    print("Proses selesai dengan filter aktif yang disempurnakan!")

if __name__ == '__main__':
    main()
