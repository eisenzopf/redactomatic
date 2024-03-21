import pandas as pd
import numpy as np
import argparse
import processor_base as pb
import entity_map as em
import entity_rules as er
import entity_values as ev
import regex_test as rt
import sys
import os
import traceback
import redact

def __version__():
    return "1.22"
    
TOKENMAP_RULENAME="_TOKEN_MAP_"

def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in {'false', 'f', '0', 'no', 'n'}:
        return False
    elif value.lower() in {'true', 't', '1', 'yes', 'y'}:
        return True
    raise ValueError(f'{value} is not a valid boolean value')

def config_args(): # add --anonymize
    parser = argparse.ArgumentParser(description='Redact call transcriptions or chat logs.')
    parser.add_argument('--column', type=int, required=False, help='the CSV column number containing the text to redact.')
    parser.add_argument('--idcolumn', type=int, required=False, help='the CSV column number containing the conversation ids.')
    parser.add_argument('--inputfile', nargs='+', required=False, help='CSV input files(s) to redact')
    parser.add_argument('--outputfile', required=False, help='CSV output files')
    parser.add_argument('--modality', required=False, choices=['text', 'voice'], help='the modality of the input file(s), either text or voice')
    parser.add_argument('--redact', action='store_true', default=True, help='turn on redaction (default=true)')
    parser.add_argument('--no-redact',   dest='redact', action='store_false', help='turn off redaction')
    parser.add_argument('--noredaction', action='store_true', help='DEPRECATED. turn off redaction')
    parser.add_argument('--anonymize', action='store_true', default=False, help='turn on anonymization')
    parser.add_argument('--no-anonymize', dest='anonymize', action='store_false', help='turn off anonymization (default)')
    parser.add_argument('--defaultrules', action='store_true', default=True, help='Load the default rules. Use --rules to specify additional rules. (default=true)')
    parser.add_argument('--no-defaultrules', dest='defaultrules',  action='store_false', help='Do not load the default rules.  Use --rules to specify all rules.')
    parser.add_argument('--large', action='store_true', help='use the spacy model trained on a larger dataset')
    parser.add_argument('--log', required=False, help='logs entities that have been redacted to separate file')
    parser.add_argument('--uppercase', required=False, action='store_true', help='converts all letters to uppercase')
    parser.add_argument('--level', default=2, required=False, help='The redaction level. Choose 1,2, or 3 or a any custom level. Default is 2')
    parser.add_argument('--seed', type=int, required=False, default=None, help='a seed value for anonymization random selection; default is None i.e. truly random.')
    parser.add_argument('--rulefile', nargs="*", required=False, default=[], help='A list of filenames defining custom rules in YML or JSON. Add to or override default rules (see --defaultrules).  These are globbable.')
    parser.add_argument('--regextest', required=False, default=False, action='store_true', help='Test the regular rexpressions defeind in the regex-test rules prior to any other processing.')
    parser.add_argument('--testoutputfile', required=False, help='The file to save test results in.')
    parser.add_argument('--chunksize', required=False, default=100000, type=int, help='The number of lines to read before processing a chunk.(default = 100000)' )
    parser.add_argument('--chunklimit', required=False, default=None, type=int, help='The number of chunks to run before stopping (used primarily for benchmarking).' )
    parser.add_argument('--header', default=False, action='store_true', help='Expect headers in the input files and print a header on the output. (default=False)')
    parser.add_argument('--columnname', type=str, default="text", help='The header name for the text; used if --header=True; overridden by --column; default is text')
    parser.add_argument('--idcolumnname', type=str, default="conversation_id", help='The header name for the conversation ID, used if --header=True; overridden by --idcolumn; default is text')
    parser.add_argument('--traceback', action='store_true', default=False, help='Give traceback information when an error is thrown (default=False)')
    parser.add_argument('-v','--verbose', action='store_true', default=True, help='Print progress of redaction to standard output as it occurs. Does not affect stderr. (default=True)')
    parser.add_argument('--no-verbose',   dest='verbose', action='store_false', help='Turn off --verbose')

    #version
    parser.add_argument('--version', action='version', help='Print the version', version=f'redactomatic {__version__()}')

    #Check conditional required options.  
    _err_list=[]
    _args=parser.parse_args()

    #Check special regex test mode.
    if ((_args.regextest) and (not _args.testoutputfile)) : _err_list.append("ERROR: The --regextest option requires the --testoutputfile option.")
    
    #warn with deprecated --noredaction option
    if (_args.noredaction):
        _err_list.append("ERROR: The --noredaction option is no longer supported. Use --no-redact instead.")
        _args.redact=False

    #If we are going to run any redactors or anonymizers then enforce other command line switches.
    if (_args.redact or _args.anonymize):
        #Check that the required flags are there
        if (not _args.header):
            if (not _args.column): _err_list.append("ERROR: The --column option is required when --header is False.")
            if (not _args.idcolumn): _err_list.append("ERROR: The --idcolumn option is required when --header is False.")
        if (not _args.inputfile): _err_list.append("ERROR: The --inputfile option is required.")
        if (not _args.outputfile): _err_list.append("ERROR: The --outputfile option is required.")
        if (not _args.modality): _err_list.append("ERROR: The --modality option is required.")
    if _err_list:
        parser.error("\n".join(_err_list))

    return _args

