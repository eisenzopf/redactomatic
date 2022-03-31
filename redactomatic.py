from selectors import EpollSelector
from pyrsistent import v
import redact
import anonymize
import entity_map as em
import entity_rules as er
import entity_values as ev
import regex_test as rt
import pandas as pd
import numpy as np
import os
import random
import argparse
import glob
import sys
import csv

def config_args(): # add --anonymize
    parser = argparse.ArgumentParser(description='Redactomatic v1.6. Redact call transcriptions or chat logs.')
    parser.add_argument('--column', type=int, required=False, help='the CSV column number containing the text to redact.')
    parser.add_argument('--idcolumn', type=int, required=False, help='the CSV column number containing the conversation ids.')
    parser.add_argument('--inputfile', nargs='+', required=False, help='CSV input files(s) to redact')
    parser.add_argument('--outputfile', required=False, help='CSV output files')
    parser.add_argument('--modality', required=False, choices=['text', 'voice'], help='the modality of the input file(s), either text or voice')
    parser.add_argument('--anonymize', default=False, action='store_true', help='include to anonymize redacted data')
    parser.add_argument('--large', action='store_true', help='use the spacy model trained on a larger dataset')
    parser.add_argument('--log', required=False, help='logs entities that have been redacted to separate file')
    parser.add_argument('--uppercase', required=False, action='store_true', help='converts all letters to uppercase')
    parser.add_argument('--level', default=2, required=False, help='sets the redaction level (1-3); default is 2')
    parser.add_argument('--noredaction', default=False, action='store_true', help='turn off redaction')
    parser.add_argument('--seed', type=int, required=False, help='a seed value for anonymization random selection; default is None i.e. truly random.',default=None)
    parser.add_argument('--rulefile', nargs="*", required=False, help='a list of YAML or JSON files containing definitions for entity rules; default is \'rules/*.yml\',\'rules/*.json\'')
    parser.add_argument('--regextest', required=False, default=False, action='store_true', help='Test the regular rexpressions defeind in the regex-test rules prior to any other processing.')
    parser.add_argument('--testoutputfile', required=False, help='The file to save test results in.')
    parser.add_argument('--chunksize', required=False, default=100000, type=int, help='The number of lines to read before processing a chunk.(default = 100000)' )
    parser.add_argument('--header', default=False, action='store_true', help='Expect headers in the input files and print a header on the output. (default=False)')
    parser.add_argument('--columnname', type=str, default="text", help='The header name for the text; used if --header=True; overridden by --column; default is text')
    parser.add_argument('--idcolumnname', type=str, default="conversation_id", help='The header name for the conversation ID, used if --header=True; overridden by --idcolumn; default is text')

    #Check conditional required options.  
    _err_str=""
    _args=parser.parse_args()
    if ((_args.regextest) and (not _args.testoutputfile)) : _err_str="ERROR: The --regextest option requires the --testoutputfile option."
    
    if ( (not _args.noredaction) or _args.anonymize ):
        #Check that the required flags are there
        if (not _args.header):
            if (not _args.column): _err_str="ERROR: The --column option is required when --header is False."
            if (not _args.idcolumn): _err_str="ERROR: The --idcolumn option is required when --header is False."
        if (not _args.inputfile): _err_str="ERROR: The --inputfile option is required."
        if (not _args.outputfile): _err_str="ERROR: The --outputfile option is required."
    if _err_str:
        parser.error(_err_str)

    return _args

