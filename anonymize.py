import pandas as pd
import numpy as np
import csv
import random
import re
import os
from datetime import date
import inflect

inflector = inflect.engine()

def generalized_callback(pattern, selector, entity_map,id):
    #wanted to write a generalized callback, 
    #but it interfered with entity updating
    pass


def adate(texts, entity_map, ids, modality):
    print("Anonymizing dates...")
    new_texts = []
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    ordinal_days = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth", "twentieth", "twenty first", "twenty second", "twenty third", "twenty fourth", "twenty fifth", "twenty sixth", "twenty seventh", "twenty eighth"]

    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])

        if modality == 'text':
            date = str(random.randrange(1,12)) + "/" + str(random.randrange(1,28))
        else:
            date = random.choice(months) + " " + random.choice(ordinal_days)

        r =  date if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
        
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[DATE-\d+\]",lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def address(texts, entity_map, ids, modality):
    print("Anonymizing addresses...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/street-names.csv')

    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        streets = df['Streets'].sample()
        street = streets.values[0]

        if modality == 'text':
            number = str(random.randrange(100,500))
        else:
            number = inflector.number_to_words(random.randrange(100,500))
        address = number + " " + street + " "
        r =  address if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[ADDRESS-\d+\]",lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def atime(texts, entity_map, ids, modality):
    print("Anonymizing time...")
    hours = ["one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve"]
    minutes = ["oh one","oh two","oh three","oh four","oh five","oh six","oh seven","oh nine","ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen"]
    new_texts = []
    
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        if modality == 'text':
            time = str(random.randrange(1,12)) + ":" + str(random.randrange(0,50)) + " " + str(random.choice(["AM","PM"]))
        else:
            time = str(random.choice(hours)) + " " + str(random.choice(minutes)) + " " + str(random.choice(["AM","PM"]))  
        r =  time if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
        
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[TIME-\d+\]",lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def cardinal(texts, entity_map, ids, modality):
    print("Anonymizing cardinals...")

    t_cardinal = ["0","1","2","3","4","5","6","7","8","9"]
    v_cardinal = ["zero","one","two","three","four","five","six","seven","eight","nine"]

    if modality == 'text':
        cardinal = t_cardinal
    else:
        cardinal = v_cardinal
    
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  random.choice(cardinal) if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r

    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[CARDINAL-\d+\]",lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def ccard(texts, entity_map, ids, modality):
    print("Anonymizing credit card numbers...")

    ccnumber = "";
    length = 16
    new_texts = []

    while len(ccnumber) <= (length - 1):
        digit = str(random.randrange(0,9))
        ccnumber += digit

    if modality == 'text':
        ccard = ccnumber
    else:
        ccard = digits2words(ccnumber)

    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  ccard if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[CARD_NUMBER-\d+\]", lambda x: callback(x,id) , text)
        new_texts.append(new_text)
    return new_texts, entity_map


def company(texts, entity_map, ids):
    print("Anonymizing names (organizations)...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/Top-100-Retailers.csv')

    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  df.sample().values[0][0].split()[0] if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[ORG-\d+\]", lambda x: callback(x,id) , text)
        new_texts.append(new_text)
    return new_texts, entity_map


def digits2words(digits):
    num2words = {'0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'}
    words = ''
    for digit in range(0, len(digits)): 
        words += " " + num2words[digits[digit]]
    return words


def event(texts, entity_map, ids):
    print("Anonymizing events...")
    events = ["seminar","conference","trade show","workshop","reunion","party","gala","picnic","meeting","lunch"]
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  random.choice(events) if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[EVENT-\d+\]",lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def fac(texts, entity_map, ids):
    print("Anonymizing facility names...")
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  "[]" if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text, id in zip(texts, ids):
        new_text = re.sub(r"\[FAC-\d+\]",lambda x: callback(x, id),text)
        new_texts.append(new_text)
    return new_texts, entity_map


def gpe(texts, entity_map, ids):
    print("Anonymizing country, city, state...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/gpe.csv')
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  df.sample().values[0][0].split()[0] if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[GPE+-\d+\]",lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def language(texts, entity_map, ids):
    print("Anonymizing language...")
    language = ["Chinese", "Spanish", "English", "Hindi", "Arabic", "Portuguese", "Russian", "German", "Korean", "French", "Turkish"]
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  random.choice(language) if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[LANGUAGE+\d+\]", lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def laughter(texts, entity_map, ids):
    print("Anonymizing laughter...")
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  "" if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[LAUGHTER+-\d+\]", lambda x: callback(x,id) ,text)
        new_texts.append(new_text)
    return new_texts, entity_map


def law(texts, entity_map, ids):
    print("Anonymizing law...")
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  "[]" if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[LAW+-\d+\]", lambda x: callback(x,id),text)
        new_texts.append(new_text)
    return new_texts, entity_map


def loc(texts, entity_map, ids):
    print("Anonymizing loc...")
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  "[]" if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[LOC+-\d+\]", lambda x: callback(x,id) ,text)
        new_texts.append(new_text)
    return new_texts,entity_map


def money(texts, entity_map, ids, modality):
    print("Anonymizing money...")

    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        if modality == 'text':
            money = '$' + str(random.randrange(200,500))
        else:
            money = inflector.number_to_words(random.randrange(200,500)) + " DOLLARS"
        r =  money if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[MONEY+-\d+\]",lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map

def norp(texts, entity_map, ids):
    print("Anonymizing NORPs (nationality, religious or political organizations)...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/nationalities.csv')
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        name = df['Nationality'].sample()
        r =  name.values[0] if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[NORP+-\d+\]",lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def ordinal(texts, entity_map, ids, modality):
    print("Anonymizing ordinals...")
    v_ordinal = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth"]
    t_ordinal = ["1st","2nd","3rd","4th","5th","6th","7th","8th","9th","10th"]
    
    if modality == 'text':
        ordinal = t_ordinal
    else:
        ordinal = v_ordinal
    
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r = random.choice(ordinal) if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts, ids):
        new_text = re.sub(r"\[ORDINAL+-\d+\]",lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def perc(texts, entity_map, ids, modality):
    print("Anonymizing cardinals...")

    if modality == 'text':
        perc = str(random.randrange(1,100)) + "%"
    else:
        perc = inflector.number_to_words(str(random.randrange(1,100))) + " PERCENT"

    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  perc if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[PERCENT-\d+\]",lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def person(texts, entity_map, ids):
    print("Anonymizing names (people)...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/baby-names.csv')
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        name = df['name'].sample()
        r =  name.values[0] if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[PERSON+-\d+\]",lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def phone(texts, entity_map, ids, modality):
    print("Anonymizing phone numbers...")

    area_code = str(random.randrange(200,999))
    exchange = str(random.randrange(200,999))
    number = str(random.randrange(1000,9999))

    if modality == 'text':
        phone = area_code + "-" + exchange + "-" + number
    else:
        phone = digits2words(str(area_code + exchange + number))
    
    new_texts = []

    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  phone if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[PHONE-\d+\]", lambda x: callback(x,id) , text)
        new_texts.append(new_text)
    return new_texts, entity_map


def product(texts, entity_map, ids):
    print("Anonymizing products...")
    product = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth"]
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  "[]" if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[PRODUCT+-\d+\]", lambda x: callback(x,id),text)
        new_texts.append(new_text)
    return new_texts, entity_map


def quantity(texts, entity_map, ids):
    print("Anonymizing quantities...")
    ordinal = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth"]
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  "[]" if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        #new_text = re.sub(r"\[QUANTITY\]",callback, text)
        new_text = re.sub(r"\[QUANTITY+-\d+\]",lambda x: callback(x,id),text)
        new_texts.append(new_text)
    return new_texts, entity_map


def work_of_art(texts, entity_map, ids):
    print("Anonymizing works of art...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/Artworks.csv')
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  str(df['Title'].sample().values[0]) if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    def callback(match,i):
        return str(df['Title'].sample().values[0])
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[WORK_OF_ART+-\d+\]",lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def zipC(texts, entity_map, ids, modality):
    print("Anonymizing zip codes...")

    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/zip_code_database.csv')

    if modality == 'text':
        zipC = df['zip'].sample().values[0]
    else:
        zipC = digits2words(str(df['zip'].sample().values[0]))

    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  zipC if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r
    for text,id in zip(texts,ids):
        new_text = re.sub(r"\[ZIP+-\d+\]",lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map