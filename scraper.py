import hashlib
import re
from urllib.parse import *
from bs4 import BeautifulSoup
from collections import Counter
from collections import defaultdict



skipped_words = [".css", ".js", ".bmp", ".gif", ".jpg", ".jpeg", ".ico",
    ".png", ".tif", ".tiff", ".mid", ".mp2", ".mp3", ".mp4",
    ".wav", ".avi", ".mov", ".mpeg", ".ram", ".m4v", ".mkv", ".ogg", ".ogv", ".pdf",
    ".ps", ".eps", ".tex", ".ppt", ".pptx", ".doc", ".docx", ".xls", ".xlsx",
    ".names", ".data", ".dat", ".exe", ".bz2", ".tar", ".msi", ".bin", ".7z",
    ".psd", ".dmg", ".iso", ".epub", ".dll", ".cnf", ".tgz", ".sha1", ".thmx",
    ".mso", ".arff", ".rtf", ".jar", ".csv", ".rm", ".smil", ".wmv", ".swf",
    ".wma", ".zip", ".rar", ".gz"]

list_of_stopwords = ["a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any",
    "are", "aren't", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", "did",
    "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few",
    "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't",
    "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if",
    "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more",
    "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
    "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while",
    "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"]

common_words_counter = Counter()
list_unique_pages = []
longest_page = ("", 0)

# TRAP DETECTION GLOBALS 
content_hashes = set()               
urls_per_path_segment = defaultdict(int) 
path_patterns = defaultdict(int) 
domain_visit_count = defaultdict(int)
path_visit_count = defaultdict(int)   
visited_params = defaultdict(set)   
domain_last_accessed = {}      

# TRAP DETECTION CONSTANTS
MAX_URL_LENGTH = 200             
MAX_PATH_SEGMENTS = 8           
MAX_QUERY_PARAMS = 5             
MAX_URLS_PER_PATH_SEGMENT = 50 
MAX_PATTERN_COUNT = 10
MAX_DOMAIN_VISITS = 1000 
CALENDAR_PATTERN = re.compile(r'/(202\d|19\d\d)/(0?[1-9]|1[0-2])/(0?[1-9]|[12][0-9]|3[01])')
PAGINATION_PATTERN = re.compile(r'page=\d+|p=\d+|pg=\d+|start=\d+|offset=\d+')
SESSION_PATTERN = re.compile(r'session(id)?=|sid=|s=\w{32}')
TRAP_PATHS = re.compile(r'/(calendar|login|logout|comment|search|print|share|tag|rss|feed|cgi-bin)/')


def scraper(url, resp):
    global longest_page
    if not high_info_content(resp) or dead_url(resp):
        return []
    
    if resp.status == 200 or resp.raw_response:
        most_common_wordsearch(resp.raw_response.content)
        longest_page = update_longest_page(url, resp.raw_response.content, longest_page)

        if is_duplicate_content(resp.raw_response.content):
            return []
    else: 
        return []
    
    links = extract_next_links(url, resp)
    check_unique_pages(url)
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
        
        if is_trap(url, parsed): 
            return False
        
        return True

    except TypeError:
        print ("TypeError for URL", parsed)
        return False
    
def is_trap(url, parsed) -> bool:
    # Check URL length
    if len(url) > MAX_URL_LENGTH:
        # print("trap 1")
        return True
    
    # Check domain visit count
    domain = parsed.netloc.lower()
    if domain_visit_count[domain] > MAX_DOMAIN_VISITS:
        # print("trap 2")
        return True
    
    # Check path segments
    path = parsed.path
    path_segments = [s for s in path.split('/') if s]
    # Check for excessive path depth
    if len(path_segments) > MAX_PATH_SEGMENTS:
        # print("trap 3")
        return True
    
    # Check for calendar patterns
    if CALENDAR_PATTERN.search(path):
        # print("trap 4")
        return True
    
    # Check for known problematic paths
    if TRAP_PATHS.search(path):
        # print("trap 5")
        return True
    
    # Check for session IDs 
    if SESSION_PATTERN.search(url):
        # print("trap 6")
        return True
    
    # Check query parameters
    if parsed.query:
        query_params = parsed.query.split('&')
        
        # Too many query parameters
        if len(query_params) > MAX_QUERY_PARAMS:
            # print("trap 7")
            return True
    
    # Check for repeated path patterns
    if path_segments:
        # Create a simplified pattern from the path
        path_pattern = '-'.join([p.split('-')[0] if '-' in p else p for p in path_segments])
        
        if path_pattern:
            path_patterns[path_pattern] += 1
            if path_patterns[path_pattern] > MAX_PATTERN_COUNT:
                # print("trap 8")
                return True
    
    # Check for too many URLs with same segment count
    segment_count = len(path_segments)
    if segment_count > 2: 
        urls_per_path_segment[segment_count] += 1
        if urls_per_path_segment[segment_count] > MAX_URLS_PER_PATH_SEGMENT:
            # print("trap 9")
            return True
    
    # Check specific path count
    path_key = '/'.join(path_segments)
    if path_key:
        path_visit_count[path_key] += 1
        if path_visit_count[path_key] > 5: 
            # print("trap 10")
            return True
    
    return False

