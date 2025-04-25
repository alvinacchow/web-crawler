import re
from urllib.parse import *
from bs4 import BeautifulSoup
from collections import Counter

skipped_words = [".css", ".js", ".bmp", ".gif", ".jpg", ".jpeg", ".ico",
    ".png", ".tif", ".tiff", ".mid", ".mp2", ".mp3", ".mp4",
    ".wav", ".avi", ".mov", ".mpeg", ".ram", ".m4v", ".mkv", ".ogg", ".ogv", ".pdf",
    ".ps", ".eps", ".tex", ".ppt", ".pptx", ".doc", ".docx", ".xls", ".xlsx",
    ".names", ".data", ".dat", ".exe", ".bz2", ".tar", ".msi", ".bin", ".7z",
    ".psd", ".dmg", ".iso", ".epub", ".dll", ".cnf", ".tgz", ".sha1", ".thmx",
    ".mso", ".arff", ".rtf", ".jar", ".csv", ".rm", ".smil", ".wmv", ".swf",
    ".wma", ".zip", ".rar", ".gz"]

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):

    links = []
    try:
        if resp.status != 200 or resp.raw_response is None:
            return links
        
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        for x in soup.find_all('a', href=True):
            href = x['href']
            newurl = urljoin(url, href)
            finalurl, _ = urldefrag(newurl)
            links.append(finalurl)
    except Exception as e:
        print(f"Error extracting links: {e}")
    
    return links

    

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        
        #check if the domain is uci.edu or uci.edu, check if it's ics, cs, informatics, or stat
        # and check if the path does not end with any of the skipped words
        if not re.match(r".*\.(ics|cs|informatics|stat)\.uci\.edu.*", parsed.netloc):
            return False
        
        if any(parsed.path.lower().endswith(extension) for extension in skipped_words):
            return False
        return True

    except TypeError:
        print ("TypeError for URL", parsed)
        return False

def crawl_pages_checker(url, resp):
    """
    Check if the page is a valid page to crawl. Call it in the scraper? This is based on the behavior 
    requirements on the instruction page on canvas
    """
    if trap_detected(url):
        pass

    if bad_url(resp):
        pass
    
    if high_info_content(resp):
        pass

    if similar_no_info(url, resp.raw_response):
        pass