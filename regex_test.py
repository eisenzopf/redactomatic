import regex
import re
import pandas as pd
import regex_utils as ru
import entity_rules as er
from enum import Enum

class MatchType(Enum):
    ONE_OR_MORE_MATCH               =0
    ONE_OR_MORE_EXACT_MATCH         =1
    ONE_OR_MORE_PARTIAL_MATCH       =2
    ALL_EXACT_MATCH                 =3
    ALL_PARTIAL_MATCH               =4
    NO_MATCHES                      =5
    NO_EXACT_MATCHES                =6
    NO_PARTIAL_MATCHES              =7    

class RegexTest():
    def __init__(self, entity_rules):
        self._entity_rules=entity_rules

    def test_regex(self, report_filename):
        print ("Testing regular expressions...")
        _phrase_fail_count=0
        _test_fail_count=0
                
        #Prepare an empty data frame for the results.        
        df=pd.DataFrame(columns = ['regex_id', 'test_type','pass','group', 'ix', 'match','left','matched_text','right'])

        #Step through each regex-id in the regex-test section
        for _regex_id, _test_rule_set in self._entity_rules.regex_test_set.items():
            print("Testing ",_regex_id)
            #Step through each test rule for this regex-id
            for _test_rule in _test_rule_set:            
                _group=_test_rule.get("group",0)  
                _engine_type=ru.to_engine_type(_test_rule.get("engine","REGEX").upper())
                _match_type=MatchType[_test_rule.get("match-type","ONE_OR_MORE_MATCH").upper()]
                _flags=ru.flags_from_array(_test_rule.get("flags",["IGNORECASE"]),_engine_type)

                #Get the regex rules and make them a list
                _regex_set=self._entity_rules.get_regex_set(_regex_id)
 
                #compile the patterns with the designated regular expression engine..
                try:
                    _pattern_set = [ru.compile(r, _flags, _engine_type) for r in _regex_set]
                except Exception as exc:
                    raise Exception("ERROR: Failed to compile regex set for ':"+_regex_id+"' with error: "+str(exc))

                #now get the test sentences
                _test_phrases=_test_rule["phrases"]

                #Get the regex test module
                #_modulename=_test_rule["module"]

                #If the rule fails any sentences then the test for the whole rule fails.
                _test_pass=True   
                
                #Step through each test phrase in this test rule.
                for test_text in _test_phrases:
                    df_utt_result=pd.DataFrame()
                    #loop through the regex patterns and try to match at least one of them.
                    _exact_match_count=0
                    _partial_match_count=0
                    _match_count=0
                    _pattern_ix=0
                    for pattern in _pattern_set:
                        _pattern_ix+=1
                        matches = list(pattern.finditer(test_text))

                        for e in matches:  
                            #name=entity-text found by pattern
                            try:
                                _matched_text = e.group(_group)
                                _match_count +=1
                                
                                _start = e.start(_group)
                                _end= e.end(_group)
                                _matched_all=(_matched_text==test_text)
                                _left_text=test_text[:_start]
                                _right_text=test_text[_end:]
                                if (_matched_all): _exact_match_count+=1
                                else: _partial_match_count+=1

                                result={
                                    'regex_id':_regex_id,
                                    'group': _group,
                                    'ix' : _match_count,
                                    'match': "exact" if _matched_all else "partial",
                                    'test_text': test_text,
                                    'pattern_ix': _pattern_ix,
                                    'left' : _left_text,
                                    'matched_text' : _matched_text,
                                    'right' : _right_text
                                }
                            except:
                                result={
                                    'regex_id':_regex_id,
                                    'group': _group,
                                    'ix' : 0,
                                    'match': "group-not-matched",
                                    'test_text': test_text,
                                    'pattern_ix': _pattern_ix,
                                    'left' : "",
                                    'matched_text' : "",
                                    'right' : ""
                                }                                
                            #Add this match result to the data frame
                            df_utt_result=pd.concat([df_utt_result,pd.DataFrame(result,index=[0])])
                        if len(matches)==0:
                            result={
                                'regex_id':_regex_id,
                                'group': _group,
                                'ix' : 0,
                                'match': "none",
                                'test_text': test_text,
                                'pattern_ix': _pattern_ix,
                                'left' : "",
                                'matched_text' : "",
                                'right' : ""
                            }
                            df_utt_result=pd.concat([df_utt_result,pd.DataFrame(result,index=[0])])
                    
                    #Now work out if this utterance passed or failed the test, and add the result to all results for this utterance.
                    #print (_match_type,_exact_match_count,_partial_match_count,len(_pattern_set))
                    _phrase_test_pass=self.get_pass_fail(_match_type,_exact_match_count,_partial_match_count,len(_pattern_set))
                    df_utt_result["test_type"]=str(_match_type)                    
                    df_utt_result["pass"]=_phrase_test_pass
                    df=pd.concat([df,df_utt_result])

                    if (not _phrase_test_pass): 
                        print ("FAIL: regex-id: "+_regex_id +" => '"+str(test_text)+"' "+str(_match_type)+" "+str(_flags))
                        _test_pass=False
                        _phrase_fail_count +=1
                if not _test_pass:
                    _test_fail_count += 1

        #save the test results
        print("Saving test report to:",report_filename)
        df.to_csv(report_filename)

        if (_test_fail_count>0): print("FAIL: Regular expression test failed with "+str(_test_fail_count)+" broken rule(s) and "+str(_phrase_fail_count)+" non-matching phrase(s).")
        else: print("SUCCESS: Regular expression tests completed successfully.")
        
    def get_pass_fail(self,match_type,exact_match_count,partial_match_count,pattern_count):
        if match_type is MatchType.ONE_OR_MORE_MATCH:
            return (exact_match_count+partial_match_count)>0

        if match_type is MatchType.ONE_OR_MORE_EXACT_MATCH:
            return exact_match_count>0
        
        if match_type is MatchType.ONE_OR_MORE_PARTIAL_MATCH:
            return partial_match_count>0
        
        if match_type is MatchType.ALL_EXACT_MATCH:
            return pattern_count==exact_match_count        
        
        if match_type is MatchType.ALL_PARTIAL_MATCH:
            return pattern_count==partial_match_count      

        if match_type is MatchType.NO_MATCHES:
            return (exact_match_count+partial_match_count)==0  
        
        if match_type is MatchType.NO_EXACT_MATCHES:
            return exact_match_count==0        
        
        if match_type is MatchType.NO_PARTIAL_MATCHES:
            return partial_match_count==0      