class RedactomaticProcessor(pb.ProcessorBase):
    def __init__(self,id,entity_rules):
        self._curr_id = 0
        self._redact_entity_map = em.EntityMap()
        self._anon_entity_map=em.EntityMap()
        self._entity_values = ev.EntityValues()
        super().__init__(id, entity_rules)    


    def process(self,df):
        #Check if we need to set column and idcolumn.
        #Note that we currently don't police that that files have the same headers and columns.
        #Behaviour is not guaranteed if they do not.
        if (args.header):
            try: 
                if (args.column is None): args.column=df.columns.get_loc(args.columnname)+1
            except: raise KeyError("The essential text field '"+args.columnname+"' was not found in the input file.")
            try: 
                if (args.idcolumn is None): args.idcolumn=df.columns.get_loc(args.idcolumnname)+1
            except: raise KeyError("The essential ID field '"+args.idcolumnname+"' was not found in the input file.")

        #df.iloc[:, args.column-1].replace(np.nan,'', inplace=True)
        
        df.fillna({args.column-1:''}, inplace=True)
        texts = df.iloc[:, args.column-1].tolist()
        ids = df.iloc[:, args.idcolumn-1].tolist()

        #get the entities to be redacted and anonymized. Make sure the token map default rule is added if there is a token map and its not in the list.
        entities=self._entity_rules.entities
        if (TOKENMAP_RULENAME not in entities): entities[:0]=[TOKENMAP_RULENAME] 

        #Now run redaction on the ordered list of redactors that are needed to meet the current redaction level.
        redaction_order=self._entity_rules.redaction_order
        redaction_order[:0] = [i for i in self._entity_rules.always_redact if i not in redaction_order]
        if args.verbose: print(f'redaction_order = {redaction_order}',file=sys.stderr)

        if args.redact:
            #Get a list of the entities in the level specified on the command line ordered by the redaction_order.
            redaction_order=[x for x in redaction_order if x in entities]
        else:
            redaction_order=self._entity_rules.always_redact

        #Terminate with error message if any entities are not in the redaction_order
        missing_entities=[x for x in entities if not x in self._entity_rules.redaction_order]
        if len(missing_entities)>0:
            raise Exception(f'ERROR: The following entities are not defined in the redaction_order: {missing_entities}')

        if (args.verbose): print("Starting redaction at anonymization level:",self._entity_rules.level)

        for rule in redaction_order:
            #Get the custom redactor model for this rule_label. (The redactor model will get the modality from the args if it is modality specific.)
            try:
                _model=self._entity_rules.get_redactor_model(rule, self._redact_entity_map, self._entity_values)
                if (args.verbose): print("Redacting ",rule,"...")
                texts, self._curr_id, ids = _model.redact(texts, self._curr_id, ids)
            except(er.NotSupportedException) as e:
                if (args.verbose): print("Skipping ",rule,"...")

        #Set up for running the anonymizers.  
        if (args.anonymize): 
            anonymization_order=[x for x in self._entity_rules.anonymization_order if x in entities]
        else:
            anonymization_order=[x for x in self._entity_rules.anonymization_order if x in self._entity_rules.always_anonymize]
        
        if args.verbose: print(f'anonymization_order = {anonymization_order}',file=sys.stderr)

        #Now re-precess all the text and execute the associated anonumizers.
        for rule in anonymization_order:
            #Get the custom anonymizer model for this rule_label. 
            try:
                _model=self._entity_rules.get_anonomizer_model(rule, self._anon_entity_map, self._entity_values)
                if (args.verbose): print("Anonymizing ",rule,"...")
                texts=_model.anonymize(texts, ids)
            except(er.NotSupportedException) as e:
                if (args.verbose): print("Skipping ",rule,"...")

        # data cleanup
        if (args.verbose): print("Cleaning text (Regex)...")
        texts = pb.clean(texts) # chats-yes, voice-yes

        if args.uppercase:
            texts = pb.convert_to_uppercase(texts)
            if (args.verbose): print("Converting letters to uppercase...")

        # write the redacted data back to the Dataframe
        df.iloc[:, args.column-1] = texts

    def write_log(self,file):
        self._entity_values.write_csv(file)

