import csv
import json
import os
import sys
import spacy
import regex
import pandas as pd
import numpy as np
import entity_map as em
import entity_rules as er

#Tracking ID-TEXT connection, find match to pattern of type label; keeping entities map updated
# pattern: the regex used to match the target entity.
# label: contains IGNORE,ADDRESS,CCARD,EMAIL,PHONE,PIN,SSN,ZIP
# texts : an array of texts to be redacted
# entity_map : a map to keep track of indexes assoigned to redacted words to enable restoration of consitent anonymized words later.
# eCount : a unique entity key, ready for the next discovered entity
# ids: an array of conversation-ids (aligns with the texts in length and content)
# entity_values: a dictionary to keep the substituted entity values keyed by their substituted labels (e.g. ) entity_values["PIN-45"=1234]
# group:  contains the target match group for the regex. By default the whole match is used but this can be a named match (e.g. group='zip')

def the_redactor(pattern, label, texts, entity_map, eCount, ids, entity_values, group=1):
    new_texts = []
    for text, d_id in zip(texts,ids):
        matches = list(pattern.finditer(text))
        newString = text
        for e in reversed(matches): #reversed to not modify the offsets of other entities when substituting
            #name=entity-text found by pattern
            if group != 1 and e.captures(group):
                    name = e.captures(group)[0]
                    start = e.span(group)[0]
            else:
                name = e.group()
                start = e.span()[0]

            if not (label == "CARDINAL" and "[" in name and "]" in name): #not capture label ids as cardinal
                c = entity_map.update_entities(name,d_id,eCount,label)
                end = start + len(name)
                newLabel = label+ "-"+str(c)
                newString = newString[:start] + "["+ newLabel + "]" + newString[end:]
                entity_values = update_entity_values(newLabel,name,entity_values)
                eCount += 1
        new_texts.append(newString)
    return new_texts, entity_map, eCount, entity_values

def update_entity_values(id,value,entity_values):
    if id not in entity_values:
        entity_values[id] = value
    return entity_values


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
    pattern = regex.compile(r'(\[(IGNORE\-\d+)\])')

    for text in texts:
        matches = list(pattern.finditer(text))
        newString = text
        for e in reversed(matches):
            name = e.group(2)
            start = e.span()[0]
            end = start + len(e.group())
            newString = newString[:start] + entity_values[name] + newString[end:]
        new_texts.append(newString)
    return new_texts


def load_config(level):
    print("Loading configuration...")
    config = {}
    entities = []
    with open(os.getcwd() + '/config.json') as json_file:
        config = json.load(json_file)
    if level == 1:
        entities = config['level-1']
    elif level == 2:
        entities = config['level-2']
    elif level == 3:
        entities = config['level-3']
    return entities, config['redaction-order'], config['anon-map'], config['token-map']


def write_audit_log(filename, entity_values):
    print("Writing log to " + filename)
    a_file = open(os.getcwd() + "/" + filename, "w")
    writer = csv.writer(a_file)
    for key, value in entity_values.items():
        writer.writerow([key, value])
    a_file.close()

### Redaction Definitions ###

def ignore_phrases(texts, entity_map, eCount, ids, entity_values):
    print("Redacting ignore phrases (Regex)...")
    entity_values = {}
    with open(os.getcwd() + '/ignore.json') as json_file:
        phrases = json.load(json_file)
    for phrase in phrases:
        pattern = regex.compile(phrase,regex.IGNORECASE)
        texts, entity_map, eCount, entity_values = the_redactor(pattern, "IGNORE", texts, entity_map, eCount, ids, entity_values)
    return texts, entity_map, eCount, entity_values

def ner_ml(texts, entity_map, eCount, ids, entity_values, args, entities):
    print("Redacting named entities (ML)...")
    from spacy.lang.en import English
    spacy_multiword_labels = ["PERSON"]
    if args.large:
        nlp = spacy.load("en_core_web_lg")
    else:
        nlp = spacy.load("en_core_web_sm")
    new_texts = []
    #Spacy version of the_redactor function...
    for doc, d_id in zip(nlp.pipe(texts, disable=["tagger", "parser", "lemmatizer"], n_process=4, batch_size=1000),ids):
        newString = doc.text
        for e in reversed(doc.ents): #reversed to not modify the offsets of other entities when substituting
            # redact if the recognized entity is in the list of entities from the config.json file
            if e.label_ in entities:
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
                    c = entity_map.update_entities(name,d_id,eCount,e.label_)
                    start = e.start_char
                    end = start + len(name)
                    newLabel = e.label_ +"-"+ str(c)
                    newString = newString[:start] + "[" + newLabel + "]" + newString[end:]
                    entity_values = update_entity_values(newLabel,value,entity_values)
                    eCount += 1
        newString = newString.replace('$','')
        new_texts.append(newString)
    return new_texts, entity_map, eCount, ids, entity_values

def entity_re(texts, entity_map, eCount, ids, entity_values, entity_rules, label, rkey, group=1 ):
    print("Redacting",rkey,"(Regex)...")
    pattern = regex.compile(entity_rules.get_regexp(rkey), regex.IGNORECASE)    
    return the_redactor(pattern, label, texts, entity_map, eCount, ids, entity_values, group)
