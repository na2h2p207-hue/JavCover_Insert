import os
import re
import sys
import argparse
import time
import requests
import io
import cloudscraper

# Try importing mutagen
try:
    from mutagen.mp4 import MP4, MP4Cover
except ImportError:
    print("WARNING: 'mutagen' library not found. Cover art embedding will be skipped.")
    print("To enable cover art, run: pip install mutagen")
    MP4 = None

# Try importing Pillow
try:
    from PIL import Image
except ImportError:
    print("WARNING: 'Pillow' library not found. Cover art cropping will be skipped.")
    print("To enable cropping, run: pip install Pillow")
    Image = None

# Force UTF-8 for output
if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
if sys.stderr is not None:
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def clean_filename(title):
    # Remove illegal characters for Windows filenames
    cleaned = re.sub(r'[\\/*?:"<>|]', "", title)
    return cleaned.strip()

def process_and_save_cover(image_data, save_path):
    """
    Crops the image (keeping right side) and saves it to disk.
    Returns the bytes of the processed image for embedding.
    """
    if Image is None:
        # Fallback if Pillow not installed: just write raw data
        with open(save_path, 'wb') as f:
            f.write(image_data)
        return image_data

    try:
        with Image.open(io.BytesIO(image_data)) as img:
            width, height = img.size
            CROP_RATIO = 378 / 800
            
            # Only crop if it's a wide image (landscape)
            if width > height:
                new_width = int(width * CROP_RATIO)
                # Keep RIGHT side
                left = width - new_width
                top = 0
                right = width
                bottom = height
                
                img = img.crop((left, top, right, bottom))
                print(f"    [Cover] Cropped to {new_width}x{height} (Right Side).")
            
            img.save(save_path, quality=95, subsampling=0)
            print(f"[COVER_PATH] {save_path}")
            
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95, subsampling=0)
            return output.getvalue()
            
    except Exception as e:
        print(f"    [Cover] Cropping failed, using original: {e}")
        with open(save_path, 'wb') as f:
            f.write(image_data)
        return image_data

def check_file_structure(video_path):
    import struct
    try:
        with open(video_path, 'rb') as f:
            offset = 0
            atoms = []
            while offset < 200:
                f.seek(offset)
                header = f.read(8)
                if len(header) < 8: break
                size = struct.unpack('>I', header[:4])[0]
                atom_type = header[4:8].decode('latin-1', errors='replace')
                atoms.append((atom_type, offset, size))
                if size <= 0 or size > 100000000: break
                offset += size
            
            for atom_type, atom_offset, _ in atoms:
                if atom_type == 'dat' and atom_offset < 100:
                    return True, "Invalid 'dat' atom found (LosslessCut corruption)"
            return False, None
    except Exception as e:
        return False, f"Error checking structure: {e}"

def apply_faststart(video_path, verify_cover=True):
    import subprocess
    import shutil
    import struct
    import gc

    if verify_cover and MP4 is not None:
        try:
            gc.collect()
            v = MP4(video_path)
            had_cover = "covr" in v
            del v
        except: pass
    
    try:
        gc.collect()
        with open(video_path, 'rb') as f:
            offset = 0
            file_size = os.path.getsize(video_path)
            while offset < min(file_size, 50000000):
                f.seek(offset)
                header = f.read(8)
                if len(header) < 8: break
                size = struct.unpack('>I', header[:4])[0]
                atom_type = header[4:8].decode('latin-1', errors='replace')
                if size == 1:
                    extended_header = f.read(8)
                    if len(extended_header) == 8: size = struct.unpack('>Q', extended_header)[0]
                elif size == 0: size = file_size - offset
                
                if atom_type == 'moov':
                    if offset == 28:
                        print(f"    [Faststart] moov already at offset 28. Skipping.")
                        return True
                    elif offset < 50000000:
                        print(f"    [Faststart] moov at offset {offset} (not 28). Re-running faststart to standardize...")
                        break
                    else:
                        print(f"    [Faststart] moov at offset {offset} (END). Running faststart...")
                        break
                offset += size
                if offset <= 0: break
    except Exception as e:
        print(f"    [Faststart] Could not check moov position: {e}")
    
    temp_path = video_path + ".faststart.mp4"
    bak_path = video_path + ".bak"
    
    try:
        print(f"    [Faststart] Moving moov atom to beginning (targeting offset 28)...")
        result = subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "quiet",
             "-i", video_path, "-c", "copy", "-movflags", "+faststart",
             temp_path],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        
        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    gc.collect()
                    if os.path.exists(bak_path): os.remove(bak_path)
                    os.rename(video_path, bak_path)
                    try:
                        os.rename(temp_path, video_path)
                        try: os.remove(bak_path)
                        except: pass
                        print(f"    [Faststart] SUCCESS! moov atom moved and standardized.")
                        return True
                    except Exception as e2:
                        print(f"    [Faststart] Swap failed, restoring original: {e2}")
                        if os.path.exists(bak_path): shutil.move(bak_path, video_path)
                        raise e2
                except PermissionError as e:
                    if attempt < max_retries - 1: time.sleep((attempt + 1) * 5)
                    else:
                        print(f"    [Faststart] Failed after {max_retries} retries: {e}")
                        return False
            return False
        else:
            if os.path.exists(temp_path): os.remove(temp_path)
            print(f"    [Faststart] Failed - temp file creation failed.")
            return False
    except FileNotFoundError:
        print("    [Faststart] ERROR: FFmpeg not found! Please install FFmpeg.")
        return False
    except Exception as e:
        print(f"    [Faststart] ERROR: {e}")
        return False

