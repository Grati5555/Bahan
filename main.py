import os
import urllib.request
import re

def read_sources_with_names(file_path):
    """Membaca file txt dengan format [nama_folder]=[url] atau hanya [url]."""
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

def main():
    print("Memulai bot pemrosesan IPTV per-folder sumber langsung di data/...")
    data_dir = 'data'
    master_dir = os.path.join(data_dir, 'master')
    os.makedirs(master_dir, exist_ok=True)
    
    # Ambil semua sumber dari file konfigurasi txt
    all_sources = []
    for txt_file in ['sources.txt', 'playlists.txt', 'sources_tambahan.txt']:
        file_path = os.path.join(data_dir, txt_file)
        all_sources.extend(read_sources_with_names(file_path))
        
    print(f"Total sumber ditemukan: {len(all_sources)}")
    
    raw_combined_content = "#EXTM3U\n"
    
    # Proses setiap sumber ke foldernya masing-masing langsung di dalam 'data/'
    for folder_name, url in all_sources:
        if not url.startswith('http'):
            continue
            
        print(f"Memproses sumber '{folder_name}' dari {url}")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'VLC/3.0.16'})
            with urllib.request.urlopen(req, timeout=15) as res:
                content = res.read().decode('utf-8', errors='ignore')
                
                # Tambahkan ke master gabungan keseluruhan
                for line in content.splitlines():
                    l = line.strip()
                    if l and l != "#EXTM3U":
                        raw_combined_content += l + "\n"
                        
                # Parse channel untuk dipecah perkategori
                channels = parse_m3u_with_options(content)
                
                # Buat folder khusus sumber langsung di dalam data/ (contoh: data/Akma/)
                source_folder_path = os.path.join(data_dir, folder_name)
                os.makedirs(source_folder_path, exist_ok=True)
                
                # Kelompokkan perkategori berdasarkan group-title
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

                # Simpan file M3U perkategori ke dalam folder sumber tersebut
                for file_key, data in categories_dict.items():
                    cat_file_path = os.path.join(source_folder_path, f"{file_key}.m3u")
                    with open(cat_file_path, 'w', encoding='utf-8') as f:
                        f.write(data["content"])
                print(f"Folder '{folder_name}' berhasil diisi file kategori.")
        except Exception as e:
            print(f"Gagal memproses sumber {folder_name} ({url}): {e}")

    # Simpan file master gabungan keseluruhan (tetap dipertahankan)
    for filename in ['all.m3u', 'master.m3u']:
        out_path = os.path.join(master_dir, filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(raw_combined_content)
    print("File master gabungan berhasil diperbarui.")

if __name__ == '__main__':
    main()
