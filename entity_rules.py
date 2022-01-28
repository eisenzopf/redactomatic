import yaml
import json
import redact
import regex
import sys

class EntityRules():
    def __init__(self):
        self._rules={}
        self._config={}
        self._level=2
        self._use_large=None

    @property
    def use_large(self):
        return self._use_large

    @use_large.setter  
    def use_large(self,value):
        self._use_large=value

    @property
    def level(self):
        return self._level

    @level.setter  
    def level(self,value):
        self._level=value

    @property  
    def entities(self):
        entities=self._config.get("level-"+str(self._level),[])
        return entities
        
    @property  
    def redaction_order(self):
        return self._config.get('redaction-order',[])

    @property  
    def anon_map(self):
        return self._config.get('anon-map',[])

    @property  
    def token_map(self):
        return self._config.get('token-map',[])  

    def load_configfile_json(self,filepath):
        print("Loading config file:",filepath)
        with open(filepath) as json_file:
            self._config=json.load(json_file)

    def load_rulefile_yaml(self, filepath):
        '''Load a YAML rulefile to define the entities'''
        print("Loading rule file:",filepath)

        with open(filepath, "r") as stream:
            try:
                self._rules=yaml.safe_load(stream)
                #print("RULES: ",str(self._rules))
            except yaml.YAMLError as exc:
                print(exc)

    def get_regexp(self, rulename):
        '''Return the regular expression associated with teh rulename'''
        regexp= self._rules["regexp"][rulename][0]
        #print ("REGEXP:",regexp)
        return regexp

    def get_redactor_model(self,label,modality):
        #print("get_redactor_model",label,modality)
        
        _entity_rule=self._rules.get("entities",None)
        if _entity_rule is None: 
            print("WARNING: No 'entities' section found in rules.",file=sys.stderr)
            return None
        
        _entity_label=_entity_rule.get(label,None)
        if _entity_label is None: 
            print("WARNING: Label",label," not listed in 'entities' in the rules.",file=sys.stderr)
            return None

        _redactor=_entity_label.get("redactor",None)
        if _redactor is None: 
            print("WARNING: Label 'redactor' is not listed for",label,"in 'entities' in the rules.",file=sys.stderr)
            return None
        
        _model_type=_redactor.get("model-type",None)
        if _model_type is None: 
            print("WARNING: Label 'model-type' is not listed in redactor section for ",label," in the rules.",file=sys.stderr)
            return None

        #Entities that are 'shared' are generated only by spacy and we return an empty model for them.
        if (_model_type == "shared"):
            return None

        #Get the model parameters for voice or text if they are specified.
        _model_params=_redactor.get(modality,None)

        if (_model_type == "spacy"):
            _model=redact.RedactorSpacy()
            _model.configure(use_large=self.use_large,entities=self.entities)
            return _model
    
        if (_model_type == "regexp"):
            if _model_params is None: 
                print("ERROR: No 'voice' or 'text' section found for ",label," in the for regexp model rules.",file=sys.stderr)
                return None

            _regexp_filename=_model_params.get("regexp-filename",None) 
            _regexp_id=_model_params.get("regexp-id",None)
            _group=_model_params.get("group",None)     
            if(_regexp_id is not None):
                _regexp=self.get_regexp(_regexp_id)
                _model=redact.RedactorRegexp()
                _model.configure(label,_regexp,_group or 1,regex.IGNORECASE)
                return _model
            
            if(_regexp_filename is not None):
                _model=redact.RedactorRegexpFromFile()
                _model.configure(label=label,filepath=_regexp_filename,group=_group or 1,flags=regex.IGNORECASE)
                return _model
            
        print("ERROR. model_type",str(_model_type),file=sys.stderr)
        