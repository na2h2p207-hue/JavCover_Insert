import requests
import re
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = 'https://adult.contents.fc2.com'

def get_fc2_metadata(fc2_id):
    """
    Scrape metadata for a given FC2 ID (Regex version).
    
    Args:
        fc2_id (str): The numeric FC2 ID (e.g., "3482842")
        
    Returns:
        tuple: (title, cover_url) or (None, None) if failed
    """
    try:
        url = f'{BASE_URL}/article/{fc2_id}/'
        logger.info(f"Scraping FC2: {url}")
        
        # Proper Headers and Cookie for Age Verification
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8',
            'Referer': 'https://adult.contents.fc2.com/',
        }
        
        # Cookie to bypass age check
        cookies = {
            'age_check_done': '1'
        }
        
        resp = requests.get(url, headers=headers, cookies=cookies, timeout=15)
        html_content = resp.text
        
        # Check for region block / login redirect
        if '/id.fc2.com/' in resp.url:
            logger.error("FC2 Region Block: Redirected to login page. Cannot scrape.")
            return None, None
            
        if resp.status_code != 200:
            logger.error(f"FC2 Scrape Error: Status {resp.status_code}")
            return None, None

        # 1. Extract Title
        title = None
        # Pattern: <div class="items_article_headerInfo"><h3>Title</h3> or just <h3>Title</h3>
        title_match = re.search(r'<div class="items_article_headerInfo">\s*<h3>(.*?)</h3>', html_content, re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()
        else:
            # Fallback generic h3
            title_match_2 = re.search(r'<h3>(.*?)</h3>', html_content, re.DOTALL)
            if title_match_2:
                title = title_match_2.group(1).strip()
        
        if title:
            title = re.sub(r'<[^>]+>', '', title).strip()
            
            # Check for "Not Found" titles
            invalid_titles = [
                "The product you were looking for was not found",
                "申し訳ありません、お探しの商品が見つかりませんでした",
                "Specified product was not found",
                "商品が見つかりませんでした"
            ]
            for invalid in invalid_titles:
                if invalid in title:
                    logger.warning(f"FC2 'Not Found' page detected. Title: {title}")
                    return None, None

        # 2. Extract Cover
        cover_url = None
        
        # Look for the sample images block (high res)
        sample_block_match = re.search(r'data-feed="sample-images"(.*?)</ul>', html_content, re.DOTALL)
        if sample_block_match:
            sample_block = sample_block_match.group(1)
            # Find first href
            href_match = re.search(r'href="([^"]+)"', sample_block)
            if href_match:
                cover_url = href_match.group(1)
        
        # Fallback to thumbnail
        if not cover_url:
            thumb_match = re.search(r'class="items_article_MainitemThumb".*?src="([^"]+)"', html_content, re.DOTALL)
            if thumb_match:
                cover_url = thumb_match.group(1)
        
        # Fix relative URLs
        if cover_url and cover_url.startswith('//'):
            cover_url = 'https:' + cover_url

        return title, cover_url

    except Exception as e:
        logger.error(f"FC2 Scrape Exception: {e}")
        return None, None

if __name__ == "__main__":
    # Test
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    test_id = "3482842"
    print(f"Testing ID: {test_id}")
    t, c = get_fc2_metadata(test_id)
    print(f"Title: {t}")
    print(f"Cover: {c}")
