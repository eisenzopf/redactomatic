import os
import spacy
import pandas as pd
import entity_rules as er
import processor_base as pb
import sys
import regex_utils as ru
import json
import yaml

## Redactor classes ##

#Base class from which all redactors are derived.
class RedactorBase(pb.ProcessorBase):
    '''Static class members'''
    REDACT_LABEL_RU=ru.compile(r'\[\w+(-\d+){0,1}\]', 0, ru.EngineType.REGEX) 

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
    
    '''Return a list of protected zones in the string that contain redaction labels'''
    def get_redactlabel_spans(self,s):
        #Find all the existing entity labels in the string, and build a list of protected start./end points
        entity_matches = list(self.REDACT_LABEL_RU.finditer(s))
        protect_zones=[]
        if entity_matches:
            print(f'entity_matches: {entity_matches}\'')
            for e in entity_matches:
                protect_zones.append([e.start(),e.end(),e.group()])  
        return protect_zones

    '''Check whether the text between indexes start and end are part of a protected zone, and returns the text of the overlapped label it there is one.'''
    def overlaps_redactlabel_span(self,start,end,protect_zones):
        #print(f'in_protect_zones({protect_zones})')
        is_overlapping=False
        overlapped_label=''
        for z in protect_zones:
            #print(f'in_protect_zones({z})')
            if ((start>=z[0] and start<=(z[1]-1)) or ((end-1)>=z[0] and (end-1)<=(z[1]-1))):
                is_overlapping=True
                overlapped_label=z[2]
        return is_overlapping,overlapped_label
    
    '''Insert the supplied label with a unique index into string s to replace the the string index between start and end.  Also update the entity store with the value and increment the unique index.'''
    def insert_redactlabel_and_update_entities(self, s, start, end, label, value, conversation_id, eCount):                         
        ix = self._entity_map.update_entities(value,conversation_id,eCount,label)
        newLabel=self._entity_values.set_label_value(label,ix,value)
        s = s[:start] + "[" + newLabel + "]" + s[end:]
        eCount += 1
        
        return s,eCount
    
