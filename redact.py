import os
import spacy
import pandas as pd
import entity_rules as er
import processor_base as pb
import sys
import regex_utils as ru
import json
import yaml

# Pattern and compiled regex to define labels that need to be protected
REDACT_LABEL_PATTERN="\[\w+(-\d+){0,1}\]"
REDACT_LABEL_RU=ru.compile(REDACT_LABEL_PATTERN, 0, ru.EngineType.REGEX) 

# Exception classes for redactors

## Redactor classes ##

#Base class from which all redactors are derived.
class RedactorBase(pb.ProcessorBase):
    '''Construct a redactor, pass command line arguments that can affect the behaviour of the redactor.'''
    def __init__(self,id,entity_rules):
        self._entity_map=None
        self._entity_values=None
        super().__init__(id, entity_rules)
     
    '''Virtual function defining what a configuration call should look like.'''
    # entity_map : a map to keep track of indexes assoigned to redacted words to enable restoration of consitent anonymized words later.
    # entity_values: a dictionary to keep the substituted entity values keyed by their substituted labels (e.g. ) entity_values["PIN-45"=1234]
    def configure(self, params, entity_map, entity_values):
        #Call the base class configurator.
        super().configure(params)
        self._entity_map=entity_map
        self._entity_values=entity_values

    #Implement the generic processor rule.  
    def process(self,df):
        #This is currently not defined and will throw an exception.
        #In the future this would call or replace redact() by converting the dataframe to a text and id array.
        raise NotImplementedError

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
            _regex_set=self._entity_rules.get_regex_set(_regex_id)
        elif (_regex_filename is not None):
            #IMPLEMENT THIS!
            raise er.EntityRuleConfigException("ERROR: regex-filename is not yet supported.")
        elif (_regex is not None):
            _regex_set=_regex
        else:
            raise er.EntityRuleConfigException("ERROR: No valid regex defined in rule: "+str(self._id))
        
        self._group=_model_params.get("group",1)     
        self._flags=ru.flags_from_array(_model_params.get("flags",["IGNORECASE"]),ru.EngineType.REGEX)
        
        #Compile these regexs after adding a pattern to also detect existing redaction labels so we can save them later.
        try:
           self._pattern_set = [ru.compile(r, self._flags, ru.EngineType.REGEX) for r in _regex_set]
        except Exception as exc:
            print(f'WARNING: Failed to compile regex set for {self._id} with error: {str(exc)}')
            print(f'IGNORING: regex set {_regex_set}')

    #previously: the_redactor()
    #Supports more than one regular expressions and runs each one, even if a prevoius one found a match.
    def redact(self, texts, eCount, ids):
        new_texts = []
        for text, d_id in zip(texts,ids):
            newString = text
            for pattern in self._pattern_set:
                #Find all the existing entity labels in the string, and build a list of protected start./end points
                entity_matches = list(REDACT_LABEL_RU.finditer(newString))
                protect_zones=[]
                if entity_matches:
                    for e in entity_matches:
                        protect_zones.append([e.start(),e.end()])    

                #Find the entities matching in the string
                matches = list(pattern.finditer(newString))
                for e in reversed(matches): #reversed to not modify the offsets of other entities when substituting
                    #name=entity-text found by pattern
                    if self._group != 1 and e.captures(self._group):
                            name = e.captures(self._group)[0]
                            start = e.span(self._group)[0]
                    else:
                        name = e.group()
                        start = e.span()[0]
                    end = start + len(name)

                    #Check if we have matched part of an entity label
                    protected=False
                    for z in protect_zones:
                        if ((start>=z[0] and start<=(z[1]-1)) or ((end-1)>=z[0] and (end-1)<=(z[1]-1))):
                            protected=True
                            #print(f'INFORMATION: The match string: \'{name}\' is part of an existing redaction label: \'{newString[z[0]:z[1]]}\' and will not be redacted.')

                    #Add a redaction label if the thing we matched wasn't already part of a redaction label.
                    #if (REDACT_LABEL_RU.match(name) is None): 
                    if not protected:
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
        #print("RedactorPhraseList.configure()._model_params:",str(_model_params),file=sys.stderr)
 
        #If the paramters do not contain a definition for the current modality then assume that the model is not designed for this and return None.
        if _model_params is None: 
            print("WARNING. Using a null model. No model defined for id:",self._id,"modality:",self._entity_rules.args.modality,file=sys.stderr)
            return None

        #Get the possible parameters
        _phrase_filename=_model_params.get("phrase-filename",None)   
        _phrase_field=_model_params.get("phrase-field",None)
        _phrase_column=_model_params.get("phrase-column",0)
        _phrase_header=_model_params.get("phrase-header",True)
        _phrase_list=_model_params.get("phrase-list",None)   

        #Load the phrase list depending on how it is specified.
        if (_phrase_list is None) and  (_phrase_filename is not None):
            if _phrase_header is None:  _df = pd.read_csv(self.absolute_path(_phrase_filename), Header=None)
            else: _df = pd.read_csv(self.absolute_path(_phrase_filename))
            if _phrase_field is None:
                _phrase_list=(_df.iloc[:,_phrase_column]).to_list()
            else:
                _phrase_list=_df[_phrase_field].to_list()
        
        #If the list is ok then add it to the phrase list set.
        if (not isinstance(_phrase_list,list)) or len(_phrase_list)==0:
            raise er.EntityRuleConfigException("ERROR: Invalid or empty phrase list rule for entity: "+str(self._id))
        
        #Debug
        #print("RedactorPhraseList.configure()._phrase_list:",self._phrase_list,file=sys.stderr)

        self._phrase_list=_phrase_list    

    #was ignore_phrases()
    def redact(self, texts, eCount, ids):
        for phrase in self._phrase_list :
            #Delegate the task to a regexRedactor which will use the parameters in this config parameter set.
            #print("Phrase: "+str(phrase))
            _my_redactor=RedactorRegex(self._id,self._entity_rules)
            _my_model_params=self._params.copy()
            _my_model_params[self._entity_rules.args.modality]["regex"]=[str(phrase)]
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

