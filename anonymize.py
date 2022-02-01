import pandas as pd
import numpy as np
import csv
import random
import regex
import os
from datetime import date
import inflect
import sys
import entity_map as em

inflector = inflect.engine()

## Helper functions ###

def digits2words(digits):
    num2words = {'0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'}
    words = ''
    for digit in range(0, len(digits)): 
        words += " " + num2words[digits[digit]]
    return words

## Anonymizer classes ##

#Base class from which all anonymizers are derived.
class AnonymizerBase():
    '''Construct a redactor, pass command line arguments that can affect the behaviour of the redactor.'''
    def __init__(self,id,entity_rules):
        self._entity_rules=entity_rules
        self._params={}
        self._id=id
     
    '''Virtual prototype for configuring an anonymizer with a specific set of parameters.'''
    def configure(self, params):
        self._params=params

    '''Virtual prototype for anonymization.'''
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        return texts, entity_map

    def persist_entity_value(self, id, tag, entity_value, entity_map):
        #Look for tags of the form '[ENTITY-dddd]' where dddd is an integer identifier for the entity.
        #The enclosing [ ] are optional so this function also works with tags of the form 'ENTITY-dddd'.
        #If this exists then we look whether we have seen something of type 'ENTITY' with this id and index previously.
        #If we have then use that value otherwise use the value we were given and remember it for later calls.
        #If the tag does not match the pattern then just return the value we were given.

        this_match = regex.fullmatch('\[?(.*)-(.*?)\]?', tag)

        if this_match:   # handling for ENTITY-dddd tags    
            m_ix=this_match[2]
            m_cat=this_match[1]
            r=entity_map.update_entities(m_ix, id, entity_value, m_cat)
        else:
            r=entity_value
        return r

    def anon_regex(self, type):
        anon_map=self._entity_rules.anon_map
        token_map=self._entity_rules.token_map

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

