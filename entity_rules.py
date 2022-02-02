import yaml
import json
import redact
import anonymize
import regex
import sys
from random import Random

# Exception classes for redactors
class EntityRuleConfigException(Exception):
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
        
        #Set up a shared randomizer for shared seeding.
        self._random = Random()
        if (self._args.seed is not None):
            print("Using fixed random seed: ",self._args.seed)
            self._random.seed(args.seed)

    @property
    def random(self):
        return self._random

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
        regex= self._rules["regex"][rulename]
        return regex

    def get_redactor_model(self,id):
        return self.get_model(id,"redactor")

    def get_anonomizer_model(self,id):
        return self.get_model(id,"anonymizer")
    
    def get_model(self,id,model_type):
        #Instantiate a model class and configure it with any parameters in the rules section for that model.
        #We find the type of class to create from the entity_rules then that object configures itself from the rules.
        _model_class=self.get_entityid_model_class(id,model_type)
            
        #Dynamically create and configure the model.
        #print("Creating dynamic class: ",str(_model_class))
        _model=get_class(_model_class)(id,self)
        _model_params=self.get_entityid_model_rule(id,model_type)
        #print("type:",type(_model).__name__)
        _model.configure(params=_model_params)
        return _model

    ### Fetch rule properties with specific exception support ###
    def get_entities_rule(self):
        '''return entity_rules(entites).'''         
        _rule=self._rules.get("entities",None)
        if _rule is None: raise EntityRuleCongfigException("WARNING: entity_rules(entities) not found in rules.")   
        return _rule  

    def get_entityid_rule(self,id):
        '''return entity_rules('entites.{id}).'''         
        _rule=self.get_entities_rule().get(id,None)
        if _rule is None: raise EntityRuleCongfigException("WARNING: entity_rules(entities."+id+") not found in rules.")
        return _rule

    def get_entityid_model_rule(self,id,model_type):
        '''return entity_rules('entites.{id}.{model_type}). Where {model_type}='redactor' or 'anonymizer'.'''            
        _rule=self.get_entityid_rule(id).get(model_type,None)
        if _rule is None: raise NotSupportedException("WARNING: entity_rules(entities."+id+"."+model_type+") not defined.")
        return _rule

    def get_entityid_model_class(self,id,model_type):
        '''return entity_rules('entites.{id}.{model_type}).model_class:'''
        _rule=self.get_entityid_model_rule(id,model_type).get("model-class",None)
        if _rule is None: raise EntityRuleCongfigException("WARNING: entity_rules(entities."+id+"."+model_type+".model-class) not defined.")
        return _rule


        