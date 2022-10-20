import regex
import re
from enum import Enum
import sys

class EngineType(Enum):
    RE               =0
    REGEX            =1

def to_engine_type(s):
    try:
        t=EngineType[s]
    except:
        raise NameError("Unrecognized regex engine type",name=s)
    return t

def flags_from_array(flist,etype):
    #flip a string to an array
    _flags = 0

    if not isinstance(flist,list):
        if isinstance(flist,str): flist=[flist]
        else: raise TypeError("ERROR: regular expression 'flag' values should be lists or single strings.")   

    for f in flist:
        _flags=_flags | flag_from_string(f,etype) 
    return _flags

def flag_from_string(s,etype):
    if etype==EngineType.REGEX:
        if (s=="ASCII" or s=="A"): return regex.ASCII	
        if (s=="IGNORECASE" or s=="I"): return regex.IGNORECASE
        if (s=="MULTILINE" or s=="M"): return regex.MULTILINE
        if (s=="DOTALL" or s=="S"): return regex.DOTALL
        if (s=="VERBOSE" or s=="X"): return regex.VERBOSE
        if (s=="LOCALE" or s=="L"): return regex.LOCALE
        else: return 0

    elif etype==EngineType.RE:
        if (s=="ASCII" or s=="A"): return re.ASCII	
        if (s=="IGNORECASE" or s=="I"): return re.IGNORECASE
        if (s=="MULTILINE" or s=="M"): return re.MULTILINE
        if (s=="DOTALL" or s=="S"): return re.DOTALL
        if (s=="VERBOSE" or s=="X"): return re.VERBOSE
        if (s=="LOCALE" or s=="L"): return re.LOCALE
        else: return 0

    else:
        return 0   #Can't happen

def recursive_sub(s,find,replace,flags,etype):
    input=s

    while True:
        if etype==EngineType.REGEX:
            output = regex.sub(find, replace, input)
        elif etype==EngineType.RE:
            output = re.sub(find, replace, input)

        if input == output:
            break
        else:
            input = output

    return output

def sub(s,find,replace,flags,etype):
    if etype==EngineType.REGEX:
        output = regex.sub(find, replace, s)
        if not output==s:
            print("FIXED:",s,"=>",output,file=sys.stderr)
    elif etype==EngineType.RE:
        output = re.sub(find, replace, s)

    return output

def compile(s,flags,etype):
    if etype==EngineType.REGEX:
        return regex.compile(s,flags)
    elif etype==EngineType.RE:
        return re.compile(s,flags)