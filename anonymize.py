import pandas as pd
import numpy as np
import csv
import random
import re
import os


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


def date(texts):
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


def gpe(texts):
    print("Anonymizing places...")
    new_texts = []
    for text in texts:
        new_text = re.sub(r"\[GPE\]",'CITI', text)
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