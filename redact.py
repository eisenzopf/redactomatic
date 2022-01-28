import json
import os
from pyrsistent import v
import spacy
import regex
import pandas as pd
import numpy as np
import entity_map as em
import entity_rules as er

#Helper functions

def clean(texts):
    print("Cleaning text (Regex)...")
    spaces = regex.compile('\s+')
    dotdot = regex.compile(r'\.\.\.')
    unknown = regex.compile(r'\<UNK\>')
    add_space = regex.compile(r'(\]\[)')
    add_space2 = regex.compile(r'((\w+)\[)')
    add_space3 = regex.compile(r'(\](\w+))')
    new_texts = []
    for text in texts:
        new_text = dotdot.sub('', text, concurrent=True)
        new_text = spaces.sub(' ', new_text, concurrent=True)
        new_text = unknown.sub('', new_text, concurrent=True)
        new_text = add_space.sub('] [', new_text, concurrent=True)
        new_text = add_space2.sub(r'\2 [', new_text, concurrent=True)
        new_text = add_space3.sub(r'] \2', new_text, concurrent=True)
        new_text = new_text.strip()
        new_texts.append(new_text)
    return new_texts

def convert_to_uppercase(texts):
    print("Converting letters to uppercase...")
    new_texts=[]
    for text in texts:
        new_text = text.upper()
        new_texts.append(new_text)
    return new_texts


def replace_ignore(texts,entity_values):
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
    return new_texts

## Redactor classes ##

#Base class from which all redactors are derived.
class RedactorModel():
    def __init__(self):
        pass

class NullRedactor(RedactorModel):
    def __init__(self):
        super().__init__()   

    def redact(self, texts, entity_map, eCount, ids, entity_values):
        return texts, entity_map, eCount, ids, entity_values

class RedactorRegexp(RedactorModel):

    def __init__(self):
        #to ignorre case set flags= regex.IGNORECASE
        self._label =None
        self._group =None
        self._pattern =None
        self._flags=0
        super().__init__()

    def configure(self,label,regexp,group=1,flags=0):
        self._label=label
        self._group=group
        self._flags=flags
        self._pattern = regex.compile(regexp, self._flags)       

    #Tracking ID-TEXT connection, find match to pattern of type label; keeping entities map updated
    # pattern: the regex used to match the target entity.
    # label: contains IGNORE,ADDRESS,CCARD,EMAIL,PHONE,PIN,SSN,ZIP
    # texts : an array of texts to be redacted
    # entity_map : a map to keep track of indexes assoigned to redacted words to enable restoration of consitent anonymized words later.
    # eCount : a unique entity key, ready for the next discovered entity
    # ids: an array of conversation-ids (aligns with the texts in length and content)
    # entity_values: a dictionary to keep the substituted entity values keyed by their substituted labels (e.g. ) entity_values["PIN-45"=1234]
    # group:  contains the target match group for the regex. By default the whole match is used but this can be a named match (e.g. group='zip')
    
    #previously: the_redactor()
    def redact(self, texts, entity_map, eCount, ids, entity_values):
        new_texts = []
        for text, d_id in zip(texts,ids):
            matches = list(self._pattern.finditer(text))
            newString = text
            for e in reversed(matches): #reversed to not modify the offsets of other entities when substituting
                #name=entity-text found by pattern
                if self._group != 1 and e.captures(self._group):
                        name = e.captures(self._group)[0]
                        start = e.span(self._group)[0]
                else:
                    name = e.group()
                    start = e.span()[0]

                if not (self._label == "CARDINAL" and "[" in name and "]" in name): #not capture label ids as cardinal
                    ix = entity_map.update_entities(name,d_id,eCount,self._label)
                    end = start + len(name)
                    newLabel=entity_values.set_label_value(self._label,ix,name)
                    newString = newString[:start] + "["+ newLabel + "]" + newString[end:]
                    eCount += 1
            new_texts.append(newString)
        return new_texts, entity_map, eCount, ids, entity_values

class RedactorRegexpFromFile(RedactorRegexp):
    def __init__(self):
        self._label=None
        self._group=None
        self._filepath=None
        self._flags=0
        super().__init__()

    def configure(self,label,filepath,group=1,flags=0):
        self._label=label
        self._group=group
        self._filepath=filepath 
        self._flag=flags

    #was ignore_phrases()
    def redact(self, texts, entity_map, eCount, ids, entity_values):
        with open(self._filepath) as json_file:
            phrases = json.load(json_file)
        
        for phrase in phrases:
            super().configure(self._label,phrase,flags=self._flags)
            texts, entity_map, eCount, ids, entity_values = super().redact(texts, entity_map, eCount, ids, entity_values)
        return texts, entity_map, eCount, ids, entity_values

class RedactorSpacy(RedactorModel):
    def __init__(self):
        self._use_large=False
        self._entities=[]
        super().__init__()
    
    def configure(self,use_large,entities):
        self._use_large=use_large
        self._entities=entities

    #was ner_ml()
    def redact(self, texts, entity_map, eCount, ids, entity_values):
        from spacy.lang.en import English
        spacy_multiword_labels = ["PERSON"]
        if self._use_large:
            nlp = spacy.load("en_core_web_lg")
        else:
            nlp = spacy.load("en_core_web_sm")
        new_texts = []
        #Spacy version of the_redactor function...
        for doc, d_id in zip(nlp.pipe(texts, disable=["tagger", "parser", "lemmatizer"], n_process=4, batch_size=1000),ids):
            newString = doc.text
            for e in reversed(doc.ents): #reversed to not modify the offsets of other entities when substituting
                # redact if the recognized entity is in the list of entities from the config.json file
                if e.label_ in self._entities:
                    name = e.text
                    value = name
                    # split name if we have a first and last name ( [PERSON] )
                    if e.label_ in spacy_multiword_labels and " " in name:
                        broken = name.split()
                        for i,n, in enumerate(reversed(broken)):
                            i = len(broken)-1 -i
                            name = n
                            start = e.start_char + sum([len(w)+1 for w in broken[:i]])
                            end = start + len(name)
                            c = entity_map.update_entities(name,d_id,eCount,e.label_)
                            newString = newString[:start] + " [" + e.label_ +"-"+ str(c) + "]" + newString[end:]
                            eCount += 1
                    else:
                        ix = entity_map.update_entities(name,d_id,eCount,e.label_)
                        start = e.start_char
                        end = start + len(name)
                        newLabel=entity_values.set_label_value(e.label_,ix,name)
                        newString = newString[:start] + "[" + newLabel + "]" + newString[end:]
                        eCount += 1
            newString = newString.replace('$','')
            new_texts.append(newString)
        return new_texts, entity_map, eCount, ids, entity_values

