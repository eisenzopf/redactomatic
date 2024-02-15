import pandas as pd
import regex
import sys
import inflect
import entity_rules as er
import regex_utils as ru
import processor_base as pb
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
class AnonymizerBase(pb.ProcessorBase):
    '''Construct a redactor, pass command line arguments that can affect the behaviour of the redactor.'''
    def __init__(self,id,entity_rules):
        self._entity_map=None
        self._entity_values=None
        super().__init__(id, entity_rules)

    '''Virtual prototype for configuring an anonymizer with a specific set of parameters.'''
    def configure(self, params,entity_map, entity_values):
        super().configure(params)
        self._entity_map=entity_map
        self._entity_values=entity_values

    #Implement the generic processor rule.  
    def process(self,df):
        #This is currently not defined and will throw an exception.
        #In the future this would call or replace anonymize() by converting the dataframe to a text and id array.
        raise NotImplementedError

    '''Anonymization function. '''
    def anonymize(self, texts, conversation_ids):
        new_texts = []
            
        #Get a regex to match any entities to be replaced (if any).
        this_regex = self.anon_regex(self._id)
        if this_regex!="":
            for text,id in zip(texts,conversation_ids):
                new_text = regex.sub(this_regex,lambda x: self.callback(x,id), text)
                new_texts.append(new_text)
        return new_texts

    '''Virtual function for callback to support anonymize().  Override this function to return the new value for the anonymized entity.'''
    def callback(self, match, i):
        tag = match.group()
        return self.persist_entity_value(i,tag,"")

    def persist_entity_value(self, id, tag, entity_value):
        #Look for tags of the form '[ENTITY-dddd]' where dddd is an integer identifier for the entity.
        #The enclosing [ ] are optional so this function also works with tags of the form 'ENTITY-dddd'.
        #If this exists then we look whether we have seen something of type 'ENTITY' with this id and index previously.
        #If we have then use that value otherwise use the value we were given and remember it for later calls.
        #If the tag does not match the pattern then just return the value we were given.

        this_match = regex.fullmatch(r'\[?(.*)-(.*?)\]?', tag)

        if (this_match and self._params.get("persist",True)):   # handling for ENTITY-dddd tags    
            m_ix=this_match[2]
            m_cat=this_match[1]
            r=self._entity_map.update_entities(m_ix, id, entity_value, m_cat)
        else:
            r=entity_value
        return r
        
    '''create a regular expression which matches an entity label of the type specified.  Includes anon_map and token_map definitions as well.'''
    def anon_regex(self, type):
        anon_map=self._entity_rules.anon_map
        token_map=self._entity_rules.token_map

        counter=0
        this_regex=r''
        if type in anon_map.keys():
            for entity in anon_map[type]:
                if (counter>0): this_regex=this_regex+'|' 
                this_regex = this_regex + r'\[' + entity + r'(-\d+)?\]'
                counter+=1
        if type in token_map.keys():
            for entity in token_map[type]:
                if (counter>0): this_regex=this_regex+r'|' 
                this_regex = this_regex + entity
                counter+=1

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

    def configure(self, params, entity_map, entity_values):
        #Call the base class configurator.
        super().configure(params, entity_map, entity_values)

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
            _regex_set=self._entity_rules.get_regex_set(_regex_id)
        elif (_regex_filename is not None):
            #IMPLEMENT THIS!
            raise er.EntityRuleConfigException("ERROR: regex-filename is not yet supported.")
        elif (_regex is not None):
            _regex_set=_regex
        else:
            raise er.EntityRuleConfigException("ERROR: No valid regex defined in rule: "+str(self._id))

        self._flags=ru.flags_from_array(_model_params.get("flags",[]),ru.EngineType.RE)
        
        try:
            self._pattern_set = [ru.compile(r, self._flags, ru.EngineType.RE) for r in _regex_set]
        except Exception as exc:
            print("WARNING: Failed to compile regex set for ':"+self._id+"' with error: "+str(exc),file=sys.stderr)

    def callback(self, match, i):
        #If there are multiple regexps in a list, then pick one at random.
        pattern=self.random.choice(self._pattern_set)
        anon_string= self._xeger.xeger(pattern)
        #print ("pattern:",pattern,"string:",anon_string)
        tag = match.group()
        return self.persist_entity_value(i,tag,anon_string)

class AnonRestoreEntityText(AnonymizerBase):
    '''Class to replace an anonymization token with the original text that was redacted in order to restore the original text.'''
    def anonymize(self, texts, conversation_ids):
        #If there are no entity values to restore then print a simple abort message ard return.
        #This deals with the situation where anonymization of a set of IGNORE items is being attempted without the --redact option set.
        if (self._entity_values.is_empty()):  
            if (self._entity_rules.args.verbose):  print(f'Aborting  {self._id} ...')
            return texts

        new_texts = []
        pattern = regex.compile(r'(\[('+self._id+'\-\d+)\])')

        for text in texts:
            matches = list(pattern.finditer(text))
            newString = text
            for e in reversed(matches):
                name = e.group(2)
                start = e.span()[0]
                end = start + len(e.group())
                try:
                    newString = newString[:start] + self._entity_values.get_value(name) + newString[end:]
                except Exception as exc:
                    #Warn that there is no restoration data for this entity and continue.
                    print(f'WARNING: entity {name} has no restoration data.',file=sys.stderr)
                    newString = newString[:start] + "["+name+"]" + newString[end:]
                   
            new_texts.append(newString)
        return new_texts

