import sys
import yaml

class EntityRules():
    def __init__(self):
        self._rules={}

    def load_rulefile_yaml(self, filepath):
        '''Load a YAML rulefile to define the entities'''

        with open(filepath, "r") as stream:
            try:
                self._rules=yaml.safe_load(stream)
                print("RULES: ",str(self._rules))
            except yaml.YAMLError as exc:
                print(exc)

    def get_regexp(self, rulename):
        '''Return the regular expression associated with teh rulename'''
        regexp= self._rules["regexp"][rulename][0]
        print ("REGEXP:",regexp)
        return regexp