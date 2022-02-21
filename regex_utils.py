import regex
import re
from enum import Enum

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

def compile(s,flags,etype):
    if etype==EngineType.REGEX:
        return regex.compile(s,flags)
    elif etype==EngineType.RE:
        return re.compile(s,flags)