class AnonNullString(AnonymizerBase):
    '''Class does nothing. Same as base class but called explicitly so that it is clear that nothing is being done.'''
    pass

### Custom anonymization classes for specific entity types ###

class AnonPhraseList(AnonymizerBase):
    '''Construct a redactor, pass command line arguments that can affect the behaviour of the redactor.'''
    def __init__(self,id,entity_rules):
        self._phrase_list_set=[]
        super().__init__(id, entity_rules)
     
    '''Virtual prototype for configuring an anonymizer with a specific set of parameters.'''
    def configure(self, params, entity_map, entity_values):
        #Call the base class configurator.
        super().configure(params, entity_map, entity_values)

        #Get params.voice or params.text if they are specified.
        _model_params=params.get(self._entity_rules.args.modality,None)
        #If the paramters do not contain a definition for the current modality then raise a NotSupported exception.
        if _model_params is None: 
            raise er.NotSupportedException("Modality: "+str(self._entity_rules.args.modality)+" not supported for anonymizer id: "+self._id)

        #Create a list of rules. If there is only one dictionary in there then treat it as a list of one.
        #This is a syntactic convenience that allows users to not bother creating lists of one dictionary.
        if isinstance(_model_params,dict):
            _phrase_rules=[ _model_params.copy() ]
        else:
            _phrase_rules= _model_params

        for _phrase_rule in _phrase_rules:
            #Get the possible parameters
            _phrase_filename=_phrase_rule.get("phrase-filename",None)   
            _phrase_field=_phrase_rule.get("phrase-field",None)
            _phrase_column=_phrase_rule.get("phrase-column",0)
            _phrase_header=_phrase_rule.get("phrase-header",True)
            _phrase_list=_phrase_rule.get("phrase-list",None)   

            #Load the phrase list depending on how it is specified.
            if (_phrase_list is None) and  (_phrase_filename is not None):
                if _phrase_header is None:  _df = pd.read_csv(self.absolute_path(_phrase_filename), Header=None)
                else: _df = pd.read_csv(self.absolute_path(_phrase_filename),)
                if _phrase_field is None:
                    _phrase_list=(_df.iloc[:,_phrase_column]).to_list()
                else:
                    _phrase_list=_df[_phrase_field].to_list()
            
            #If the list is ok then add it to the phrase list set.
            if (not isinstance(_phrase_list,list)) or len(_phrase_list)==0:
                raise er.EntityRuleConfigException("ERROR: Invalid or empty phrase list rule for entity: "+str(self._id))
            self._phrase_list_set.append(_phrase_list)

    #Choose a random item from each phrase list and concatenate them in order.
    def callback(self, match, i):
        phrase=""
        for phrase_list in self._phrase_list_set:
            phrase = phrase + str(self.random.choice(phrase_list))
        tag = match.group()
        return self.persist_entity_value(i,tag,phrase)

class AnonAddress(AnonPhraseList):
    def callback(self,match, i):
        street = str(self.random.choice(self._phrase_list_set[0]))
        if self._entity_rules.args.modality == 'text':
            number = str(self.random.randrange(100,500))
        else:
            number = inflector.number_to_words(self.random.randrange(100,500))
        address = number + " " + street + " "

        tag = match.group()
        return self.persist_entity_value(i,tag,address)

class AnonZipC(AnonPhraseList):
    def callback(self, match, i):
        if self._entity_rules.args.modality == 'text':
            zipC = str(self.random.choice(self._phrase_list_set[0]))
        else:
            zipC = digits2words(str(self.random.choice(self._phrase_list_set[0])))
        tag = match.group()
        return self.persist_entity_value(i,tag,zipC)

class AnonPhone(AnonymizerBase):
    def callback(self, match, i):
        area_code = str(self.random.randrange(200,999))
        exchange = str(self.random.randrange(200,999))
        number = str(self.random.randrange(1000,9999))
        if self._entity_rules.args.modality == 'text':
            phone = area_code + "-" + exchange + "-" + number
        else:
            phone = digits2words(str(area_code + exchange + number))
        tag = match.group()
        return self.persist_entity_value(i,tag,phone)

class AnonSSN(AnonymizerBase):
    def callback(self, match, i):
        first = str(self.random.randrange(200,999))
        second = str(self.random.randrange(10,99))
        third = str(self.random.randrange(1000,9999))
        if self._entity_rules.args.modality == 'text':
            ssn = first + "-" + second + "-" + third
        else:
            ssn = digits2words(str(first + second + third))
        tag = match.group()
        return self.persist_entity_value(i,tag,ssn)