class RedactorRegex(RedactorBase):
    def __init__(self,id, entity_rules):
        #to ignore case set flags= regex.IGNORECASE
        self._group = 1      
        self._pattern_set =[]
        self._flags= 0
        super().__init__(id, entity_rules)

    '''Helper function returning a regex from parameter group looking for either regex:, regex-id, or regex-filename.'''
    def get_regex_set_from_params(self,param_set,default=''):
        if (not param_set is None):
            _regex_filename=param_set.get("regex-filename",None)   
            _regex_id=param_set.get("regex-id",None)
            _regex=param_set.get("regex",None)

            #Build a prematch regex.
            if (_regex_id is not None): 
                return self._entity_rules.get_regex_set(_regex_id)
            elif (_regex_filename is not None):
                #IMPLEMENT THIS!
                raise er.EntityRuleConfigException("ERROR: regex-filename is not yet supported.")
            elif (_regex is not None):
                if isinstance(_regex,list): return _regex
                else: return [ _regex ]
            else:
                raise er.EntityRuleConfigException("ERROR: No regex, regex-id or regex-filename defined in: "+str(self._id))
        return default

    def configure(self, params, entity_map, entity_values):
        #Call the base class configurator.
        super().configure(params, entity_map, entity_values)

        #Now use the parameters passed, plus the modality in the entity_rules to congifure up this class.
        #Get params.voice or params.text if they are specified.
        _model_params=params.get(self._entity_rules.args.modality,None)

        #If the paramters do not contain a definition for the current modality then assume that the model is not designed for this and return None.
        if _model_params is None: 
            raise er.NotSupportedException("Modality: "+str(self._entity_rules.args.modality)+" not supported for redactor id: "+self._id)
        #print("_model_params:",_model_params)

        #Build a regular expression matcher using the parameters in the relevant 'voice' or 'text' section.
        _regex_set=self.get_regex_set_from_params(_model_params)
        self._group=_model_params.get("group",1)     

        #Now compile the regex_set ready for redaction.
        _flags=ru.flags_from_array(_model_params.get("flags",["IGNORECASE"]),ru.EngineType.REGEX)
        _single_regex=_model_params.get("single-regex",True)
        try:
            self._pattern_set=ru.compile_set(_regex_set,single_regex=_single_regex, flags=_flags, etype=ru.EngineType.REGEX)
        except Exception as exc:
            print(f'WARNING: Failed to compile regex set for {self._id} with error: {str(exc)}')
            print(f'ABANDONING: {self._id}')

    #Supports more than one regular expressions and runs each one, even if a prevoius one found a match.
    def redact(self, texts, eCount, ids):
        new_texts = []
        for text, d_id in zip(texts,ids):
            newString = text
            for pattern in self._pattern_set:
                #Find all the existing entity labels in the string.
                protect_zones=self.get_redactlabel_spans(newString)

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
                    
                    #Check if we have matched part of an entity label, and add the redaction label if we are not.
                    is_overlapping,overlapped_label=self.overlaps_redactlabel_span(start,end,protect_zones)
                    if not is_overlapping:
                        newString, eCount=self.insert_redactlabel_and_update_entities(newString, start, end, self._id, name, d_id, eCount)   

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

        #Get pre and postmatch regex, default to word break if there is none defined.
        _add_wordbreak=_model_params.get("add-wordbreak",True)  
        _prematch_params=_model_params.get("prematch",None)  
        _pre_regex = ru.list_to_regex(self.get_regex_set_from_params(_prematch_params,['\b'] if _add_wordbreak else ['']))
        _postmatch_params=_model_params.get("postmatch",None)  
        _post_regex = ru.list_to_regex(self.get_regex_set_from_params(_postmatch_params,['\b'] if _add_wordbreak else ['']))
        #print(f'preregex: {str(_pre_regex)}')
        #print(f'postregex: {str(_post_regex)}')

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

        #Now compile the regex_set, default to add-wordbreaks=True and a combine-sets=True for efficiency.
        _flags=ru.flags_from_array(_model_params.get("flags",["IGNORECASE"]),ru.EngineType.REGEX)
        _single_regex=_model_params.get("combine-sets",True)
        try:
            self._pattern_set=ru.compile_set(_phrase_list,_pre_regex,_post_regex,_single_regex,_flags,ru.EngineType.REGEX)
        except Exception as exc:
            print(f'WARNING: Failed to compile regex set for {self._id} with error: {str(exc)}')
            print(f'ABANDONING: {self._id}')


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

        #Get the phrase parameters
        _phrase_filename=_model_params.get("phrase-filename",None)   
        _phrase_path=_model_params.get("phrase-path",None)

        #Get pre and postmatch regex, default to word break if there is none defined.
        _add_wordbreak=_model_params.get("add-wordbreak",True)  
        _prematch_params=_model_params.get("prematch",None)  
        _pre_regex = ru.list_to_regex(self.get_regex_set_from_params(_prematch_params,['\\b'] if _add_wordbreak else ['']))
        _postmatch_params=_model_params.get("postmatch",None)  
        _post_regex = ru.list_to_regex(self.get_regex_set_from_params(_postmatch_params,['\\b'] if _add_wordbreak else ['']))
        #print(f'preregex: {str(_pre_regex)}')
        #print(f'postregex: {str(_post_regex)}')

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

        #Now get a list of all the phrases 
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

        #Now compile the regex_set, default to add-wordbreaks=True and a combine-sets=True for efficiency.
        _flags=ru.flags_from_array(_model_params.get("flags",["IGNORECASE"]),ru.EngineType.REGEX)
        _single_regex=_model_params.get("combine-sets",True)
        try:
            self._pattern_set=ru.compile_set(_phrase_list,_pre_regex,_post_regex,_single_regex,_flags,ru.EngineType.REGEX)
        except Exception as exc:
            print(f'WARNING: Failed to compile regex set for {self._id} with error: {str(exc)}')
            print(f'ABANDONING: {self._id}')

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
            protect_zones=self.get_redactlabel_spans(newString)
 
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

                            #If the matched item is not in a protected zone (i.e a redaction label) then redact it.
                            is_overlapping,overlapped_label=self.overlaps_redactlabel_span(start,end,protect_zones)
                            if not is_overlapping:
                                newString, eCount=self.insert_redactlabel_and_update_entities(newString, start, end, e.label_, name, d_id, eCount)   
                    else:
                        start = e.start_char
                        end = start + len(name)

                        #If the matched item is not in a protected zone (i.e a redaction label) then redact it.
                        is_overlapping,overlapped_label=self.overlaps_redactlabel_span(start,end,protect_zones)
                        if not is_overlapping:
                            newString, eCount=self.insert_redactlabel_and_update_entities(newString, start, end, e.label_, name, d_id, eCount)   
            newString = newString.replace('$','')
            new_texts.append(newString)
        return new_texts, eCount, ids
    
