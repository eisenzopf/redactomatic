import json
import os
#from pyrsistent import v
import spacy
import regex
import pandas as pd
import numpy as np
import entity_map as em
import entity_rules as er
import sys
import regex_utils as ru

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

## Redactor classes ##

#Base class from which all redactors are derived.
class RedactorBase():
    '''Construct a redactor, pass command line arguments that can affect the behaviour of the redactor.'''
    def __init__(self,id,entity_rules):
        self._entity_rules=entity_rules
        self._entity_map=None
        self._entity_values=None
        self._params={}
        self._id=id
     
    '''Virtual function defining what a configuration call should look like.'''
    # entity_map : a map to keep track of indexes assoigned to redacted words to enable restoration of consitent anonymized words later.
    # entity_values: a dictionary to keep the substituted entity values keyed by their substituted labels (e.g. ) entity_values["PIN-45"=1234]
    def configure(self, params, entity_map, entity_values):
        self._params=params
        self._entity_map=entity_map
        self._entity_values=entity_values

    # IMPLEMENT THIS FUNCTION TO:
    # Find match to pattern of type label; keeping entities map updated and tracking ID-TEXT connection,
    # pattern: the regex used to match the target entity.
    # label: contains IGNORE,ADDRESS,CCARD,EMAIL,PHONE,PIN,SSN,ZIP
    # texts : an array of texts to be redacted
    # eCount : a unique entity key, ready for the next discovered entity
    # ids: an array of conversation-ids (aligns with the texts in length and content)

    '''Virtual function defining what a redaction should look like.'''
    def redact(self, texts, eCount, ids):
        return texts, eCount, ids

class RedactorRegex(RedactorBase):
    def __init__(self,id, entity_rules):
        #to ignore case set flags= regex.IGNORECASE
        self._group =None      
        self._pattern_set =[]
        self._flags=0
        super().__init__(id, entity_rules)

    def configure(self, params, entity_map, entity_values):
        #Call the base class configurator.
        super().configure(params,entity_map, entity_values)

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

        self._group=_model_params.get("group",1)     
        self._flags=ru.flags_from_array(_model_params.get("flags",["IGNORECASE"]),ru.EngineType.REGEX)
        
        try:
            self._pattern_set = [regex.compile(r, self._flags) for r in _regex_set]
        except Exception as exc:
            print("WARNING: Failed to compile regex set for ':"+self._id+"' with error: "+str(exc))

    #previously: the_redactor()
    #Supports more than one regular expressions and runs each one, even if a prevoius one found a match.
    def redact(self, texts, eCount, ids):
        new_texts = []
        for text, d_id in zip(texts,ids):
            newString = text
            for pattern in self._pattern_set:
                matches = list(pattern.finditer(text))

                for e in reversed(matches): #reversed to not modify the offsets of other entities when substituting
                    #name=entity-text found by pattern
                    if self._group != 1 and e.captures(self._group):
                            name = e.captures(self._group)[0]
                            start = e.span(self._group)[0]
                    else:
                        name = e.group()
                        start = e.span()[0]

                    if not (self._id == "CARDINAL" and "[" in name and "]" in name): #not capture label ids as cardinal
                        ix = self._entity_map.update_entities(name,d_id,eCount,self._id)
                        end = start + len(name)
                        newLabel=self._entity_values.set_label_value(self._id,ix,name)
                        newString = newString[:start] + "["+ newLabel + "]" + newString[end:]
                        eCount += 1
            new_texts.append(newString)
        return new_texts, eCount, ids

class RedactorPhraseList(RedactorRegex):
    def __init__(self, id, entity_rules):
        self._phrase_list=None
        self._params={}
        super().__init__(id, entity_rules)

    def configure(self, params, entity_map, entity_values):
        #Fully override the base class configure function.
        self._params=params
        self._entity_map=entity_map
        self._entity_values=entity_values

        #Now use the parameters passed, plus the modality in the entity_rules to congifure up this class.
        #Get params.voice or params.text if they are specified.
        _model_params=params.get(self._entity_rules.args.modality,None)

        #If the paramters do not contain a definition for the current modality then assume that the model is not designed for this and return None.
        if _model_params is None: return None

        #Get the possible parameters
        _phrase_filename=_model_params.get("phrase-filename",None)   
        _phrase_field=_model_params.get("phrase-field",None)
        _phrase_column=_model_params.get("phrase-column",0)
        _phrase_header=_model_params.get("phrase-header",True)
        _phrase_list=_model_params.get("phrase-list",None)   

        #Load the phrase list depending on how it is specified.
        if (_phrase_list is None) and  (_phrase_filename is not None):
            if _phrase_header is None:  _df = pd.read_csv(_phrase_filename, Header=None)
            else: _df = pd.read_csv(_phrase_filename)
            if _phrase_field is None:
                _phrase_list=(_df.iloc[:,_phrase_column]).to_list()
            else:
                _phrase_list=_df[_phrase_field].to_list()
        
        #If the list is ok then add it to the phrase list set.
        if (not isinstance(_phrase_list,list)) or len(_phrase_list)==0:
            raise er.EntityRuleConfigException("ERROR: Invalid or empty phrase list rule for entity: "+str(self._id))
        
        self._phrase_list=_phrase_list    

    #was ignore_phrases()
    def redact(self, texts, eCount, ids):
        for phrase in self._phrase_list :
            #Delegate the task to a regexRedactor which will use the parameters in this config parameter set.
            #print("Phrase: "+str(phrase))
            _my_redactor=RedactorRegex(self._id,self._entity_rules)
            _my_model_params=self._params.copy()
            _my_model_params[self._entity_rules.args.modality]["regex"]=str(phrase)
            #print("my_model_params:",_my_model_params)

            _my_redactor.configure(_my_model_params, self._entity_map, self._entity_values)
            texts, eCount, ids = _my_redactor.redact(texts, eCount, ids)
        return texts, eCount, ids

class RedactorSpacy(RedactorBase):
    def __init__(self,id, entity_rules):
        super().__init__(id, entity_rules)
    
    #was ner_ml()
    def redact(self, texts, eCount, ids):
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
                            c = self._entity_map.update_entities(name,d_id,eCount,e.label_)
                            newString = newString[:start] + " [" + e.label_ +"-"+ str(c) + "]" + newString[end:]
                            eCount += 1
                    else:
                        ix = self._entity_map.update_entities(name,d_id,eCount,e.label_)
                        start = e.start_char
                        end = start + len(name)
                        newLabel=self._entity_values.set_label_value(e.label_,ix,name)
                        newString = newString[:start] + "[" + newLabel + "]" + newString[end:]
                        eCount += 1
            newString = newString.replace('$','')
            new_texts.append(newString)
        return new_texts, eCount, ids

