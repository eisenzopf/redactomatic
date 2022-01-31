import yaml
import json
import redact
import regex
import sys

# Exception classes for redactors
class EntityRuleCongfigException(Exception):
    pass

class ModalityNotSupportedException(Exception):
    pass

#Helper function to merge config files as they are
def merge(source, destination):
    """
    Deep merge two dictionaries

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
            #print("key:",key,"value",value,"node",node,file=sys.stderr)
        else:
            destination[key] = value

    return destination

class EntityRules():
    def __init__(self, args):
        self._rules={}
        self._args=args

    @property
    def level(self):
        '''Return the current level set in the args.'''
        return self._args.level

    @property  
    def entities(self):
        '''Return the entities list defined in the 'level-{level} section in the rules.'''
        entities=self._rules.get("level-"+str(self.level),[])
        return entities
        
    @property  
    def redaction_order(self):
        '''Return the redaction_order list set in the rules'''
        return self._rules.get('redaction-order',[])

    @property  
    def anon_map(self):
        '''Return the anon_map list fromt the rules'''
        return self._rules.get('anon-map',[])

    @property  
    def token_map(self):
        '''Return the token_map list from the rules'''
        return self._rules.get('token-map',[])  

    @property  
    def args(self):
        '''return the args object.'''
        return self._args

    def load_rulefile_json(self,filepath):
        '''Load a JSON rulefile to define the entities'''
        #print("Loading config file:",filepath)
        with open(filepath) as stream:
            try:
                _new_rules=json.load(stream)
                self._rules=merge(self._rules,_new_rules)
                #print("RULES: ",str(self._rules))    
            except Exception as e:
                raise(e)

    def load_rulefile_yaml(self, filepath):
        '''Load a YAML rulefile to define the entities'''
        #print("Loading rule file:",filepath)

        with open(filepath, "r") as stream:
            try:
                _new_rules=yaml.safe_load(stream)
                self._rules=merge(self._rules,_new_rules)
                #print("RULES: ",str(self._rules))    
            except yaml.YAMLError as e:
                raise(e)

    def print_rulefile(self,f):
        print(self._rules,file=f)

    def get_regex(self, rulename):
        '''Return the regular expression associated with the rulename'''
        regex= self._rules["regex"][rulename][0]
        #print ("regex:",regex)
        return regex

    def get_redactor_model(self,id):
        #print("get_redactor_model",id,modality)
        
        _entity_rule=self._rules.get("entities",None)
        if _entity_rule is None: 
            raise EntityRuleCongfigException("WARNING: No 'entities' section found in rules.")
        
        _specific_entity=_entity_rule.get(id,None)
        if _specific_entity is None: 
            raise EntityRuleCongfigException("WARNING: Entity ",id," not listed in 'entities' in the rules.")

        _redactor_params=_specific_entity.get("redactor",None)
        if _redactor_params is None: 
            raise EntityRuleCongfigException("WARNING: No 'redactor' specified for: "+id+" the rules.")
        
        _model_type=_redactor_params.get("model-type",None)
        if _model_type is None: 
            raise EntityRuleCongfigException("WARNING: Label 'model-type' is not listed in redactor section for "+id+" in the rules.")

        #Instantiate a model class and configure it with any parameters in the rules section for that model.
        #Models get a reference to this entity_rules object so they use it to configure themselves. (e.g. find rules defs in other parts of the configuration.)
        #Entities that are 'shared' are generated only by spacy and we return an empty model for them.
        if (_model_type == "shared"): return None
        elif (_model_type == "spacy"): _model=redact.RedactorSpacy(id,self)
        elif (_model_type == "regex"): _model=redact.RedactorRegex(id,self)
        elif (_model_type == "phraselist"): _model=redact.RedactorPhraseList(id,self)
        else:
            raise EntityRuleCongfigException("Undefined model_type: ",str(_model_type))

        #Configure the model.  
        try:
            _model.configure(_redactor_params)
        except(ModalityNotSupportedException) as e:
            print("Skipping: "+id)
            _model=None

        return _model

        
        