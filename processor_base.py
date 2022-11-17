import regex
import os

## ProcessorBase class and helper functions ##

# Base class from which all corpus processors are based.
class ProcessorBase():
    '''Construct a processor, pass entity_rules object that can provide general configuration for the processor.'''
    def __init__(self,id,entity_rules):
        self._entity_rules=entity_rules
        self._params={}
        self._id=id
     
    '''Virtual function defining what a configuration call should look like.'''
    # params: a dictionary of specific parameters that are relevant to this processor.
    def configure(self, params):
        self._params=params

    '''Virtual function defining what a processor should look look like'''
    def process(self,df):
        #A processor takes a set of conversation records as a pandas data frame, manipulates them and returns them.
        return df

    '''takes a path and returns the absolute path, depending on whether the input is relative or absolute. '''
    def absolute_path(self,path):
        if os.path.isabs(path):
            return path
        else:
            #Use REDACT_HOME if it is specified or use the location of the current file as the base if not.
            _homedir=os.getenv("REDACT_HOME")
            if (_homedir is None): 
                _homedir=os.path.dirname(os.path.realpath(__file__))
            return os.path.join(_homedir,path)

# Helper functions - These can be refactored as processors operating on the text field at a later date. 

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