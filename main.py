import re
import sys
from ssl import SSLWantReadError

import requests
import keyboard
from pykakasi import kakasi, wakati
from bs4 import BeautifulSoup

REQUEST_SESSION = requests.session()
KAKASI = kakasi()
KAKASI.setMode("J", "H")
KAKASI_CONVERTER = KAKASI.getConverter()
WAKATI = wakati()
WAKATI_CONVERTER = WAKATI.getConverter()


def get_relevant_data(result_page):
    """Grabs the relevant information from the term's dictionary page and passes it to the hotkey
     function to be pasted into Anki."""
    kanji = result_page.find("div", class_="jp").text.replace("·", "")
    kanji = re.sub("(\(.{1,3}\))", "", kanji)
    try:
        kana = result_page.find(
            "div", class_="furigana").text.replace("[", "").replace("]", "").replace("·", "")
        kana = re.sub("(\(.{1,3}\))", "", kana)
    except AttributeError:
        kana = kanji
    romaji = result_page.find("div", class_="romaji hide").text
    term_definition = result_page.find("div", class_="en").find("ol").text.rstrip().lstrip()
    try:
        example_sentences = result_page.find(
            "div", id="idSampleSentences").find_all("div", class_="sm")
    except AttributeError:
        print("No example sentences available.")
        prepare_info_hotkey([kanji, kana, romaji, term_definition])
    else:
        example_sentence_list = []
        for i in example_sentences:
            jap = i.find("div", class_="jp").text
            eng = i.find("div", class_="en").text
            example_sentence_list.append([jap, eng])
        example_sentence = choose_example_sentence(example_sentence_list)
        example_jap = example_sentence[0]
        example_eng = example_sentence[1]
        example_jap_token = WAKATI_CONVERTER.do(example_jap)
        example_jap_kana = KAKASI_CONVERTER.do(example_jap_token)
        prepare_info_hotkey(
            [kanji, kana, romaji, term_definition, example_jap, example_eng, example_jap_kana])


def initial_search(search_term):
    """Given a search term or a tanoshiijapense.com search entry link scrape the data from the web
     page, asking the user to choose the correct term if there are multiple results. Scraped info is
     passed to a function that pulls the desired data from the page."""
    if "tanoshii" not in search_term:
        search_term = 'https://www.tanoshiijapanese.com/dictionary/index.cfm?j=' + search_term
    try:
        result = REQUEST_SESSION.get(search_term, timeout=5)
    except requests.exceptions.Timeout:
        print('Timeout')
        return False
    except requests.exceptions.ConnectionError:
        print('ConnectionError')
        return False
    except SSLWantReadError:
        print('SSLWantReadError')
        return False
    result_soup = BeautifulSoup(result.text, "html.parser")
    page_header = result_soup.find("div", id="cnheader").find("h1").text
    if "Search Results" in page_header:
        entries_list = []
        entries = result_soup.find_all("div", class_="message")
        if len(entries) == 0:
            print('Your query returned no results.')
            return False
        for i in entries:
            term = i.find("div", class_="jp").text
            definition = i.find("div", class_="en").find("ol").text
            entry_link = i.find(
                "div", class_="entrylinks").find(
                "a", text='Entry Details »')['href'].replace(
                "../", "https://www.tanoshiijapanese.com/")
            entries_list.append([term, definition, entry_link])
        result_soup = BeautifulSoup(choose_search_term(entries_list).text, "html.parser")
        if not result_soup:
            return False
    filtered_soup = result_soup.find("div", id="cncontentbody")
    get_relevant_data(filtered_soup)


def choose_search_term(terms):
    """Prints the available term options and asks the user to choose which one to proceed with.
     Returns the chosen data."""
    print("Which term do you want?\n\n")
    for count, i in enumerate(terms):
        print(str(count + 1) + ": " + i[0] + "\n" + i[1])
    response = input("Choose a term")
    try:
        response = int(response)
    except ValueError:
        print("Please enter a valid entry number")
        return choose_search_term(terms)
    if response <= 0 or response > len(terms):
        print("Please enter a valid entry number")
        return choose_search_term(terms)
    try:
        result = REQUEST_SESSION.get(terms[int(response) - 1][2], timeout=5)
    except requests.exceptions.Timeout:
        print('Timeout')
        return False
    except requests.exceptions.ConnectionError:
        print('ConnectionError')
        return False
    except SSLWantReadError:
        print('SSLWantReadError')
        return False
    return result


def choose_example_sentence(example_sentences):
    """Prints the available example sentences and asks the user to choose which one to proceed with.
     Returns the chosen data."""
    print("Choose an example sentence: \n\n")
    for count, i in enumerate(example_sentences):
        print(str(count + 1) + ': ' + i[0] + "\n" + i[1] + "\n")
    response = input("Which sentence do you want?")
    try:
        response = int(response)
    except ValueError:
        print("Please enter a valid entry number")
        return choose_search_term(example_sentences)
    if response <= 0 or response > len(example_sentences):
        print("Please enter a valid entry number")
        return choose_search_term(example_sentences)
    return example_sentences[response - 1]


def prepare_info_hotkey(info):
    """Given a list of information pulled from the search term web page set the information to be
     pasted into Anki one piece at a time at the press of the specified hotkey."""

    def write_info(entry):
        keyboard.write(entry)
        keyboard.press_and_release('tab')

    for i in info:
        print("Press f1 to paste: " + i)
        keyboard.add_hotkey('f1', lambda: write_info(i))
        keyboard.wait('f1')
        keyboard.unregister_all_hotkeys()
    print("Finished!")


def main_loop():
    """Funtion to run on startup that asks the user to provide a search term.
     Loops on completion."""
    response = input("Enter a search term")
    if response.lower() in ['exit', 'quit']:
        print("Closing Program.")
        sys.exit()
    initial_search(response)
    main_loop()


main_loop()
