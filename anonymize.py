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


def adate(texts, entity_map, ids, modality, anon_map):
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
        
    this_regex = anon_regex("DATE", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def address(texts, entity_map, ids, modality, anon_map):
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

        if m_id not in entity_map[i]:
            r = address
        else:
            r = entity_map[i][m_id]

        entity_map[i][m_id] = r
        return r
    
    this_regex = anon_regex("ADDRESS", anon_map)

    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def anon_regex(type, anon_map):
    counter = 0
    if type in anon_map.keys():
        for entity in anon_map[type]:
            if counter == 0:
                this_regex = "\[" + entity + "-\d+\]"
            else:
                this_regex = this_regex + "|\[" + entity + "-\d+\]"
            counter = counter + 1
    return this_regex


def atime(texts, entity_map, ids, modality, anon_map):
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
        
    this_regex = anon_regex("TIME", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def cardinal(texts, entity_map, ids, modality, anon_map):
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

    this_regex = anon_regex("CARDINAL", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def ccard(texts, entity_map, ids, modality, anon_map):
    print("Anonymizing credit card numbers...")

    ccnumber = ""
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

        if m_id not in entity_map[i]:
            r = ccard
        else:
            r = entity_map[i][m_id]

        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("CCARD", anon_map)

    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id) , text)
        new_texts.append(new_text)
    return new_texts, entity_map


def company(texts, entity_map, ids, anon_map):
    print("Anonymizing names (organizations)...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/Top-100-Retailers.csv')

    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  df.sample().values[0][0] if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("ORG", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id) , text)
        new_texts.append(new_text)
    return new_texts, entity_map


def digits2words(digits):
    num2words = {'0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'}
    words = ''
    for digit in range(0, len(digits)): 
        words += " " + num2words[digits[digit]]
    return words


def email(texts, entity_map, ids, modality, anon_map):
    print("Anonymizing email addresses...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/baby-names.csv')
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        name = df['name'].sample()

        if m_id not in entity_map[i]:
            r = name.values[0] + "@gmail.com"
        else:
            r = entity_map[i][m_id]

        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("EMAIL", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def event(texts, entity_map, ids, anon_map):
    print("Anonymizing events...")
    events = ["seminar","conference","trade show","workshop","reunion","party","gala","picnic","meeting","lunch"]
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  random.choice(events) if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("EVENT", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def fac(texts, entity_map, ids, anon_map):
    print("Anonymizing facility names...")
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  "[]" if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("FAC", anon_map)
    for text, id in zip(texts, ids):
        new_text = re.sub(this_regex,lambda x: callback(x, id),text)
        new_texts.append(new_text)
    return new_texts, entity_map


def gpe(texts, entity_map, ids, anon_map):
    print("Anonymizing country, city, state...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/gpe.csv')
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  df.sample().values[0][0] if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("GPE", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def language(texts, entity_map, ids, anon_map):
    print("Anonymizing language...")
    language = ["Chinese", "Spanish", "English", "Hindi", "Arabic", "Portuguese", "Russian", "German", "Korean", "French", "Turkish"]
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  random.choice(language) if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("LANGUAGE", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def laughter(texts, entity_map, ids, anon_map):
    print("Anonymizing laughter...")
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  "" if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("LAUGHTER", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id) ,text)
        new_texts.append(new_text)
    return new_texts, entity_map


def law(texts, entity_map, ids, anon_map):
    print("Anonymizing law...")
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  "[]" if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("LAW", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id),text)
        new_texts.append(new_text)
    return new_texts, entity_map


def loc(texts, entity_map, ids, anon_map):
    print("Anonymizing loc...")
    # us-area-code-cities
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/us-area-code-cities.csv')
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        name = df['city'].sample()
        r =  name.values[0] if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("LOC", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id) ,text)
        new_texts.append(new_text)
    return new_texts,entity_map


def money(texts, entity_map, ids, modality, anon_map):
    print("Anonymizing money...")
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        if modality == 'text':
            money = '$' + str(random.randrange(200,500))
        else:
            money = inflector.number_to_words(random.randrange(200,500)) + " DOLLARS"

        if m_id not in entity_map[i]:
            r = money
        else:
            r = entity_map[i][m_id]

        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("MONEY", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map

def norp(texts, entity_map, ids, anon_map):
    print("Anonymizing NORPs (nationality, religious or political organizations)...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/nationalities.csv')
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        name = df['Nationality'].sample()
        r =  name.values[0] if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r

    this_regex = anon_regex("NORP", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def ordinal(texts, entity_map, ids, modality, anon_map):
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

    this_regex = anon_regex("ORDINAL", anon_map)
    for text,id in zip(texts, ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def perc(texts, entity_map, ids, modality, anon_map):
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

    this_regex = anon_regex("PERCENT", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def person(texts, entity_map, ids, df, anon_map):
    print("Anonymizing names (people)...")
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        name = str(df['name'].sample().values[0])

        if m_id not in entity_map[i]:
            r = name
        else:
            r = entity_map[i][m_id]

        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("PERSON", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def phone(texts, entity_map, ids, modality, anon_map):
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

        if m_id not in entity_map[i]:
            r = phone
        else:
            r = entity_map[i][m_id]

        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("PHONE", anon_map)

    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id) , text)
        new_texts.append(new_text)
    return new_texts, entity_map


def product(texts, entity_map, ids, anon_map):
    print("Anonymizing products...")
    product = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth"]
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  "[]" if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("PRODUCT", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id),text)
        new_texts.append(new_text)
    return new_texts, entity_map


def quantity(texts, entity_map, ids, anon_map):
    print("Anonymizing quantities...")
    ordinal = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth"]
    new_texts = []
    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        r =  "[]" if entity_map[i][m_id] == '' else entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("QUANTITY", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id),text)
        new_texts.append(new_text)
    return new_texts, entity_map


def ssn(texts, entity_map, ids, modality, anon_map):
    print("Anonymizing Social Security numbers...")

    first = str(random.randrange(200,999))
    second = str(random.randrange(10,99))
    third = str(random.randrange(1000,9999))

    if modality == 'text':
        ssn = first + "-" + second + "-" + third
    else:
        ssn = digits2words(str(first + second + third))

    new_texts = []

    def callback(match, i):
        tag = match.group()
        m_id = int(tag[tag.rindex('-')+1:-1])
        if m_id not in entity_map[i]:
            r = ssn
        else:
            r = entity_map[i][m_id]
        entity_map[i][m_id] = r
        return r

    this_regex = anon_regex("SSN", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def work_of_art(texts, entity_map, ids, anon_map):
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

    this_regex = anon_regex("WORK_OF_ART", anon_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def zipC(texts, entity_map, ids, modality, anon_map):
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
        if m_id not in entity_map[i]:
            r = zipC
        else:
            r = entity_map[i][m_id]
        entity_map[i][m_id] = r
        return str(r)

    this_regex = anon_regex("ZIP", anon_map)

    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map