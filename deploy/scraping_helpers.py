import requests
from bs4 import BeautifulSoup



def load_page(url):
    """ Returns the response for the URL"""
    
    ### Load the first page:
    page = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}, timeout=5)

    return page

def get_next_page_href(page):
    """On a given webpage, finds and returns the URL for the 'next' page"""

    # Convert page to soup object
    soup = BeautifulSoup(page.content, "html.parser")

    # Find the URL for the next page
    # Find the <img> tag with the specified src attribute
    next_tag = soup.find('img', {'src': '/images/next.jpg'})

    if next_tag:
        # Find the parent <a> tag
        parent_a_tag = next_tag.find_parent('a')
        
        if parent_a_tag:
            # Get the href attribute of the parent <a> tag
            next_page_url = parent_a_tag.get('href')
        else:
            next_page_url = None
            print("Parent <a> tag not found.")
    else:
        next_page_url = None
        print("Image with the specified src attribute not found.")

    return next_page_url

def get_article_titles_and_hrefs(page, last_href):
    """ For a given page, returns all article hrefs as a list"""
    # Convert to soup object
    soup = BeautifulSoup(page.content, "html.parser")

    # Locate all the links and store them in the list 'hrefs'

    # Find all <span> elements with the class 'headline_avherald'
    spans = soup.find_all('span', {'class': 'headline_avherald'})

    # Print or process the found spans
    article_hrefs = []
    article_titles = []
    for span in spans:
        # Get the parent <a> tag
        parent_a_tag = span.find_parent('a')
        if parent_a_tag:
            # Get the href
            href = parent_a_tag.get('href')

            # Check if the href is the last_href
            if href == last_href:
                return article_titles, article_hrefs, 1

            article_hrefs.append(href)

        # Get the title
        article_title = span.get_text()
        article_titles.append(article_title)

    return article_titles, article_hrefs, 0



def get_new_titles_and_hrefs(url, last_href):
    # Create empty lists for titles and hrefs:
    article_titles = []
    article_hrefs = []

    # Load home page
    page = load_page(url)

    # Get next page URL
    next_page_href = get_next_page_href(page)

    # While next_page_URL:
    while next_page_href:
        
        page = load_page(url)

        titles, articles, end = get_article_titles_and_hrefs(page, last_href)
        article_titles += titles
        article_hrefs += articles
        if end == 1:
            break # Break out of the loop when the last available href is reached
        
        next_page_href = get_next_page_href(page)
        url = "https://avherald.com" + next_page_href

    return article_titles, article_hrefs # returns 2 separate lists
    


def get_article(page):
    """ For a given article page, returns the article text and the timestamp (including author)"""
    # Convert to soup object
    soup = BeautifulSoup(page.content, "html.parser")

    # Locate all the links and store them in the list 'hrefs'

    # Find the <span> element with the class 'sitetext'
    texts = soup.find_all('span', {'class': 'sitetext'})
    if len(texts) > 3:
        article_text = texts[3].get_text()
    else:
        article_text = "xxx"

    time_author = soup.find('span', {'class': 'time_avherald'})
    if time_author is not None:
        time_author = time_author.get_text()
    else:
        time_author = "yyy"

    return article_text, time_author

def get_comments(page):
    """ For a given article page, returns the title and the comments"""
        # Convert to soup object
    soup = BeautifulSoup(page.content, "html.parser")

    # Find the <span> element with the class 'headline_article', which is the article headline containing the event date
    headline = soup.find('span', {'class': 'headline_article'})
    if headline:
        headline_text = headline.get_text()
    else:
        headline_text = None

    # Finde comments and comment authors
    comment_authors = soup.find_all('span', {'class': 'time_avherald'})
    comments = soup.find_all('span', {'class': 'sitecomment'})

    comment_authors_texts = []
    comments_texts = []

    for comment_author in comment_authors[1:]: # The class 'time_avherald' is also used just below the headline, so we omit that one
        comment_authors_texts.append(comment_author.get_text())
    for comment in comments[:-1]:
        comments_texts.append(comment.get_text())

    return headline_text, comment_authors_texts, comments_texts
