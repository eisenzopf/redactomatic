import yaml
import json
import regex
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
        raise Exception("ERROR: Unable to find classname:"+classname+" in module:"+modulename) from err

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
        _rules=self._rules.get("level",None)
        if _rules is None: raise EntityRuleConfigException("WARNING: entity_rules(level) not found in rules.")
        
        _entities=_rules.get(str(self.level),None)
        if _entities is None: raise EntityRuleConfigException("WARNING: entity_rules(level."+self.level+") not found in rules.")
        return _entities
        
    @property  
    def redaction_order(self):
        '''Return the redaction_order list set in the rules'''
        _item=self._rules.get('redaction-order',None)
        if _item is None: raise EntityRuleConfigException("WARNING: entity_rules(redaction_order) not found in rules.")
        return _item
    
    @property  
    def regex_test_set(self):
        '''Return a list of entities in the regex-test section of the rules.'''
        _item=self._rules.get('regex-test',None)
        if _item is None: raise EntityRuleConfigException("WARNING: entity_rules(regex-test) not found in rules.")
        return _item

    @property  
    def anon_map(self):
        '''Return the anon_map list fromt the rules'''
        _item= self._rules.get('anon-map',None)
        if _item is None: raise EntityRuleConfigException("WARNING: entity_rules(anon-map) not found in rules.")
        return _item

    @property  
    def token_map(self):
        '''Return the token_map list from the rules.  If not defined return an empty array. '''
        _item=self._rules.get('token-map',None)  
        if _item is None: raise EntityRuleConfigException("WARNING: entity_rules(token-map) not found in rules. Please add an empty token-map rule if you don't need any token mapping.")
        return _item

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

    def resolve_regex_includes(self,s):
        #extract the regexp ID for any text of the form: ?INCLUDE<one_to_9-voice>
        include_pattern=regex.compile('\?INCLUDE<(?<rule_id>([^>]*))>')
        e = regex.search(include_pattern,s)
        if (e is None):
            return s
        else: 
            _matched_rule_id = e.group("rule_id")
            _matched_include = e.group()
            _start = e.start()
            _end= e.end()
            _left_text=s[:_start]
            _right_text=s[_end:]
            _substitution_text=self.get_regex_set(_matched_rule_id)[0]
            regex_string=_left_text+_substitution_text+_right_text
            #print("REGEX:"+regex_string)

            #Recursively resolve inlcudes until we are all done.
            return self.resolve_regex_includes(regex_string)

    def get_regex_set(self, rulename):
        '''Return the regular expression associated with the rulename.  Process INCLUDEs of other rules.'''
        _regex_set= self._rules["regex"][rulename]

        #Make it a list if it isn't already.
        if isinstance(_regex_set,str): _regex_set=[_regex_set]
        if not isinstance(_regex_set,list): raise TypeError("ERROR: 'regex' rules should be lists or single strings.")   

        #Now parse each regex in the list to add in any includes.
        _regex_set=[self.resolve_regex_includes(r) for r in _regex_set]
        return _regex_set

    def get_redactor_model(self,id,entity_map, entity_values):
        return self.get_model(id,"redactor",entity_map, entity_values)

    def get_anonomizer_model(self,id,entity_map, entity_values):
        return self.get_model(id,"anonymizer",entity_map, entity_values)
    
    def get_model(self,id,model_type, entity_map, entity_values):
        #Instantiate a model class and configure it with any parameters in the rules section for that model.
        #We find the type of class to create from the entity_rules then that object configures itself from the rules.
        _model_class=self.get_entityid_model_class(id,model_type)
            
        #Dynamically create the model and return it,
        #print("Creating dynamic class: ",str(_model_class))
        _model=get_class(_model_class)(id,self)
        _model_params=self.get_entityid_model_rule(id,model_type)
        #print("type:",type(_model).__name__)
        _model.configure(_model_params, entity_map, entity_values)
        return _model

    ### Fetch rule properties with specific exception support ###
    def get_entities_rule(self):
        '''return entity_rules(entites).'''         
        _rule=self._rules.get("entities",None)
        if _rule is None: raise EntityRuleConfigException("WARNING: entity_rules(entities) not found in rules.")   
        return _rule  

    def get_entityid_rule(self,id):
        '''return entity_rules('entites.{id}).'''         
        _rule=self.get_entities_rule().get(id,None)
        if _rule is None: raise EntityRuleConfigException("WARNING: entity_rules(entities."+id+") not found in rules.")
        return _rule

    def get_entityid_model_rule(self,id,model_type):
        '''return entity_rules('entites.{id}.{model_type}). Where {model_type}='redactor' or 'anonymizer'.'''            
        _rule=self.get_entityid_rule(id).get(model_type,None)
        if _rule is None: raise NotSupportedException("WARNING: entity_rules(entities."+id+"."+model_type+") not defined.")
        return _rule

    def get_entityid_model_class(self,id,model_type):
        '''return entity_rules('entites.{id}.{model_type}).model_class:'''
        _rule=self.get_entityid_model_rule(id,model_type).get("model-class",None)
        if _rule is None: raise EntityRuleConfigException("WARNING: entity_rules(entities."+id+"."+model_type+".model-class) not defined.")
        return _rule


        