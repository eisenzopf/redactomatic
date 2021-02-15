import pandas as pd
import numpy as np
import csv
import random
import re
import os
from datetime import date


def cardinal(texts):
    print("Anonymizing cardinals...")
    cardinal = ["zero","one","two","three","four","five","six","seven","eight","nine"]
    new_texts = []
    def callback(match):
        return random.choice(cardinal)
    for text in texts:
        new_text = re.sub(r"\[CARDINAL\]",callback, text).upper()
        new_texts.append(new_text)
    return new_texts


def company(texts):
    print("Anonymizing names (organizations)...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/Top-100-Retailers.csv')
    def callback(match):
        company = df.sample()
        return company.values[0][0].upper()
    for text in texts:
        new_text = re.sub(r"\[ORG\]",callback, text)
        new_texts.append(new_text)
    return new_texts


def adate(texts):
    print("Anonymizing dates...")
    new_texts = []
    relative_dates = ['today','yesterday','last monday', 'last tuesday', 'last wednesday', 'last thursday', 'last friday', 'last saturday', 'last sunday']
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    ordinal_days = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth", "twentieth", "twenty first", "twenty second", "twenty third", "twenty fourth", "twenty fifth", "twenty sixth", "twenty seventh", "twenty eighth"]
    def callback(match):
        mode = random.choice([0,1])
        if mode == 1:
            return random.choice(relative_dates).upper()
        else:
            date = random.choice(months).upper() + " " + random.choice(ordinal_days).upper()
            return date
    for text in texts:
        new_text = re.sub(r"\[DATE\]",callback, text)
        new_texts.append(new_text)
    return new_texts


def digits2words(digits):
    num2words = {'0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'}
    words = ''
    for digit in range(0, len(digits)): 
        words += " " + num2words[digits[digit]]
    return words


def event(texts):
    print("Anonymizing events...")
    events = ["seminar","conference","trade show","workshop","reunion","party","gala","picnic","meeting","lunch"]
    new_texts = []
    def callback(match):
        return random.choice(events)
    for text in texts:
        new_text = re.sub(r"\[EVENT\]",callback, text).upper()
        new_texts.append(new_text)
    return new_texts


def fac(texts):
    print("Anonymizing facility names...")
    new_texts = []
    for text in texts:
        new_text = re.sub(r"\[FAC\]","",text)
        new_texts.append(new_text)
    return new_texts


def gpe(texts):
    print("Anonymizing country, city, state...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/gpe.csv')
    def callback(match):
        gpe = df.sample()
        return gpe.values[0][0].upper()
    for text in texts:
        new_text = re.sub(r"\[GPE\]",callback, text)
        new_texts.append(new_text)
    return new_texts


def language(texts):
    print("Anonymizing language...")
    language = ["Chinese", "Spanish", "English", "Hindi", "Arabic", "Portuguese", "Russian", "German", "Korean", "French", "Turkish"]
    new_texts = []
    def callback(match):
        return random.choice(language)
    for text in texts:
        new_text = re.sub(r"\[LANGUAGE\]", callback, text).upper()
        new_texts.append(new_text)
    return new_texts


def laughter(texts):
    print("Anonymizing laughter...")
    new_texts = []
    for text in texts:
        new_text = re.sub(r"\[LAUGHTER\]","",text)
        new_texts.append(new_text)
    return new_texts


def law(texts):
    print("Anonymizing law...")
    new_texts = []
    for text in texts:
        new_text = re.sub(r"\[LAW\]","",text)
        new_texts.append(new_text)
    return new_texts


def loc(texts):
    print("Anonymizing loc...")
    new_texts = []
    for text in texts:
        new_text = re.sub(r"\[LOC\]","",text)
        new_texts.append(new_text)
    return new_texts


def money(texts):
    print("Anonymizing money...")
    new_texts = []
    def callback(match):
        return digits2words(str(random.randrange(200,500))).upper()
    for text in texts:
        new_text = re.sub(r"\[MONEY\]",callback, text).upper()
        new_texts.append(new_text)
    return new_texts

def norp(texts):
    print("Anonymizing NORPs (nationality, religious or political organizations)...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/nationalities.csv')
    def callback(match):
        name = df['Nationality'].sample()
        return name.values[0].upper()
    for text in texts:
        new_text = re.sub(r"\[NORP\]",callback, text)
        new_texts.append(new_text)
    return new_texts


def ordinal(texts):
    print("Anonymizing ordinals...")
    ordinal = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth"]
    new_texts = []
    def callback(match):
        return random.choice(ordinal)
    for text in texts:
        new_text = re.sub(r"\[ORDINAL\]",callback, text).upper()
        new_texts.append(new_text)
    return new_texts


def person(texts):
    print("Anonymizing names (people)...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/baby-names.csv')
    def callback(match):
        name = df['name'].sample()
        return name.values[0].upper()
    for text in texts:
        new_text = re.sub(r"\[PERSON\]",callback, text)
        new_texts.append(new_text)
    return new_texts


def product(texts):
    print("Anonymizing products...")
    product = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth"]
    new_texts = []
    #def callback(match):
        #return random.choice(product)
    for text in texts:
        #new_text = re.sub(r"\[PRODUCT\]",callback, text).upper()
        new_text = re.sub(r"\[PRODUCT\]","",text)
        new_texts.append(new_text)
    return new_texts


def quantity(texts):
    print("Anonymizing quantities...")
    ordinal = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth"]
    new_texts = []
    #def callback(match):
        #return random.choice(ordinal)
    for text in texts:
        #new_text = re.sub(r"\[QUANTITY\]",callback, text).upper()
        new_text = re.sub(r"\[QUANTITY\]","",text)
        new_texts.append(new_text)
    return new_texts
    

def time(texts):
    print("Anonymizing time...")
    day = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth","eleventh","twelvth","thirteenth","fourteenth","fifteenth","sixteenth"]
    month = ["january","february","march","april","may","june","july","august","september","october","november","december"]
    new_texts = []
    def callback(match):
        return (random.choice(month) + " " +  random.choice(day))
    for text in texts:
        new_text = re.sub(r"\[TIME\]",callback, text).upper()
        new_texts.append(new_text)
    return new_texts


def work_of_art(texts):
    print("Anonymizing works of art...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/Artworks.csv')
    def callback(match):
        return str(df['Title'].sample().values[0]).upper()
    for text in texts:
        new_text = re.sub(r"\[WORK_OF_ART\]",callback, text)
        new_texts.append(new_text)
    return new_texts


def zip(texts):
    print("Anonymizing zip codes...")
    new_texts = []
    df = pd.read_csv(os.getcwd() + '/data/zip_code_database.csv')
    def callback(match):
        return digits2words(str(df['zip'].sample().values[0])).upper()
    for text in texts:
        new_text = re.sub(r"\[ZIP\]",callback, text)
        new_texts.append(new_text)
    return new_texts