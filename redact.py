import json
import os
from pyrsistent import v
import spacy
import regex
import pandas as pd
import numpy as np
import entity_map as em
import entity_rules as er
import sys

# Exception classes for redactors

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
class RedactorBase():
    '''Construct a redactor, pass command line arguments that can affect the behaviour of the redactor.'''
    def __init__(self,id,entity_rules):
        self._entity_rules=entity_rules
        self._params={}
        self._id=id
     
    '''Virtual function defining what a configuration call should look like.'''
    def configure(self, params):
        self._params=params

    # IMPLEMENT THIS FUNCTION TO:
    # Find match to pattern of type label; keeping entities map updated and tracking ID-TEXT connection,
    # pattern: the regex used to match the target entity.
    # label: contains IGNORE,ADDRESS,CCARD,EMAIL,PHONE,PIN,SSN,ZIP
    # texts : an array of texts to be redacted
    # entity_map : a map to keep track of indexes assoigned to redacted words to enable restoration of consitent anonymized words later.
    # eCount : a unique entity key, ready for the next discovered entity
    # ids: an array of conversation-ids (aligns with the texts in length and content)
    # entity_values: a dictionary to keep the substituted entity values keyed by their substituted labels (e.g. ) entity_values["PIN-45"=1234]
    # group:  contains the target match group for the regex. By default the whole match is used but this can be a named match (e.g. group='zip')

    '''Virtual function defining what a redaction should look like.'''
    def redact(self, texts, entity_map, eCount, ids, entity_values):
        return texts, entity_map, eCount, ids, entity_values

class RedactorRegex(RedactorBase):
    def __init__(self,id, entity_rules):
        #to ignore case set flags= regex.IGNORECASE
        self._group =None      
        self._pattern =None
        self._flags=0
        super().__init__(id, entity_rules)

    def configure(self, params):
        #Call the base class configurator.
        super().configure(params)

        #Now use the parameters passed, plus the modality in the entity_rules to congifure up this class.
        #Get params.voice or params.text if they are specified.
        _model_params=params.get(self._entity_rules.args.modality,None)

        #If the paramters do not contain a definition for the current modality then assume that the model is not designed for this and return None.
        if _model_params is None: 
            raise er.NotSupportedException("Modality: "+str(self._entity_rules.args.modality)+" not supported for redactor id: "+self._id)
        #print("_model_params:",_model_params)

        #Build a regular expression matcher using the parameters in the relevant 'voice' or 'text' section.
        _regex_filename=_model_params.get("regex-filename",None)   
        _regex_id=_model_params.get("regex-id",None)
        _regex=_model_params.get("regex",None)
        
        #Get the regex from an inline definition, a ruleref, or an external file (NOT YET SUPPORTED)
        if (_regex_id is not None): 
            _regex_string=str(self._entity_rules.get_regex(_regex_id))
        elif (_regex_filename is not None):
            #IMPLEMENT THIS!
            raise er.EntityRuleCongfigError("ERROR: regex-filename is not yet supported.")
        elif (_regex is not None):
            _regex_string=str(_regex)
        else:
            raise er.EntityRuleCongfigError("ERROR: No valid regex defined in rule: "+str(self._id))

        self._group=_model_params.get("group",1)     
        self._flags=_model_params.get("flags",regex.IGNORECASE)
        
        #The regex is defined in another rule in the rulesbase object then use this definition. Will overwrite any local regex definition.
        try:
            #print("compiling:",_regex_string)
            self._pattern = regex.compile(_regex_string, self._flags)              
        except Exception as exc:
            print("WARNING: Failed to compile regex ':"+self._id+"' with error: "+str(exc))

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

                if not (self._id == "CARDINAL" and "[" in name and "]" in name): #not capture label ids as cardinal
                    ix = entity_map.update_entities(name,d_id,eCount,self._id)
                    end = start + len(name)
                    newLabel=entity_values.set_label_value(self._id,ix,name)
                    newString = newString[:start] + "["+ newLabel + "]" + newString[end:]
                    eCount += 1
            new_texts.append(newString)
        return new_texts, entity_map, eCount, ids, entity_values

class RedactorPhraseList(RedactorRegex):
    def __init__(self, id, entity_rules):
        self._phrase_list=None
        self._params={}
        super().__init__(id, entity_rules)

    def configure(self, params):
        #Remember the params. We'll use them when we delegate this match to RedactorRegex
        self._params=params

        #Now use the parameters passed, plus the modality in the entity_rules to congifure up this class.
        #Get params.voice or params.text if they are specified.
        _model_params=params.get(self._entity_rules.args.modality,None)

        #If the paramters do not contain a definition for the current modality then assume that the model is not designed for this and return None.
        if _model_params is None: return None

        #Note the filename for the match.
        _phrase_filename=_model_params.get("phrase-filename",None)   
        _phrase_list=_model_params.get("phrase-list",None)   
        if (_phrase_list is not None):
            self._phrase_list=_phrase_list
            #print("Phrase list: "+str(self._phrase_list))
        elif (_phrase_filename is not None):
            with open(self._phrase_filename) as json_file:
                #print ("Open ",self._phrase_filename)
                self._phrase_list = json.load(json_file)
        else:
            raise er.EntityRuleCongfigException("ERROR: No phrase list defined for phrase-list entity definition.")

    #was ignore_phrases()
    def redact(self, texts, entity_map, eCount, ids, entity_values):
        for phrase in self._phrase_list :
            #Delegate the task to a regexRedactor which will use the parameters in this config parameter set.
            #print("Phrase: "+str(phrase))
            _my_redactor=RedactorRegex(self._id,self._entity_rules)
            _my_model_params=self._params.copy()
            _my_model_params[self._entity_rules.args.modality]["regex"]=str(phrase)
            #print("my_model_params:",_my_model_params)

            _my_redactor.configure(_my_model_params)
            texts, entity_map, eCount, ids, entity_values = _my_redactor.redact(texts, entity_map, eCount, ids, entity_values)
        return texts, entity_map, eCount, ids, entity_values

class RedactorSpacy(RedactorBase):
    def __init__(self,id, entity_rules):
        super().__init__(id, entity_rules)
    
    def configure(self,params):
        '''Configure the spacy redactor.'''
        super().configure(params)

    #was ner_ml()
    def redact(self, texts, entity_map, eCount, ids, entity_values):
        from spacy.lang.en import English
        spacy_multiword_labels = ["PERSON"]
        if self._entity_rules.args.large:
            nlp = spacy.load("en_core_web_lg")
        else:
            nlp = spacy.load("en_core_web_sm")
        new_texts = []
        #Spacy version of the_redactor function...
        for doc, d_id in zip(nlp.pipe(texts, disable=["tagger", "parser", "lemmatizer"], n_process=4, batch_size=1000),ids):
            newString = doc.text
            for e in reversed(doc.ents): #reversed to not modify the offsets of other entities when substituting
                # redact if the recognized entity is in the list of entities from the config.json file
                if e.label_ in self._entity_rules.entities:
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

