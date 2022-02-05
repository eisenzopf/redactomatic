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
import entity_rules as er
import regex_utils as ru
from xeger import Xeger

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

    @property
    def random(self):
        #common random object to ensure seeding is deterministic
        return self._entity_rules.random

class AnonRegex(AnonymizerBase):
    '''Class to anonymize a token by generating a random string from a regular expression.'''
    def __init__(self,id,entity_rules):
        self._pattern_set =[]
        self._flags=0
        self._limit=10
        self._xeger=None
        super().__init__(id, entity_rules)

    def configure(self, params):
        #Call the base class configurator.
        super().configure(params)

        #Get params.voice or params.text if they are specified.
        _model_params=params.get(self._entity_rules.args.modality,None)
        
        #Set up the Xeger generator. Pass it the shared random function so that the seed is deterministic.
        self._limit=_model_params.get("limit",10)  
        self._xeger = Xeger(limit=self._limit)
        self._xeger.random = self.random

        #If the paramters do not contain a definition for the current modality then raise a NotSupported exception.
        if _model_params is None: 
            raise er.NotSupportedException("Modality: "+str(self._entity_rules.args.modality)+" not supported for anonymizer id: "+self._id)
        #print("_model_params:",_model_params)

        #Build a regular expression matcher using the parameters in the relevant 'voice' or 'text' section.
        _regex_filename=_model_params.get("regex-filename",None)   
        _regex_id=_model_params.get("regex-id",None)
        _regex=_model_params.get("regex",None)
        
        #Get the regex from an inline definition, a ruleref, or an external file (NOT YET SUPPORTED)
        if (_regex_id is not None): 
            _regex_set=self._entity_rules.get_regex(_regex_id)
        elif (_regex_filename is not None):
            #IMPLEMENT THIS!
            raise er.EntityRuleConfigException("ERROR: regex-filename is not yet supported.")
        elif (_regex is not None):
            _regex_set=_regex
        else:
            raise er.EntityRuleConfigException("ERROR: No valid regex defined in rule: "+str(self._id))

        #ensure we have a list of regexp expressions (even if there is just one in the list.)  
        if isinstance(_regex_set,str): _regex_set=[_regex_set]
        if not isinstance(_regex_set,list): raise er.EntityRuleConfigException("ERROR: regular expression rules should be lists or single strings.")    

        #self._flags=_model_params.get("flags",0)
        self._flags=ru.flags_from_array(_model_params.get("flags",[]),ru.EngineType.RE)
        
        try:
            self._pattern_set = [regex.compile(r, self._flags) for r in _regex_set]
        except Exception as exc:
            print("WARNING: Failed to compile regex set for ':"+self._id+"' with error: "+str(exc))

    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []

        def callback(match, i):
            #If there are multiple regexps in a list, then pick one at random.
            pattern=self.random.choice(self._pattern_set)
            anon_string= self._xeger.xeger(pattern)
            #print ("pattern:",pattern,"string:",anon_string)
            tag = match.group()
            return self.persist_entity_value(i,tag,anon_string,entity_map)
            
        this_regex = self.anon_regex(self._id)
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonRestoreEntityText(AnonymizerBase):
    '''Class to replace an anonymization token with the original text that was redacted in order to restore the original text.'''
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        print("Re-inserting ignored text...")
        new_texts = []
        pattern = regex.compile(r'(\[('+self._id+'\-\d+)\])')

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

class AnonNullString(AnonymizerBase):
    '''Class to replace the anonymization token with a null string.'''
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        def callback(match, i):
            tag = match.group()
            return self.persist_entity_value(i,tag,"",entity_map)

        this_regex = self.anon_regex(self._id)
        for text, id in zip(texts, conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x, id),text)
            new_texts.append(new_text)
        return new_texts, entity_map

### Custom anonymization classes for specific entity types ###

class AnonAddress(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/street-names.csv')

        def callback(match, i):
            street = str(self.random.choice(df['Streets']))
            if self._entity_rules.args.modality == 'text':
                number = str(self.random.randrange(100,500))
            else:
                number = inflector.number_to_words(self.random.randrange(100,500))
            address = number + " " + street + " "

            tag = match.group()
            return self.persist_entity_value(i,tag,address,entity_map)
        
        this_regex = self.anon_regex("ADDRESS")

        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonCompany(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/Top-100-Retailers.csv')

        def callback(match, i):
            company = str(self.random.choice(df['Company']))
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
            name = str(self.random.choice(df['name']))

            email = name + "@gmail.com"
            tag = match.group()
            return self.persist_entity_value(i,tag,email,entity_map)

        this_regex = self.anon_regex("EMAIL")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonGPE(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/gpe.csv')
        def callback(match, i):
            gpe = str(self.random.choice(df. iloc[:, 0]))
            tag = match.group()
            return self.persist_entity_value(i,tag,gpe,entity_map)

        this_regex = self.anon_regex("GPE")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex,lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map

class AnonLoc(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        # us-area-code-cities
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/us-area-code-cities.csv')
        def callback(match, i):
            loc = str(self.random.choice(df['city']))
            tag = match.group()
            return self.persist_entity_value(i,tag,loc,entity_map)

        this_regex = self.anon_regex("LOC")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id) ,text)
            new_texts.append(new_text)
        return new_texts,entity_map

class AnonNorp(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []
        df = pd.read_csv(os.getcwd() + '/data/nationalities.csv')
        def callback(match, i):
            norp = str(self.random.choice(df['Nationality']))
            tag = match.group()
            return self.persist_entity_value(i,tag,norp,entity_map)

        this_regex = self.anon_regex("NORP")
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
            name = str(self.random.choice(df['name']))
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
            area_code = str(self.random.randrange(200,999))
            exchange = str(self.random.randrange(200,999))
            number = str(self.random.randrange(1000,9999))
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

class AnonSSN(AnonymizerBase):
    def anonymize(self, texts, conversation_ids, entity_map, entity_values):
        new_texts = []

        def callback(match, i):
            first = str(self.random.randrange(200,999))
            second = str(self.random.randrange(10,99))
            third = str(self.random.randrange(1000,9999))
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
            work = str(self.random.choice(df['Title']))
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
                zipC = str(self.random.choice(df['zip']))
            else:
                zipC = digits2words(str(self.random.choice(df['zip'])))
            tag = match.group()
            return self.persist_entity_value(i,tag,zipC,entity_map)

        this_regex = self.anon_regex("ZIP")
        for text,id in zip(texts,conversation_ids):
            new_text = regex.sub(this_regex, lambda x: callback(x,id), text)
            new_texts.append(new_text)
        return new_texts, entity_map