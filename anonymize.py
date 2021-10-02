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


def adate(texts, entity_map, ids, modality, anon_map, token_map):
    print("Anonymizing dates...")
    new_texts = []
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    ordinal_days = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth", "twentieth", "twenty first", "twenty second", "twenty third", "twenty fourth", "twenty fifth", "twenty sixth", "twenty seventh", "twenty eighth"]

    def callback(match, i):
        if modality == 'text':
            date = str(random.randrange(1,12)) + "/" + str(random.randrange(1,28))
        else:
            date = random.choice(months) + " " + random.choice(ordinal_days)
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = date
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = date
        return r
        
    this_regex = anon_regex("DATE", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def address(texts, entity_map, ids, modality, anon_map, token_map):
    print("Anonymizing addresses...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/street-names.csv')

    def callback(match, i):
        streets = df['Streets'].sample()
        street = streets.values[0]
        if modality == 'text':
            number = str(random.randrange(100,500))
        else:
            number = inflector.number_to_words(random.randrange(100,500))
        address = number + " " + street + " "

        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = address
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = address
        return r
    
    this_regex = anon_regex("ADDRESS", anon_map, token_map)

    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def anon_regex(type, anon_map, token_map):
    counter = 0
    if type in anon_map.keys():
        for entity in anon_map[type]:
            if counter == 0:
                this_regex = "\[" + entity + "-\d+\]"
            else:
                this_regex = this_regex + "|\[" + entity + "-\d+\]"
            counter = counter + 1
    if type in token_map.keys():
        for entity in token_map[type]:
            if counter == 0:
                this_regex = entity
            else:
                this_regex = this_regex + "|" + entity
            counter = counter + 1
    return this_regex


def atime(texts, entity_map, ids, modality, anon_map, token_map):
    print("Anonymizing time...")
    hours = ["one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve"]
    minutes = ["oh one","oh two","oh three","oh four","oh five","oh six","oh seven","oh nine","ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen"]
    new_texts = []
    
    def callback(match, i):
        if modality == 'text':
            time = str(random.randrange(1,12)) + ":" + str(random.randrange(0,50)) + " " + str(random.choice(["AM","PM"]))
        else:
            time = str(random.choice(hours)) + " " + str(random.choice(minutes)) + " " + str(random.choice(["AM","PM"]))  
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = time
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = time
        return r
        
    this_regex = anon_regex("TIME", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def cardinal(texts, entity_map, ids, modality, anon_map, token_map):
    print("Anonymizing cardinals...")
    t_cardinal = ["0","1","2","3","4","5","6","7","8","9"]
    v_cardinal = ["zero","one","two","three","four","five","six","seven","eight","nine"]
    if modality == 'text':
        cardinal = t_cardinal
    else:
        cardinal = v_cardinal
    
    new_texts = []
    def callback(match, i):
        this_cardinal = random.choice(cardinal)
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = this_cardinal
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = this_cardinal
        return r

    this_regex = anon_regex("CARDINAL", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def ccard(texts, entity_map, ids, modality, anon_map, token_map):
    print("Anonymizing credit card numbers...")
    new_texts = []

    def callback(match, i):
        ccnumber = ""
        length = 16
        while len(ccnumber) <= (length - 1):
            digit = str(random.randrange(0,9))
            ccnumber += digit
        if modality == 'text':
            ccard = str(ccnumber)
        else:
            ccard = digits2words(ccnumber)
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = ccard
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = ccard
        return r

    this_regex = anon_regex("CCARD", anon_map, token_map)

    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id) , text)
        new_texts.append(new_text)
    return new_texts, entity_map


def company(texts, entity_map, ids, anon_map, token_map):
    print("Anonymizing names (organizations)...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/Top-100-Retailers.csv')

    def callback(match, i):
        company = df.sample().values[0][0]
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = company
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = company
        return r

    this_regex = anon_regex("ORG", anon_map, token_map)
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


def email(texts, entity_map, ids, modality, anon_map, token_map):
    print("Anonymizing email addresses...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/baby-names.csv')
    def callback(match, i):
        name = df['name'].sample()
        email = name.values[0] + "@gmail.com"
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = email
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = email
        return r

    this_regex = anon_regex("EMAIL", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def event(texts, entity_map, ids, anon_map, token_map):
    print("Anonymizing events...")
    events = ["seminar","conference","trade show","workshop","reunion","party","gala","picnic","meeting","lunch"]
    new_texts = []
    def callback(match, i):
        event = random.choice(events)
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = event
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = event
        return r

    this_regex = anon_regex("EVENT", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def fac(texts, entity_map, ids, anon_map, token_map):
    print("Anonymizing facility names...")
    new_texts = []
    def callback(match, i):
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = ""
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = ""
        return r

    this_regex = anon_regex("FAC", anon_map, token_map)
    for text, id in zip(texts, ids):
        new_text = re.sub(this_regex,lambda x: callback(x, id),text)
        new_texts.append(new_text)
    return new_texts, entity_map


def gpe(texts, entity_map, ids, anon_map, token_map):
    print("Anonymizing country, city, state...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/gpe.csv')
    def callback(match, i):
        gpe = df.sample().values[0][0]
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = gpe
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = gpe
        return r

    this_regex = anon_regex("GPE", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def language(texts, entity_map, ids, anon_map, token_map):
    print("Anonymizing language...")
    language = ["Chinese", "Spanish", "English", "Hindi", "Arabic", "Portuguese", "Russian", "German", "Korean", "French", "Turkish"]
    new_texts = []
    def callback(match, i):
        this_language = random.choice(language)
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = this_language
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = this_language
        return r

    this_regex = anon_regex("LANGUAGE", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def laughter(texts, entity_map, ids, anon_map, token_map):
    print("Anonymizing laughter...")
    new_texts = []
    def callback(match, i):
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = ""
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = ""
        return r

    this_regex = anon_regex("LAUGHTER", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id) ,text)
        new_texts.append(new_text)
    return new_texts, entity_map


def law(texts, entity_map, ids, anon_map, token_map):
    print("Anonymizing law...")
    new_texts = []
    def callback(match, i):
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = ""
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = ""
        return r

    this_regex = anon_regex("LAW", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id),text)
        new_texts.append(new_text)
    return new_texts, entity_map


def loc(texts, entity_map, ids, anon_map, token_map):
    print("Anonymizing loc...")
    # us-area-code-cities
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/us-area-code-cities.csv')
    def callback(match, i):
        name = df['city'].sample()
        loc = name.values[0]
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = loc
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = loc
        return r

    this_regex = anon_regex("LOC", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id) ,text)
        new_texts.append(new_text)
    return new_texts,entity_map


def money (texts, entity_map, ids, modality, anon_map, token_map):
    print("Anonymizing money...")
    new_texts = []
    def callback(match, i):
        if modality == 'text':
            money = '$' + str(random.randrange(200,500))
        else:
            money = inflector.number_to_words(random.randrange(200,500)) + " dollars"
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = money
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = money
        return r

    this_regex = anon_regex("MONEY", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def norp (texts, entity_map, ids, anon_map, token_map):
    print("Anonymizing NORPs (nationality, religious or political organizations)...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/nationalities.csv')
    def callback(match, i):
        name = df['Nationality'].sample()
        norp = name.values[0]
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = norp
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = norp
        return r

    this_regex = anon_regex("NORP", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def ordinal (texts, entity_map, ids, modality, anon_map, token_map):
    print("Anonymizing ordinals...")
    v_ordinal = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth"]
    t_ordinal = ["1st","2nd","3rd","4th","5th","6th","7th","8th","9th","10th"]
    
    if modality == 'text':
        ordinal = t_ordinal
    else:
        ordinal = v_ordinal
    
    new_texts = []
    def callback(match, i):
        number = random.choice(ordinal)
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = number
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = number
        return r

    this_regex = anon_regex("ORDINAL", anon_map, token_map)
    for text,id in zip(texts, ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def perc (texts, entity_map, ids, modality, anon_map, token_map):
    print("Anonymizing cardinals...")
    new_texts = []
    def callback(match, i):
        if modality == 'text':
            perc = str(random.randrange(1,100)) + "%"
        else:
            perc = inflector.number_to_words(str(random.randrange(1,100))) + " PERCENT"
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = perc
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = perc
        return r

    this_regex = anon_regex("PERCENT", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def person (texts, entity_map, ids, df, anon_map, token_map):
    print("Anonymizing names (people)...")
    new_texts = []
    def callback(match, i):
        tag = match.group()
        name = str(df['name'].sample().values[0])
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = name
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = name
        return r

    this_regex = anon_regex("PERSON", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def phone(texts, entity_map, ids, modality, anon_map, token_map):
    print("Anonymizing phone numbers...")
    new_texts = []

    def callback(match, i):
        area_code = str(random.randrange(200,999))
        exchange = str(random.randrange(200,999))
        number = str(random.randrange(1000,9999))
        if modality == 'text':
            phone = area_code + "-" + exchange + "-" + number
        else:
            phone = digits2words(str(area_code + exchange + number))
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = phone
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = phone
        return r

    this_regex = anon_regex("PHONE", anon_map, token_map)

    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id) , text)
        new_texts.append(new_text)
    return new_texts, entity_map


def pin(texts, entity_map, ids, modality, anon_map, token_map):
    print("Anonymizing PIN numbers...")
    new_texts = []

    def callback(match, i):
        rand_4d = str(random.randrange(1000,9999))
        if modality == 'voice':
            pin = digits2words(str(rand_4d))
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = pin
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = pin
        return r

    this_regex = anon_regex("PIN", anon_map, token_map)
    print("PIN regex is " + this_regex)

    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id) , text)
        new_texts.append(new_text)
    return new_texts, entity_map


def product(texts, entity_map, ids, anon_map, token_map):
    print("Anonymizing products...")
    product = ["cheese","beef","milk","corn","couch","chair","table","window","stove","desk"]
    new_texts = []
    def callback(match, i):
        this_product = random.choice(product)
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = this_product
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = this_product
        return r

    this_regex = anon_regex("PRODUCT", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id),text)
        new_texts.append(new_text)
    return new_texts, entity_map


def quantity(texts, entity_map, ids, anon_map, token_map):
    print("Anonymizing quantities...")
    new_texts = []
    def callback(match, i):
        quantity = str(random.randrange(1000,9999))
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = quantity
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = quantity
        return r

    this_regex = anon_regex("QUANTITY", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id),text)
        new_texts.append(new_text)
    return new_texts, entity_map


def ssn(texts, entity_map, ids, modality, anon_map, token_map):
    print("Anonymizing Social Security numbers...")
    new_texts = []

    def callback(match, i):
        first = str(random.randrange(200,999))
        second = str(random.randrange(10,99))
        third = str(random.randrange(1000,9999))
        if modality == 'text':
            ssn = first + "-" + second + "-" + third
        else:
            ssn = digits2words(str(first + second + third))
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = ssn
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = ssn
        return r

    this_regex = anon_regex("SSN", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def work_of_art(texts, entity_map, ids, anon_map, token_map):
    print("Anonymizing works of art...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/Artworks.csv')

    def callback(match, i):
        work = str(df['Title'].sample().values[0])
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = work
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = work
        return r

    this_regex = anon_regex("WORK_OF_ART", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex,lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map


def zipC(texts, entity_map, ids, modality, anon_map, token_map):
    print("Anonymizing zip codes...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/zip_code_database.csv')

    def callback(match, i):
        if modality == 'text':
            zipC = str(df['zip'].sample().values[0])
        else:
            zipC = digits2words(str(df['zip'].sample().values[0]))
        tag = match.group()
        this_match = re.search('-', tag)
        if this_match:   # handling for ENTITY-dddd tags
            m_id = int(tag[tag.rindex('-')+1:-1])   # create entity_map if we are anonymizing a previously redacted file 
            if i not in entity_map:
                entity_map[i]={}
            if m_id not in entity_map[i]:
                entity_map[i][m_id]={}
            if bool(entity_map[i][m_id]):    # if we have an existing value in the entity_map, use it, otherwise use a new one and save it to the entity_map for context
                r = entity_map[i][m_id]
            else:
                r = zipC
                entity_map[i][m_id] = r
        else:   # for token mapped tags, we don't care about the entity_map, just randomize a value
            r = zipC
        return r

    this_regex = anon_regex("ZIP", anon_map, token_map)
    for text,id in zip(texts,ids):
        new_text = re.sub(this_regex, lambda x: callback(x,id), text)
        new_texts.append(new_text)
    return new_texts, entity_map