def process_chunk(df,curr_id, chunk,entity_values,entity_rules,redact_entity_map,anon_entity_map,args):
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

    df.iloc[:, args.column-1].replace(np.nan,'', inplace=True)
    texts = df.iloc[:, args.column-1].tolist()
    ids = df.iloc[:, args.idcolumn-1].tolist()

    entities=entity_rules.entities

    redaction_order=entity_rules.redaction_order
    #If IGNORE isn't specified in the running order then add it first. This keeps backwards compatibility.
    #if not "_IGNORE_" in redaction_order: redaction_order.insert(0,"_IGNORE_")
    #if not "_IGNORE_" in entities: entities.insert(0,"_IGNORE_")
        
    #If SPACY isn't specified in the running order then add it last. This keeps backwards compatibility.
    #if not "_SPACY_" in redaction_order: redaction_order.append("_SPACY_")
    #if not "_SPACY_" in entities: entities.append("_SPACY_")
    
    #Get a list of the entities in the level specified on the command line ordered by the redaction_order.
    rule_order=[x for x in redaction_order if x in entities]

    #Now run redaction on the ordered list of redactors that are needed to meet the current redaction level.
    if not args.noredaction:
        print("Starting redaction at anonymization level:",entity_rules.level)

        for rule in rule_order:
            #Get the custom redactor model for this rule_label. (The redactor model will get the modality from the args if it is modality specific.)
            try:
                _model=entity_rules.get_redactor_model(rule, redact_entity_map, entity_values)
                print("Redacting ",rule,"...")
                texts, curr_id, ids = _model.redact(texts, curr_id, ids)
            except(er.NotSupportedException) as e:
                print("Skipping ",rule,"...")

    #Set up for running the anonymizers.  
    if args.anonymize:
        #Run the anonymizers for the same targets as redaction (order doesn't matter)
        anon_order=rule_order
    else:
        # If no anonymization just run the special _IGNORE_ text restorer.
        anon_order=['_IGNORE_']

    #Now re-precess all the text and execute the associated anonumizers.
    for rule in anon_order:
        #Get the custom anonymizer model for this rule_label. 
        try:
            _model=entity_rules.get_anonomizer_model(rule, anon_entity_map, entity_values)
            print("Anonymizing ",rule,"...")
            texts=_model.anonymize(texts, ids)
        except(er.NotSupportedException) as e:
            print("Skipping ",rule,"...")

    # data cleanup
    texts = redact.clean(texts) # chats-yes, voice-yes

    if args.uppercase:
        texts = redact.convert_to_uppercase(texts)

    # write the redacted data back to the Dataframe
    df.iloc[:, args.column-1] = texts
    return curr_id

def main():
     # get command line params and then initialize an empty rules base, passing these arguments to it.
    args = config_args()
    entity_rules = er.EntityRules(args)

    #Load the config rules filess into the entity rules base. 
    #Use all relevant files in the rules directory if no globs are given.
    for g in args.rulefile or ['rules/*.yml','rules/*.json']:
        pathlist=glob.glob(g)
        #print("Pathlist:",pathlist)
        for file in pathlist:
            print("Loading rulefile " + file + "...")
            fname, fext = os.path.splitext(file)
            if (fext==".yml" or fext==".yaml"):
                entity_rules.load_rulefile_yaml(file)
            elif (fext==".json"):
                entity_rules.load_rulefile_json(file)

    #entity_rules.print_rulefile(sys.stderr)

    #Now run the regex tests if required
    if args.regextest:
        test= rt.RegexTest(entity_rules)
        test.test_regex(args.testoutputfile)

    #Continue if redaction or anonymization is needed.
    if ( (not args.noredaction) or args.anonymize ):
        #initialize entity maps.
        redact_entity_map = em.EntityMap()
        anon_entity_map=em.EntityMap()
        entity_values = ev.EntityValues()

        #Initialize some looping counts and an empty data frame.
        curr_id = 0
        chunk=0
        df=None

        for file in args.inputfile:
            print("Loading datafile " + file + "...")
            df_iter = pd.read_csv(file,chunksize=args.chunksize,header=(0 if args.header else None))
            for df in df_iter:
                curr_id=process_chunk(df,curr_id,chunk,entity_values,entity_rules,redact_entity_map,anon_entity_map,args)
                print("Writing outfile ",args.outputfile, "chunk ",chunk)
                if chunk==0: df.to_csv(args.outputfile, index=False, header=args.header)
                else: df.to_csv(args.outputfile, mode='a', header=False, index=False)
                chunk=chunk+1

        # write audit log
        if args.log:
            print("Writing logfile", args.log)
            entity_values.write_csv(args.log)

        print("Done.")

if __name__ == "__main__":
    main()