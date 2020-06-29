import requests

import keyboard
from pykakasi import kakasi, wakati
from ssl import SSLWantReadError
from bs4 import BeautifulSoup

REQUEST_SESSION = requests.session()
KAKASI = kakasi()
KAKASI.setMode("J", "H")
KAKASI_CONVERTER = KAKASI.getConverter()
WAKATI = wakati()
WAKATI_CONVERTER = WAKATI.getConverter()


def initial_search(search_term):
    search_term = 'https://www.tanoshiijapanese.com/dictionary/index.cfm?j=' + search_term
    print(search_term)
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
        for i in entries:
            term = i.find("div", class_="jp").text
            definition = i.find("div", class_="en").find("ol").text
            entry_link = i.find("div", class_="entrylinks").find("a", text='Entry Details »')['href'].replace("../", "https://www.tanoshiijapanese.com/")
            entries_list.append([term, definition, entry_link])
        result_soup = BeautifulSoup(choose_search_term(entries_list).text, "html.parser")
        if not result_soup:
            return
    filtered_soup = result_soup.find("div", id="cncontentbody")
    kanji = filtered_soup.find("div", class_="jp").text
    kana = filtered_soup.find("div", class_="furigana").text
    romaji = filtered_soup.find("div", class_="romaji hide").text
    term_definition = filtered_soup.find("div", class_="en").find("ol").text
    print(kanji, kana, romaji)
    example_sentences = filtered_soup.find("div", id="idSampleSentences").find_all("div", class_="sm")
    example_sentence_list = []
    for i in example_sentences:
        jap = i.find("div", class_="jp").text
        english = i.find("div", class_="en").text
        example_sentence_list.append([jap, english])
    example_sentence = choose_example_sentence(example_sentence_list)
    example_jap = example_sentence[0]
    example_eng = example_sentence[1]
    example_jap_kana = KAKASI_CONVERTER.do(example_jap)
    example_jap_kana_token = WAKATI_CONVERTER.do(example_jap_kana)
    print(kanji, kana, romaji, term_definition, example_jap, example_eng, example_jap_kana_token)


def choose_search_term(terms):
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


def main_loop():
    response = input("Enter a search term")
    initial_search(response)
    main_loop()


main_loop()
