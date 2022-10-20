import regex

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