def repair_with_ffmpeg(video_path):
    import subprocess
    import shutil
    print(f"    [Repair] Detected corrupted file structure. Repairing with FFmpeg...")
    temp_path = video_path + ".repaired.mp4"
    backup_path = video_path + ".corrupt.bak"
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
            "-i", video_path, "-c", "copy", "-movflags", "+faststart",
            temp_path],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        if result.returncode != 0 or not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            if os.path.exists(temp_path): os.remove(temp_path)
            return False, video_path
        try:
            shutil.move(video_path, backup_path)
            shutil.move(temp_path, video_path)
            print(f"    [Repair] ✓ File repaired successfully!")
            return True, video_path
        except Exception as e:
            if os.path.exists(backup_path): shutil.move(backup_path, video_path)
            return False, video_path
    except Exception as e:
        print(f"    [Repair] ERROR: {e}")
        return False, video_path

def embed_cover(video_path, image_data):
    if MP4 is None: return
    try:
        video = MP4(video_path)
        video["covr"] = [MP4Cover(image_data, imageformat=MP4Cover.FORMAT_JPEG)]
        video.save()
        
        video_reread = MP4(video_path)
        if "covr" in video_reread: print(f"    [Cover] Successfully embedded and VERIFIED (Size: {len(video_reread['covr'][0])} bytes).")
        else: print("    [Cover] WARNING: Embedded but 'covr' not found on re-read.")
        del video_reread
        del video
        time.sleep(2)
    except Exception as e:
        print(f"    [Cover] Failed to embed cover: {e}")