class AnonRestoreEntityText(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        print("Re-inserting ignored text...")
        new_texts = []
        pattern = regex.compile(r'(\[(_IGNORE_\-\d+)\])')

        for text in texts:
            matches = list(pattern.finditer(text))
            newString = text
            for e in reversed(matches):
                name = e.group(2)
                start = e.span()[0]
                end = start + len(e.group())
                newString = newString[:start] + entity_values.get_value(name) + newString[end:]
            new_texts.append(newString)
        return new_texts, entity_map

class AnonDate(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        ordinal_days = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth", "twentieth", "twenty first", "twenty second", "twenty third", "twenty fourth", "twenty fifth", "twenty sixth", "twenty seventh", "twenty eighth"]

        def callback(match, i):
            if self._entity_rules.args.modality == 'text':
                date = str(random.randrange(1,12)) + "/" + str(random.randrange(1,28))
            else:
                date = random.choice(months) + " " + random.choice(ordinal_days)
            tag = match.group()
            return self.persist_entity_value(i,tag,date,entity_map)
            
        this_regex = self.anon_regex("DATE")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonAddress(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/street-names.csv')

        def callback(match, i):
            street = str(random.choice(df['Streets']))
            if self._entity_rules.args.modality == 'text':
                number = str(random.randrange(100,500))
            else:
                number = inflector.number_to_words(random.randrange(100,500))
            address = number + " " + street + " "

            tag = match.group()
            return self.persist_entity_value(i,tag,address,entity_map)
        
        this_regex = self.anon_regex("ADDRESS")

        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonTime(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        hours = ["one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve"]
        minutes = ["oh one","oh two","oh three","oh four","oh five","oh six","oh seven","oh nine","ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen"]
        new_texts = []
        
        def callback(match, i):
            if self._entity_rules.args.modality == 'text':
                time = str(random.randrange(1,12)) + ":" + str(random.randrange(0,50)) + " " + str(random.choice(["AM","PM"]))
            else:
                time = str(random.choice(hours)) + " " + str(random.choice(minutes)) + " " + str(random.choice(["AM","PM"]))  
            tag = match.group()
            return self.persist_entity_value(i,tag,time,entity_map)
            
        this_regex = self.anon_regex("TIME")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonCardinal(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        t_cardinal = ["0","1","2","3","4","5","6","7","8","9"]
        v_cardinal = ["zero","one","two","three","four","five","six","seven","eight","nine"]
        if self._entity_rules.args.modality == 'text':
            cardinal = t_cardinal
        else:
            cardinal = v_cardinal
        
        new_texts = []
        def callback(match, i):
            this_cardinal = random.choice(cardinal)
            tag = match.group()
            return self.persist_entity_value(i,tag,this_cardinal,entity_map)

        this_regex = self.anon_regex("CARDINAL")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonCCard(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []

        def callback(match, i):
            ccnumber = ""
            length = 16
            while len(ccnumber) <= (length - 1):
                digit = str(random.randrange(0,9))
                ccnumber += digit
            if self._entity_rules.args.modality == 'text':
                ccard = str(ccnumber)
            else:
                ccard = digits2words(ccnumber)
            tag = match.group()
            return self.persist_entity_value(i,tag,ccard,entity_map)

        this_regex = self.anon_regex("CCARD")

        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id) , text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonCompany(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/Top-100-Retailers.csv')

        def callback(match, i):
            company = str(random.choice(df['Company']))
            tag = match.group()
            return self.persist_entity_value(i,tag,company,entity_map)

        this_regex = self.anon_regex("ORG")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id) , text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonEmail(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/baby-names.csv')
        def callback(match, i):
            name = str(random.choice(df['name']))

            email = name + "@gmail.com"
            tag = match.group()
            return self.persist_entity_value(i,tag,email,entity_map)

        this_regex = self.anon_regex("EMAIL")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonEvent(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        events = ["seminar","conference","trade show","workshop","reunion","party","gala","picnic","meeting","lunch"]
        new_texts = []
        def callback(match, i):
            event = random.choice(events)
            tag = match.group()
            return self.persist_entity_value(i,tag,event,entity_map)

        this_regex = self.anon_regex("EVENT")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonFac(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        def callback(match, i):
            tag = match.group()
            return self.persist_entity_value(i,tag,"",entity_map)

        this_regex = self.anon_regex("FAC")
        for text, id in zip(texts, conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x, id),text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonGPE(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/gpe.csv')
        def callback(match, i):
            gpe = str(random.choice(df. iloc[:, 0]))
            tag = match.group()
            return self.persist_entity_value(i,tag,gpe,entity_map)

        this_regex = self.anon_regex("GPE")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonLanguage(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        language = ["Chinese", "Spanish", "English", "Hindi", "Arabic", "Portuguese", "Russian", "German", "Korean", "French", "Turkish"]
        new_texts = []
        def callback(match, i):
            this_language = random.choice(language)
            tag = match.group()
            return self.persist_entity_value(i,tag,this_language,entity_map)

        this_regex = self.anon_regex("LANGUAGE")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonLaughter(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        def callback(match, i):
            tag = match.group()
            return self.persist_entity_value(i,tag,"",entity_map)

        this_regex = self.anon_regex("LAUGHTER")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id) ,text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonLaw(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        def callback(match, i):
            tag = match.group()
            this_match = regex.search('-', tag)
            return self.persist_entity_value(i,tag,"",entity_map)

        this_regex = self.anon_regex("LAW")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id),text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonLoc(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        # us-area-code-cities
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/us-area-code-cities.csv')
        def callback(match, i):
            loc = str(random.choice(df['city']))
            tag = match.group()
            return self.persist_entity_value(i,tag,loc,entity_map)

        this_regex = self.anon_regex("LOC")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id) ,text)
            new_texts.append(new_text)
        return new_texts,entity_map


class AnonMoney(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        def callback(match, i):
            if self._entity_rules.args.modality == 'text':
                money = '$' + str(random.randrange(200,500))
            else:
                money = inflector.number_to_words(random.randrange(200,500)) + " dollars"
            tag = match.group()
            return self.persist_entity_value(i,tag,money,entity_map)

        this_regex = self.anon_regex("MONEY")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonNorp(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/nationalities.csv')
        def callback(match, i):
            norp = str(random.choice(df['Nationality']))
            tag = match.group()
            return self.persist_entity_value(i,tag,norp,entity_map)

        this_regex = self.anon_regex("NORP")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonOrdinal(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        v_ordinal = ["first","second","third","fourth","fifth","sixth","seventh","eighth","ninth","tenth"]
        t_ordinal = ["1st","2nd","3rd","4th","5th","6th","7th","8th","9th","10th"]
        
        if self._entity_rules.args.modality == 'text':
            ordinal = t_ordinal
        else:
            ordinal = v_ordinal
        
        new_texts = []
        def callback(match, i):
            number = random.choice(ordinal)
            tag = match.group()
            return self.persist_entity_value(i,tag,number,entity_map)

        this_regex = self.anon_regex("ORDINAL")
        for text,id in zip(texts, conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonPercent(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        def callback(match, i):
            if self._entity_rules.args.modality == 'text':
                perc = str(random.randrange(1,100)) + "%"
            else:
                perc = inflector.number_to_words(str(random.randrange(1,100))) + " PERCENT"
            tag = match.group()
            return self.persist_entity_value(i,tag,perc,entity_map)

        this_regex = self.anon_regex("PERCENT")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonPerson(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/baby-names.csv')

        def callback(match, i):
            tag = match.group()
            name = str(random.choice(df['name']))
            return self.persist_entity_value(i,tag,name,entity_map)

        this_regex = self.anon_regex("PERSON")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonPhone(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []

        def callback(match, i):
            area_code = str(random.randrange(200,999))
            exchange = str(random.randrange(200,999))
            number = str(random.randrange(1000,9999))
            if self._entity_rules.args.modality == 'text':
                phone = area_code + "-" + exchange + "-" + number
            else:
                phone = digits2words(str(area_code + exchange + number))
            
            tag = match.group()
            return self.persist_entity_value(i,tag,phone,entity_map)

        this_regex = self.anon_regex("PHONE")

        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id) , text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonPIN(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []

        def callback(match, i):
            rand_4d = str(random.randrange(1000,9999))
            if self._entity_rules.args.modality == 'voice':
                pin = digits2words(str(rand_4d))
            else:
                pin = rand_4d
            tag = match.group()
            return self.persist_entity_value(i,tag,pin,entity_map)

        this_regex = self.anon_regex("PIN")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id) , text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonProduct(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        product = ["cheese","beef","milk","corn","couch","chair","table","window","stove","desk"]
        new_texts = []
        def callback(match, i):
            this_product = random.choice(product)
            tag = match.group()
            return self.persist_entity_value(i,tag,this_product,entity_map)

        this_regex = self.anon_regex("PRODUCT")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id),text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonQuantity(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        def callback(match, i):
            quantity = str(random.randrange(1000,9999))
            tag = match.group()
            return self.persist_entity_value(i,tag,quantity,entity_map)

        this_regex = self.anon_regex("QUANTITY")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id),text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonSSN(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []

        def callback(match, i):
            first = str(random.randrange(200,999))
            second = str(random.randrange(10,99))
            third = str(random.randrange(1000,9999))
            if self._entity_rules.args.modality == 'text':
                ssn = first + "-" + second + "-" + third
            else:
                ssn = digits2words(str(first + second + third))
            tag = match.group()
            return self.persist_entity_value(i,tag,ssn,entity_map)

        this_regex = self.anon_regex("SSN")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonWorkOfArt(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/Artworks.csv')

        def callback(match, i):
            work = str(random.choice(df['Title']))
            tag = match.group()
            return self.persist_entity_value(i,tag,work,entity_map)

        this_regex = self.anon_regex("WORK_OF_ART")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map


class AnonZipC(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/zip_code_database.csv')

        def callback(match, i):
            if self._entity_rules.args.modality == 'text':
                zipC = str(random.choice(df['zip']))
            else:
                zipC = digits2words(str(random.choice(df['zip'])))
            tag = match.group()
            return self.persist_entity_value(i,tag,zipC,entity_map)

        this_regex = self.anon_regex("ZIP")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map