# These functions are used to scrape all the relevant data from the American
# Presidency Project

import requests
from bs4 import BeautifulSoup as bs
import html
import json
from time import sleep
import logging as log



LOG_FILE = "american_presidency_project.log"
BASE_URL = "https://www.presidency.ucsb.edu"
URL_LIST_QUERY = "/documents/app-categories/presidential/interviews?page="
REQ_DELAY = 0.2
HEADERS = {"User-agent": "rdata"}
INTERVIEW_LINKS_CSV_FILE = "american_presidency_project_interview_links.csv"

log.basicConfig(filename=LOG_FILE, encoding="utf-8", level=log.DEBUG)



def clean_html_text(string):
    """ Remove special characters from html text """

    clean_text = string.replace(u'\xa0', u' ').replace(u'\n', u' ')
    return clean_text


def is_search_done(soup):
    """ Determine whether or not list of articles is exhausted """

    search_done = not soup.find("div", class_="view-empty") is None
    return search_done


def get_interview_links_from_page(soup):
    """ Get list of links from given list page """

    log.debug("Retrieving links from page...")

    list_soup = soup.find_all("div", class_="views-row")
    links = []
        
    for row in list_soup:
        title = row.find("div", class_="field-title")
        link = BASE_URL + title.find("a")['href']
        links.append(link)

    log.debug("Retrieved links from page", links)

    return links


def get_all_interview_links():
    """ Returns all interview links """

    log.debug("Retrieving all interview links...")

    page_number = 0
    done_searching = False # Flag for all pages retrieved
    links = [] # List of links to articles

    while not done_searching:
        log.debug("Getting new page...")
        try:
            # Get page soup
            res = requests.get(BASE_URL 
                    + URL_LIST_QUERY 
                    + str(page_number), headers=HEADERS)
            if not res.status_code == 200:
                raise Exception(res.status_code)
            soup = bs(res.text, "html")

            # Check if results are empty (all pages searched)
            if is_search_done(soup):
                log.debug("All link list pages exhausted.")
                done_searching = True

            links += get_interview_links_from_page(soup)
            page_number += 1
            sleep(REQ_DELAY)
        
        except Exception as e:
            log.error(e)
        
    return links


def store_interview_links():
    """ Store interview links in csv file """

    links = get_all_interview_links()

    log.debug("Storing interview links in csv file...")
    with open(INTERVIEW_LINKS_CSV_FILE, "w") as file:
        for link in links:
            file.write(link + ",")


def get_interview_data(link):
    """ Get article data from interview link """

    log.debug("Getting interview data from", link)

    res = requests.get(url=link, headers=HEADERS)
    if res.status_code == 200:
        interview_html = res.text
    else: 
        raise Exception(res.status_code)

    # Find the article
    soup = bs(interview_html, "html")
    entry_content = soup.find("div", class_="entry-content")
    if entry_content is None:
        entry_content = soup.find("div", class_="field-docs-content")
        
    entry_paragraphs = entry_content.find_all("p", recursive=False)

    # Create list of statements
    statements = []
    last_speaker = ""
    speaker = ""
    for p in entry_paragraphs:
        try: 
            if p is not None:
                # Determine speaker
                speaker_tag = p.find("b")
                if speaker_tag is None:
                    speaker_tag = p.find("i")
                    if speaker_tag is None:
                        speaker = last_speaker
                else:
                    speaker = clean_html_text(speaker_tag.text)

                # Get statement text
                if p.text:
                    statement = []
                    if len(p.text.split(": ")) >= 2:
                        statement = [speaker, clean_html_text(
                                p.text.split(": ")[1])]
                    else:
                        statement = [speaker, clean_html_text(p.text)]
                    statements.append(statement)

                last_speaker = speaker

        except Exception as e:
            log.error(e)

    return statements


def get_all_interview_data():
    """ 
    Get all interview data from American Presidency Project. This will take 
    some time. This function references the csv file, doesn't check the website 
    for updated list.
    """

    # Retrieve links from 