class RedactorPhraseDict(RedactorRegex):
    def __init__(self, id, entity_rules):
        self._phrase_list=None
        self._params={}
        super().__init__(id, entity_rules)

    def load_phraseset_json(self,filepath):
        '''Load a JSON file to define the phrase sets'''
        print("Loading phrase set file:",filepath)
        with open(filepath) as stream:
            try:
                self._phrase_dict=json.load(stream)
                #print("PHRASE SET: ",str(self._phrase_dict))    
            except Exception as e:
                raise(e)

    def load_phraseset_yaml(self, filepath):
        '''Load a YAML rulefile to define the entities'''
        print("Loading phrase set file:",filepath)

        with open(filepath, "r") as stream:
            try:
                self._phrase_dict=yaml.safe_load(stream)
                #print("PHRASE SET: ",str(self._phrase_dict))    
            except yaml.YAMLError as e:
                raise(e)

    def load_phraseset(self, filepath):
        fname, fext = os.path.splitext(filepath)
        if (fext==".yml" or fext==".yaml"):
            self.load_phraseset_yaml(filepath)
        elif (fext==".json"):
            self.load_phraseset_json(filepath)
        else:
            print("WARNING: file: "+str(filepath)+" is being ignored. Phrase set files must have extension .yml, .yaml. or .json.",file=sys.stderr)
        
    def configure(self, params, entity_map, entity_values):
        #Fully override the base class configure function.
        self._params=params
        self._entity_map=entity_map
        self._entity_values=entity_values
        self._phrase_dict={}

        #Now use the parameters passed, plus the modality in the entity_rules to congifure up this class.
        #Get params.voice or params.text if they are specified.
        _model_params=params.get(self._entity_rules.args.modality,None)
        #print(f'RedactorPhraseListTMobile.configure()._model_params: {str(_model_params)}',file=sys.stderr)
 
        #If the paramters do not contain a definition for the current modality then assume that the model is not designed for this and return None.
        if _model_params is None: 
            print("WARNING. Using a null model. No model defined for id:",self._id,"modality:",self._entity_rules.args.modality,file=sys.stderr)
            return None

        #Get the possible parameters
        _phrase_filename=_model_params.get("phrase-filename",None)   
        _phrase_path=_model_params.get("phrase-path",None)

        #If there are prematch parameters then get them
        _prematch_params=_model_params.get("prematch",None)  
        self._pre_regex="\\b"
        if (not _prematch_params is None):
            _pre_regex_filename=_prematch_params.get("regex-filename",None)   
            _pre_regex_id=_prematch_params.get("regex-id",None)
            _pre_regex=_prematch_params.get("regex",None)

            #Build a prematch regex.
            if (_pre_regex_id is not None): 
                _pre_regex_set=self._entity_rules.get_regex_set(_pre_regex_id)
            elif (_pre_regex_filename is not None):
                #IMPLEMENT THIS!
                raise er.EntityRuleConfigException("ERROR: regex-filename is not yet supported.")
            elif (_pre_regex is not None):
                _pre_regex_set=[ _pre_regex ]
            else:
                raise er.EntityRuleConfigException("ERROR: No valid prematch egex defined in rule: "+str(self._id))

            #Now create one single regex from the pre-regex set.
            n=0
            self._pre_regex="("
            for pattern in _pre_regex_set:
                if n==0:  
                    self._pre_regex+=f'({pattern})'
                else:
                    self._pre_regex+=f'|({pattern})'
                n+=1
            self._pre_regex+=")"

            #print(f'prematch regex: {self._pre_regex}')

        #I would like to use jsonpath_ng for this but for simiplicity for now I will simply assume that an optional top-level array is allowed.
        _phrase_path_list=_phrase_path.split(".")
        _phrase_array_key=None
        if len(_phrase_path_list)==1:
            _phrase_field=_phrase_path_list[0]
        elif len(_phrase_path_list)==2:
            _phrase_array_key=_phrase_path_list[0]
            _phrase_field=_phrase_path_list[1]

        #Load the phrase set from file.
        if (_phrase_filename is not None):
            self.load_phraseset(self.absolute_path(_phrase_filename))

        #Now get a list of all the ignore phrases 
        _phrase_list=[]
        if (not self._phrase_dict=={}):
            if (not _phrase_array_key is None):
                terms=self._phrase_dict.get(_phrase_array_key)   
            else:
                terms=[self._phrase_dict]
            for t in terms:
                phrases=t.get(_phrase_field)
                if isinstance(phrases, str):
                    _phrase_list.append(t.get(_phrase_field))
                else:
                    _phrase_list.extend(t.get(_phrase_field))
         
        #If the list is ok then add it to the phrase list set.
        if (not isinstance(_phrase_list,list)) or len(_phrase_list)==0:
            raise er.EntityRuleConfigException("ERROR: Invalid or empty phrase list rule for entity: "+str(self._id))
        
        #Debug
        #print("RedactorPhraseList.configure()._phrase_list:",_phrase_list,file=sys.stderr)

        self._phrase_list=_phrase_list    

    #was ignore_phrases()
    def redact(self, texts, eCount, ids):
        for phrase in self._phrase_list :
            #Delegate the task to a regexRedactor which will use the parameters in this config parameter set.
            #print("Phrase: "+str(phrase))
            _my_redactor=RedactorRegex(self._id,self._entity_rules)
            _my_model_params=self._params.copy()
            _match_pattern=self._pre_regex+str(phrase)+"\\b"
            #print(f'match pattern: {_match_pattern}')
            _my_model_params[self._entity_rules.args.modality]["regex"]=[_match_pattern]
            #print("my_model_params:",_my_model_params)

            _my_redactor.configure(_my_model_params, self._entity_map, self._entity_values)
            texts, eCount, ids = _my_redactor.redact(texts, eCount, ids)
        return texts, eCount, ids