def _extract_metadata_from_page(detail_html, code, scraper):
    """Helper to extract title and cover from a JavTrailers detail page."""
    # Extract Title
    # Priority: og:description > twitter:description > meta description > h1
    title = None
    
    # Method 1: og:description (BEST - has correct title)
    og_desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', detail_html, re.IGNORECASE)
    if og_desc_match:
        raw_title = og_desc_match.group(1)
        # Remove code prefix (with flexible matching for zeros)
        code_pattern = re.escape(code.split('-')[0]) + r'-?0*' + re.escape(code.split('-')[1].lstrip('0'))
        clean_t = re.sub(code_pattern, "", raw_title, flags=re.IGNORECASE)
        title = clean_t.strip(" -")
    
    # Method 2: twitter:description
    if not title:
        tw_desc_match = re.search(r'<meta name="twitter:description" content="([^"]+)"', detail_html, re.IGNORECASE)
        if tw_desc_match:
            raw_title = tw_desc_match.group(1)
            code_pattern = re.escape(code.split('-')[0]) + r'-?0*' + re.escape(code.split('-')[1].lstrip('0'))
            clean_t = re.sub(code_pattern, "", raw_title, flags=re.IGNORECASE)
            title = clean_t.strip(" -")
    
    # Method 3: meta description
    if not title:
        desc_match = re.search(r'<meta name="description" content="([^"]+)"', detail_html, re.IGNORECASE)
        if desc_match:
            raw_title = desc_match.group(1)
            code_pattern = re.escape(code.split('-')[0]) + r'-?0*' + re.escape(code.split('-')[1].lstrip('0'))
            clean_t = re.sub(code_pattern, "", raw_title, flags=re.IGNORECASE)
            title = clean_t.strip(" -")
    
    # Method 4: h1 fallback
    if not title:
        h1_match = re.search(r'<h1>(.*?)</h1>', detail_html, re.IGNORECASE)
        if h1_match:
            raw_title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
            code_pattern = re.escape(code.split('-')[0]) + r'-?0*' + re.escape(code.split('-')[1].lstrip('0'))
            clean_t = re.sub(code_pattern, "", raw_title, flags=re.IGNORECASE)
            title = clean_t.strip(" -")
    
    if title:
        # Remove duplicate suffixes/names
        def remove_duplicates(text):
            parts = text.split()
            if len(parts) >= 2 and parts[-1] == parts[-2]:
                text = ' '.join(parts[:-1])
            for length in range(2, min(20, len(text) // 2 + 1)):
                suffix = text[-length:]
                if text[-2*length:-length] == suffix:
                    text = text[:-length]
                    break
            return text
        title = remove_duplicates(title)
    
    # Extract Cover URL
    cover_url = None
    og_img = re.search(r'<meta property="og:image" content="([^"]+)"', detail_html)
    if og_img:
        cover_url = og_img.group(1)
    
    return title, cover_url

def get_metadata_via_jt_cloudscraper(code):
    """
    Scrape JavTrailers using cloudscraper (JavSP logic replacement).
    Returns: (title, cover_url)
    """
    scraper = cloudscraper.create_scraper()
    
    # Primary: Search
    search_url = f"https://javtrailers.com/ja/search/{code}"
    print(f"  [JavTrailers] Scraping Search: {search_url}")
    
    try:
        resp = scraper.get(search_url, timeout=30)
        if resp.status_code != 200:
            print(f"  [JavTrailers] Search failed (Status {resp.status_code})")
            return None, None
        
        html = resp.text
        # Find first result: <a href="/ja/video/..." class="video-link">
        link_match = re.search(r'<a href="(/ja/video/[^"]+)" class="video-link"', html)
        
        if not link_match:
            # Fallback: Try direct URL (e.g., ABW-009 -> 118abw00009)
            code_match = re.match(r'^([A-Z]+)-?(\d+)$', code.upper())
            if code_match:
                prefix = code_match.group(1).lower()
                number = code_match.group(2).zfill(5)  # Pad to 5 digits
                direct_url = f"https://javtrailers.com/ja/video/118{prefix}{number}"
                print(f"  [JavTrailers] Search no results, trying direct URL: {direct_url}")
                
                try:
                    resp = scraper.get(direct_url, timeout=30)
                    if resp.status_code == 200 and '<h1>' in resp.text:
                        print(f"  [JavTrailers] Direct URL success!")
                        return _extract_metadata_from_page(resp.text, code, scraper)
                except Exception as e:
                    print(f"  [JavTrailers] Direct URL failed: {e}")
            
            print("  [JavTrailers] No results found.")
            return None, None
            
        href = link_match.group(1)
        detail_url = f"https://javtrailers.com{href}"
        print(f"  [JavTrailers] Found detail URL: {detail_url}")
        
        # Request Detail Page
        resp_detail = scraper.get(detail_url, timeout=30)
        if resp_detail.status_code != 200:
             print(f"  [JavTrailers] Detail page failed (Status {resp_detail.status_code})")
             return None, None
        
        detail_html = resp_detail.text
        
        # Verify Code
        if code.upper() not in detail_html.upper():
             print(f"  [JavTrailers] WARNING: Code {code} not found on detail page.")
             return None, None
             
        # Extract Title
        # Priority: og:description > twitter:description > meta description > h1
        title = None
        
        # Method 1: og:description (BEST - has correct title)
        og_desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', detail_html, re.IGNORECASE)
        if og_desc_match:
            raw_title = og_desc_match.group(1)
            clean_t = re.sub(f"^{re.escape(code)}", "", raw_title, flags=re.IGNORECASE)
            title = clean_t.strip(" -")
        
        # Method 2: twitter:description
        if not title:
            tw_desc_match = re.search(r'<meta name="twitter:description" content="([^"]+)"', detail_html, re.IGNORECASE)
            if tw_desc_match:
                raw_title = tw_desc_match.group(1)
                clean_t = re.sub(f"^{re.escape(code)}", "", raw_title, flags=re.IGNORECASE)
                title = clean_t.strip(" -")
        
        # Method 3: meta description (may have wrong suffix like Tsubomi)
        if not title:
            desc_match = re.search(r'<meta name="description" content="([^"]+)"', detail_html, re.IGNORECASE)
            if desc_match:
                raw_title = desc_match.group(1)
                clean_t = re.sub(f"^{re.escape(code)}", "", raw_title, flags=re.IGNORECASE)
                title = clean_t.strip(" -")
        
        # Method 4: h1 fallback
        if not title:
            h1_match = re.search(r'<h1>(.*?)</h1>', detail_html, re.IGNORECASE)
            if h1_match:
                raw_title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
                clean_t = re.sub(f"^{re.escape(code)}", "", raw_title, flags=re.IGNORECASE)
                title = clean_t.strip(" -")
        
        if title:
            # Remove duplicate suffixes/names (handles Japanese names without spaces)
            def remove_duplicates(text):
                # Method 1: Check if last two space-separated words are identical
                parts = text.split()
                if len(parts) >= 2 and parts[-1] == parts[-2]:
                    text = ' '.join(parts[:-1])
                
                # Method 2: Check for trailing duplicate substrings (Japanese names)
                # e.g., "菊乃らん菊乃らん" -> "菊乃らん"
                for length in range(2, min(20, len(text) // 2 + 1)):
                    suffix = text[-length:]
                    if text[-2*length:-length] == suffix:
                        text = text[:-length]
                        break
                
                # Method 3: Remove trailing romanized names (JavTrailers adds these)
                # e.g., "つぼみの体内に...Tsubomi" -> "つぼみの体内に..."
                # Pattern: Title ends with capitalized English word(s) not preceded by space
                trailing_romaji = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$', text)
                if trailing_romaji:
                    romaji_name = trailing_romaji.group(1)
                    # Check if it's attached directly to Japanese text (no space before)
                    pos = text.rfind(romaji_name)
                    if pos > 0 and text[pos-1] not in ' \t':
                        # Remove the trailing romaji
                        text = text[:pos].strip()
                
                return text
            
            title = remove_duplicates(title)
        
        # Extract Cover: og:image
        cover_url = None
        og_img_match = re.search(r'<meta property="og:image" content="([^"]+)"', detail_html, re.IGNORECASE)
        if og_img_match:
            cover_url = og_img_match.group(1)
        
        return title, cover_url
        
    except Exception as e:
        print(f"  [JavTrailers] Error: {e}")
        return None, None

def has_cover(video_path):
    if MP4 is None: return False
    try:
        video = MP4(video_path)
        has = "covr" in video
        del video
        return has
    except: return False

def process_directory(directory, dry_run=True, target_file=None, progress_callback=None, custom_cover_dir=None):
    if progress_callback: progress_callback(0, 0, "Scanning directory...")
    print(f"Scanning directory: {directory}")
    print(f"Mode: {'DRY RUN (No changes)' if dry_run else 'LIVE (Renaming files)'}")
    if target_file: print(f"Target: Single file '{target_file}'")
    
    # Setup Cover Directory once
    script_dir = os.path.dirname(os.path.abspath(__file__))
    label_dir = os.path.dirname(script_dir)  # Parent of rename/
    # If custom dir provided, use that. Else default to label/cover.
    cover_dir = custom_cover_dir if custom_cover_dir else os.path.join(label_dir, "cover")
    print(f"Cover Output Directory: {cover_dir}")
    print("-" * 50)
    
    try:
        files = sorted(os.listdir(directory))
        for i, filename in enumerate(files):
            if target_file and filename != target_file: continue
            if not filename.lower().endswith(".mp4"): continue
            
            # Progress: Start of file (Analyze) - 10%
            if progress_callback: progress_callback(i, 10, f"Analyzing: {filename}")
            print(f"\nAnalyzing: {filename}")
            
            clean_name = re.sub(r'^[^@]+@', '', filename)
            
            # Check for FC2
            is_fc2 = False
            fc2_match = re.search(r'(FC2(?:PPV)?)-?(\d+)', clean_name, re.IGNORECASE)
            if fc2_match:
                is_fc2 = True
                code_prefix = fc2_match.group(1).upper()
                if code_prefix == "FC2": code_prefix = "FC2-PPV"
                code_num = fc2_match.group(2)
                code = f"{code_prefix}-{code_num}"
                print(f"  Identified FC2: {code}")

            # 1. Extraction Logic
            if not is_fc2:
                # Pattern: LETTERS + DASH + DIGITS or LETTERS + PADDED_DIGITS
                # Examples: ABW-009, IPTD-764, iptd00764, WANZ00684
                
                # First try: standard format with hyphen (ABW-009)
                match = re.search(r'^([A-Z]+)-(\d+)', clean_name, re.IGNORECASE)
                if match:
                    code = f"{match.group(1).upper()}-{match.group(2)}"
                else:
                    # Second try: no hyphen format (iptd00764, WANZ00684)
                    # Convert to standard: LETTERS-DIGITS
                    match = re.search(r'^([A-Z]+)(\d+)', clean_name, re.IGNORECASE)
                    if not match:
                        print(f"  Skipping: Could not extract code from {filename}")
                        continue
                    prefix = match.group(1).upper()
                    num_str = match.group(2)
                    num_int = int(num_str)
                    
                    # DV uses 4 digits, most others use 3 digits
                    if prefix == "DV":
                        code = f"{prefix}-{num_int:04d}"
                    else:
                        code = f"{prefix}-{num_int:03d}"
                print(f"  Code: {code}")
            
            # 1.5. Corruption Check
            file_path = os.path.join(directory, filename)
            is_corrupted, error_msg = check_file_structure(file_path)
            if is_corrupted:
                print(f"  [WARNING] {error_msg}")
                success, repaired_path = repair_with_ffmpeg(file_path)
                if success: file_path = repaired_path
                else: continue
            
            # 2. Check Labeled
            already_labeled = bool(re.search(r'[\u3040-\u30ff]', filename))
            if already_labeled:
                if has_cover(file_path):
                    print(f"  [INFO] File has Japanese title AND cover art. Skipping.")
                    if not target_file: continue
                else:
                    print(f"  [INFO] File has title but NO cover. Proceeding to fetch...")

            # 3. Handle Suffixes
            name_without_ext = os.path.splitext(filename)[0]
            rest = name_without_ext[len(code):]
            rest_upper_raw = rest.upper()
            has_restored = bool(re.search(r'\.?RESTOR(ED?)?($|[^A-Z])', rest_upper_raw))
            rest = re.sub(r'-\d{2}\.\d{2}\.\d{2}\.\d{3}-\d{2}\.\d{2}\.\d{2}\.\d{3}', '', rest)
            rest = re.sub(r'-cut-merged-\d+', '', rest)
            rest = re.sub(r'\.restored.*', '', rest, flags=re.IGNORECASE)
            
            suffix = ""
            rest_upper = rest.upper()
            if has_restored and "无码" not in rest_upper: suffix = " 无码-lada"
            elif "无码-LADA-C" in rest_upper: suffix = " 无码-lada-C"
            elif "-C 无码-LADA" in rest_upper or "-C无码-LADA" in rest_upper: suffix = "-C 无码-lada"
            elif "无码-LADA" in rest_upper: suffix = " 无码-lada"
            elif rest_upper.endswith('-UC'): suffix = " 无码-lada-C"
            elif rest_upper.endswith('-U'): suffix = " 无码-lada"
            elif rest_upper.endswith('-C'): suffix = "-C" 
            else:
                suffix_match = re.search(r'(-[0-9A-Z]+)$', rest, re.IGNORECASE)
                if suffix_match: suffix = suffix_match.group(1).upper()

            print(f"  Code: {code}")

            # 4. Fetch Title & Cover
            if progress_callback: progress_callback(i, 50, "Fetching metadata...")
            if is_fc2:
                # FC2 Scraping
                try:
                    from fc2_scraper import get_fc2_metadata
                    print(f"  [FC2] Scraping metadata for {code_num}...")
                    jp_title, cover_url = get_fc2_metadata(code_num)
                    if not jp_title:
                        print("  [FC2] Web scraping failed.")
                        # Fallback
                        temp_name = clean_name
                        temp_name = re.sub(r'FC2(?:PPV)?-?\d+', '', temp_name, flags=re.IGNORECASE)
                        temp_name = re.sub(r'-[A-Z0-9]+(\.mp4)', r'\1', temp_name, flags=re.IGNORECASE)
                        temp_name = os.path.splitext(temp_name)[0].strip()
                        if len(temp_name) > 5:
                            jp_title = temp_name
                            print(f"  [FC2] Fallback: Extracted title from filename: {jp_title}")
                except Exception as e:
                    print(f"  [FC2] Error: {e}")
                    jp_title, cover_url = None, None
            else:
                # JavTrailers Scraping via Cloudscraper
                jp_title, cover_url = get_metadata_via_jt_cloudscraper(code)
            
            if not jp_title:
                 print("  FAILED to fetch title. Skipping.")
                 continue
                 
            print(f"  Fetched Title: {jp_title}")
            if cover_url: print(f"  Fetched Cover URL: {cover_url}")
            else: print("  [WARN] No cover URL found.")

            # 5. Construct New Name
            new_filename = f"{code} {jp_title}{suffix}.mp4"
            new_filename = clean_filename(new_filename)
            
            if progress_callback: progress_callback(i, 70, "Renaming...")
            
            do_rename = True
            if new_filename == filename:
                print("  [SKIP] New filename is identical to old.")
                do_rename = False
            elif jp_title in filename and not target_file:
                 print("  [SKIP] Filename already contains title.")
                 do_rename = False
            
            if do_rename:
                print(f"  [RENAME] '{filename}'\n        -> '{new_filename}'")
            
            if not dry_run:
                final_path = os.path.join(directory, filename)
                if do_rename:
                    try:
                        old_path = os.path.join(directory, filename)
                        new_path = os.path.join(directory, new_filename)
                        os.rename(old_path, new_path)
                        print("    Success Rename.")
                        final_path = new_path
                    except OSError as e:
                        print(f"    Error renaming: {e}")
                        final_path = old_path

                # PROCESS & EMBED COVER
                if cover_url:
                    if progress_callback: progress_callback(i, 90, "Downloading & Embedding Cover...")
                    try:
                        print(f"    [Cover] Downloading: {cover_url}")
                        c_scraper = cloudscraper.create_scraper() # reuse scraper
                        resp = c_scraper.get(cover_url, timeout=15)
                        resp.raise_for_status()
                        raw_data = resp.content
                        
                        clean_cover_name = clean_filename(f"{code} {jp_title}")
                        clean_cover_name = clean_filename(f"{code} {jp_title}")
                        
                        # Use cover_dir calculated at start of function
                        os.makedirs(cover_dir, exist_ok=True)
                        cover_save_path = os.path.join(cover_dir, f"{clean_cover_name}.jpg")
                        
                        processed_data = process_and_save_cover(raw_data, cover_save_path)
                        print(f"    [Cover] Saved to: {os.path.basename(cover_save_path)}")
                        embed_cover(final_path, processed_data)
                        
                    except Exception as e:
                         print(f"    [Cover] Error handling cover: {e}")
            
            if progress_callback: progress_callback(i, 100, "Done.")

    except Exception as e:
        print(f"Unhandled error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rename MP4 files and embed cover art (Using Cloudscraper/JavTrailers).")
    # Use relative path for cross-platform compatibility
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_dir = os.path.dirname(script_dir)  # Parent of rename/ = label/
    parser.add_argument("--dir", default=default_dir, help="Directory to scan")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no changes)")
    parser.add_argument("--target", help="Process specific file only")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation for live mode")
    args = parser.parse_args()
    
    if not args.dry_run and not args.yes:
        print("WARNING: You are running in LIVE mode. Files will be renamed.")
    
    process_directory(args.dir, dry_run=args.dry_run, target_file=args.target)