def main(args):
    #Initialize an empty rules base and pass the args namespace to it.
    #Load the config rules files (use all files in the rules directory if no globs are given.)
    entity_rules = er.EntityRules(args)
    #print(f'{args}')

    #Generate an array of rulesfile expressions using the default ones and/or any specified on the command line.
    if args.defaultrules:
        default_rules_dir= os.path.dirname(os.path.abspath(__file__))+"/rules"
        rulefiles=[default_rules_dir+'/*.yml',default_rules_dir+'/*.yaml',default_rules_dir+'/*.json'] + args.rulefile
    else:    
        rulefiles=args.rulefile

    if (entity_rules.load_rule_globlist(rulefiles) ==0):
        raise Exception("ERROR. No rulesfiles loaded.")

    #Now add in a special token mapper if there is a token-map defined (would like to deprecate this later).
    token_map_config={
        "entities": {
            TOKENMAP_RULENAME : {
                "redactor": {
                    "model-class": "redact.RedactorTokenMap",
                    "text": {
                        "token-map": entity_rules.token_map
                    },
                    "voice": {
                        "token-map": entity_rules.token_map
                    }
                }
            }
        }
    }

    #Now merge the rules into the configuration. Note that if there is a _TOKEN_MAP already defined then it will simply be merged with this one.  This is ok.
    entity_rules.merge_rules(token_map_config)
    #print(f'Created _TOKEN_MAP_: {entity_rules.get_entityid_rule(TOKENMAP_RULENAME)}',file=sys.stderr)

    #Now run the regex tests if required
    if args.regextest:
        test= rt.RegexTest(entity_rules)
        test.test_regex(args.testoutputfile)

    #Continue if redaction or anonymization is needed.
    if ( args.redact or args.anonymize ):
        #Initialize some looping counts and an empty data frame.
        chunk=0
        df=None

        ##initialise and configure the redactomatic processor
        redactomatic=RedactomaticProcessor("redactomatic",entity_rules)
        redactomatic.configure(None)

        for file in args.inputfile:
            if (args.verbose): print("Loading datafile " + file + "...")
            df_iter = pd.read_csv(file,chunksize=args.chunksize,header=(0 if args.header else None),dtype=str, keep_default_na=False)
            for df in df_iter:
                redactomatic.process(df)
                if (args.verbose): print("Writing outfile ",args.outputfile, "chunk ",chunk)
                if chunk==0: df.to_csv(args.outputfile, index=False, header=args.header)
                else: df.to_csv(args.outputfile, mode='a', header=False, index=False)
                
                #Quit if the chunklimit has been reached.
                if (args.chunklimit is not None) and (chunk+1>=args.chunklimit):
                    if (args.verbose): print(f"QUIT. chunklimit reached:{args.chunklimit}\n")
                    break

                chunk=chunk+1

        # write audit log
        if args.log:
            if (args.verbose): print("Writing logfile", args.log)
            redactomatic.write_log(args.log)

        if (args.verbose): print("Done.")

if __name__ == "__main__":
    # get command line params.
    args = config_args()
    try:
        main(args)
    except Exception as e:
        print(f"ERROR. Terminating redactomatic with error: {e}",file=sys.stderr)
        if args.traceback:
            traceback.print_exc(file=sys.stderr)
