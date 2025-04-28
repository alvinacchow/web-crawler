import re
from urllib.parse import *
from bs4 import BeautifulSoup
from collections import Counter


common_words_counter = Counter()

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

list_unique_pages = []

def scraper(url, resp):
    

    if resp.status == 200 or resp.raw_response:
        most_common_wordsearch(resp.raw_response.content)


    print(print_common_words)

    links = extract_next_links(url, resp)

    # checks if this is a unique page
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
        return True

    except TypeError:
        print ("TypeError for URL", parsed)
        return False


#ok now im not sure if we should do this lol but we can try it out?
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

# THIS SECTION IS FOR THE TOP 50 WORDS
def most_common_wordsearch(html_content):
    words_counts = common_words_counter(html_content)
    #i called the common_words_counter at the top
    common_words_counter.update(words_counts)

def common_words_counter(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    words = re.findall(r'\b\w+\b', text.lower())
    filtered_words = [word for word in words if word not in list_of_stopwords]
    return Counter(filtered_words).most_common(50)

def print_common_words(html_content):
    with open('common_words.txt', 'w') as f:
        common = common_words_counter(html_content)
        for word, count in common:
            f.write(f"{word}: {count}\n")

def longest_page(url, word_count):
    """
    Check if the page is the longest page. Call it in the scraper? This is based on the behavior 
    requirements on the instruction page on canvas
    """
    pass


# COUNTING NUMBER OF UNIQUE PAGES 
def check_unique_pages(url):
    # removes the fragment part of url
    link = discard_fragment(url) 

    # if its not in our list, add to our list
    if link not in list_unique_pages:
        list_unique_pages.append(link)

def discard_fragment(url):
    pound_sign = text.find('#')
    if index != -1:
        return url[:pound_sign]
    return url

def return_num_unique_pages(list_of_pages):
    return len(list_of_pages)
# COUNTING NUMBER OF UNIQUE PAGES 


# UCI.EDU DOMAIN
def count_pages_per_subdomain(list_of_pages):
    subdomain_counter = defaultdict(int)

    for url in pages:
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


# CALL WHEN TESTING FUNCTIONS (AFTER DONE CRAWLING)
'''
return_num_unique_pages(list_unique_pages)

subdomain_count = count_pages_per_subdomain(list_unique_pages)
print_subdomains(subdomain_count)


'''