def is_duplicate_content(content):
    try:
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text()
    
        content_hash = hashlib.md5(text_content.encode('utf-8')).hexdigest()
        
        if content_hash in content_hashes:
            return True
        
        content_hashes.add(content_hash)
        return False
    
    except Exception as e:
        print(f"Error checking duplicate content: {e}")
        return False


# THIS SECTION IS FOR THE TOP 50 WORDS
def most_common_wordsearch(html_content):
    word_counts = get_common_words(html_content)
    common_words_counter.update(word_counts)

def get_common_words(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    words = re.findall(r'\b\w+\b', text.lower())
    filtered_words = [word for word in words if word not in list_of_stopwords and len(word) > 2 and word.isalpha() and not word.isdigit()]
    return Counter(filtered_words)

def print_common_words():
    with open('common_words.txt', 'w') as f:
        for word, count in common_words_counter.most_common(50):
            f.write(f"{word}: {count}\n")

# THIS SECTION IS FOR LONGEST PAGE
def update_longest_page(url, html_content, current):
    """
    Check if the page is the longest page. Call it in the scraper? This is based on the behavior 
    requirements on the instruction page on canvas
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    words = re.findall(r'\b\w+\b', text.lower())
    filtered_words = [word for word in words if word not in list_of_stopwords and len(word) > 2 and word.isalpha() and not word.isdigit()]
    word_count = len(filtered_words)
    
    if word_count > current[1]: 
        return (url, word_count)
    return current

def print_longest_page(longest_page):
    with open('longest.txt', 'w') as f: 
        f.write(f"{longest_page[0]}, {longest_page[1]}\n") 
        return (f"{longest_page[0]}, {longest_page[1]}\n")


# COUNTING NUMBER OF UNIQUE PAGES 
def check_unique_pages(url):
    # removes the fragment part of url
    link = discard_fragment(url) 

    # if its not in our list, add to our list
    if link not in list_unique_pages:
        list_unique_pages.append(link)

def discard_fragment(url):
    pound_sign = url.find('#')
    if pound_sign != -1:
        return url[:pound_sign]
    return url

def return_num_unique_pages(list_of_pages):
    f.write(f"{uniquePages}, {len(list_of_pages)}\n") 
    return len(list_of_pages)
# COUNTING NUMBER OF UNIQUE PAGES 


# UCI.EDU DOMAIN
def count_pages_per_subdomain(list_of_pages):
    subdomain_counter = defaultdict(int)

    for url in list_of_pages:
        parsed = urlparse(url)
        subdomain = parsed.netloc.lower()  # get the subdomain 
        
        # make sure to only include subdomains under uci.edu
        if subdomain.endswith(".uci.edu"): 
            subdomain_counter[subdomain] += 1
    return subdomain_counter

def print_subdomains(subdomain_counter):
    with open('subdomains.txt', 'w') as f:
        for subdomain in sorted(subdomain_counter.keys()):
            # writes into file ( we can get rid of this if its unnecessary LOL)
            f.write(f"{subdomain}, {subdomain_counter[subdomain]}\n") 
            print(f"{subdomain}, {subdomain_counter[subdomain]}")  # also print to console
# UCI.EDU DOMAIN

def dead_url(resp):
    if resp.status == 200:
        if resp.raw_response:

            #if theres nothing in the content, this is DEAD
            if len(resp.raw_response.content) == 0:
                return True
        else:
            return True
    return False 

def count_words_all(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    words = re.findall(r'\b\w+\b', text.lower())
    return len(words)

def high_info_content(resp):
    if not resp.raw_response:
        return False
    
    wordcount = count_words_all(resp.raw_response.content)
    return wordcount >= 100


# CALL WHEN TESTING FUNCTIONS (AFTER DONE CRAWLING)
'''
return_num_unique_pages(list_unique_pages)

subdomain_count = count_pages_per_subdomain(list_unique_pages)
print_subdomains(subdomain_count)


'''