import yaml
import json
import redact
import anonymize
import regex
import sys

# Exception classes for redactors
class EntityRuleCongfigException(Exception):
    pass

class NotSupportedException(Exception):
    pass


def get_class(classpath):
    '''Take a string of the form module.class and return the actual class object.'''
    try:
        modulename,classname=classpath.split('.')
        module = __import__(modulename)
        class_ = getattr(module, classname)
        return class_
    except Exception as err:
        raise Exception("ERROR: Unable to find classname:"+classname+"in module:"+modulename) from err

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
        return self.get_model(id,"redactor")

    def get_anonomizer_model(self,id):
        return self.get_model(id,"anonymizer")

    def get_model(self,id,model_type):
        #model_type="redactor","anoymizer"
        #print("get_model",id,model_type)
        
        _entity_rule=self._rules.get("entities",None)
        if _entity_rule is None: 
            raise EntityRuleCongfigException("WARNING: No 'entities' section found in rules.")
        
        _specific_entity=_entity_rule.get(id,None)
        if _specific_entity is None: raise EntityRuleCongfigException("WARNING: Entity ",id," not listed in 'entities' in the rules.")

        _model_params=_specific_entity.get(model_type,None)
        if _model_params is None: 
            raise NotSupportedException("WARNING: No '"+model_type+"' specified for: "+id+" the rules.")
        
        #Instantiate a model class and configure it with any parameters in the rules section for that model.
        #Models get a reference to this entity_rules object so they use it to configure themselves. (e.g. find rules defs in other parts of the configuration.)
        _model_class=_model_params.get("model-class",None)
        if _model_class is None: raise EntityRuleCongfigException("WARNING: Label 'model-class' is not listed in '"+model_type+"' section for "+id+" in the rules.")
        
        #Dynamically create a model
        #print("Creating dynamic class: ",_model_class)
        _model=get_class(_model_class)(id,self)

        #Configure the model.  
        try:
            _model.configure(_model_params)
        except(NotSupportedException) as e:
            raise NotSupportedException("WARNING: configuration failed for '"+model_type+"' specified for: "+id+" the rules.")

        return _model

        