'''A redactor class to implement the mapping from token map patterns to redaction labels.'''
class RedactorTokenMap(RedactorBase):
    def __init__(self,id, entity_rules):
        super().__init__(id, entity_rules)
        self._token_map={}
        self._flags= 0
        self._token_pattern={}
        self._all_patterns=None

    def configure(self, params, entity_map, entity_values):
        super().configure(params, entity_map, entity_values)

        #Now use the parameters passed, plus the modality in the entity_rules to congifure up this class.
        #Get params.voice or params.text if they are specified.
        _model_params=params.get(self._entity_rules.args.modality,None)

        #If the paramters do not contain a definition for the current modality then assume that the model is not designed for this and return None.
        if _model_params is None: 
            print("WARNING. Using a null model. No model defined for id:",self._id,"modality:",self._entity_rules.args.modality,file=sys.stderr)
            return None

        #Get the token map for this modality
        self._token_map=_model_params.get("token-map",{})   
        #print(f'RedactorTokenMap.configure(modality={self._entity_rules.args.modality})._token_map: {str(self._token_map)}',file=sys.stderr)

        #Get any regular expression flags from the array parameter 'flags'. 
        #Allowed items: "ASCII", "A", "IGNORECASE", "I", "MULTILINE", "M", "DOTALL", "S", "VERBOSE", "X", "LOCALE", "L" in any combination.
        self._flags=ru.flags_from_array(_model_params.get("flags",[]),ru.EngineType.REGEX)

        #Now cache the compiled regex patterns for this map
        all_patterns=[]
        for type,pattern_list in self._token_map.items():
            TOKEN_PATTERN=ru.list_to_regex(pattern_list)
            #print(f'RedactorTokenMap.redact(). token_patterns[{type}]={TOKEN_PATTERN}',file=sys.stderr)
            try:
                self._token_pattern[type]=ru.compile(TOKEN_PATTERN, self._flags, ru.EngineType.REGEX) 
                all_patterns.extend(pattern_list)
            except Exception as exc:
                print(f'WARNING. Invalid regular expression \'{TOKEN_PATTERN}\' built from the token map definitions in redactor class RedactorTokenMap for entity \'{type}\'.  This token map will be ignored.',file=sys.stderr)

        #print(f'RedactorTokenMap.redact(). all_patterns={all_patterns}',file=sys.stderr)
        self._all_patterns=ru.compile(ru.list_to_regex(all_patterns), self._flags, ru.EngineType.REGEX) 
        
    #Find any tokens that are in the token map and replace them with their canonical redaction tokens  
    def redact(self, texts, eCount, ids):
        new_texts = []
        for text, d_id in zip(texts,ids):
            new_text = str(text)
            #Check if there are any relevant patterns and only run the relatively costly map if there are:
            try:
                if ru.search(self._all_patterns,new_text,0,ru.EngineType.REGEX):  
                    for type,pattern in self._token_pattern.items():
                        #Replace all the matching expressions with a canonical redaction token
                        #We won't bother adding an index or incrementing the eCount becuase this is a generic match not a specific match.
                        if pattern is not None:
                            #print(f'RedactorTokenMap.redact(). TOKEN_PATTERN={pattern}',file=sys.stderr)
                            #Find all the existing entity labels in the string.
                            protect_zones=self.get_redactlabel_spans(new_text)

                            #Find the entities matching in the string
                            matches = list(pattern.finditer(new_text))
                            for e in reversed(matches): #reversed to not modify the offsets of other entities when substituting
                                matched_text = e.group()
                                start = e.span()[0]
                                end = start + len(matched_text)

                                #Check if we have matched part of an entity label, and add the redaction label if we are not.
                                is_overlapping,overlapped_label=self.overlaps_redactlabel_span(start,end,protect_zones)
                                if not is_overlapping:
                                    #Parameters: s, start, end, label, value, conversation_id, eCount):       
                                    c, eCount=self.insert_redactlabel_and_update_entities(matched_text, start, end, type, matched_text, d_id, eCount)

                    #if new_text != text: print(f'CHANGED: \'{text}\' => \'{new_text}\'')
            except Exception as e:
                print(f'WARNING: Ignoring error: {e} whilst matching string \'{str(new_text)}\'',file=sys.stderr)
                pass
           
            new_texts.append(new_text)

        return new_texts, eCount, ids