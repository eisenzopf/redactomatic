import redact
import anonymize
import entity_map as em
import entity_rules as er
import entity_values as ev
import pandas as pd
import numpy as np
import os
import random
import argparse
import glob
import sys

def config_args(): # add --anonymize
    parser = argparse.ArgumentParser(description='Redactomatic v1.6. Redact call transcriptions or chat logs.')
    parser.add_argument('--column', type=int, required=True, help='the CSV column number containing the text to redact.')
    parser.add_argument('--idcolumn', type=int, required=True, help='the CSV column number containing the conversation ids.')
    parser.add_argument('--inputfile', nargs='+', required=True, help='CSV input files(s) to redact')
    parser.add_argument('--outputfile', required=True, help='CSV output files')
    parser.add_argument('--modality', required=True, choices=['text', 'voice'], help='the modality of the input file(s), either text or voice')
    parser.add_argument('--anonymize', action='store_true', help='include to anonymize redacted data')
    parser.add_argument('--large', action='store_true', help='use the spacy model trained on a larger dataset')
    parser.add_argument('--log', required=False, help='logs entities that have been redacted to separate file')
    parser.add_argument('--uppercase', required=False, action='store_true', help='converts all letters to uppercase')
    parser.add_argument('--level', default=2, required=False, help='sets the redaction level (1-3); default is 2')
    parser.add_argument('--noredaction', action='store_true', help='turn off redaction')
    parser.add_argument('--seed', type=int, required=False, help='a seed value for anonymization random selection; default is None i.e. truly random.',default=None)
    parser.add_argument('--rulefile', nargs="*", required=False, help='a list of YAML or JSON files containing definitions for entity rules; default is \'rules/*.yml\',\'rules/*.json\'')

    return parser.parse_args()

def df_load_files(args):
    dfs = []
    for file in args.inputfile:
        print("Loading " + file + "...")
        dfs.append(pd.read_csv(file))
    df = pd.concat(dfs, ignore_index=True)
    df.iloc[:, args.column-1].replace('', np.nan, inplace=True)
    df.dropna(axis='index',subset=[df.columns[args.column-1]], inplace=True)
    texts = df.iloc[:, args.column-1].tolist()
    ids = df.iloc[:, args.idcolumn-1].tolist()
    return df, texts, ids

def main():
     # get command line params and then initialize an empty rules base, passing these arguments to it.
    args = config_args()
    entity_rules = er.EntityRules(args)

    # load config.json into the entity rules base.   
    #entity_rules.load_configfile_json(os.getcwd() + '/config.json')

    #Load the config rules filess into the entity rules base. 
    #Use all relevant files in the rules directory if no globs are given.
    for g in args.rulefile or ['rules/*.yml','rules/*.json']:
        #print("GLOB:",g)
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

    entities=entity_rules.entities
    redaction_order=entity_rules.redaction_order
    anon_map=entity_rules.anon_map
    token_map=entity_rules.token_map
    
    #initialize entity map, entity_values.
    entity_map = em.EntityMap()
    entity_values = ev.EntityValues()

    # initialize the unique entity key
    curr_id = 0

    # load data into a Pandas Dataframe
    df, texts, ids = df_load_files(args)

    #If IGNORE isn't specified in the running order then add it first. This keeps backwards compatibility.
    if not "_IGNORE_" in redaction_order: redaction_order.insert(0,"_IGNORE_")
    if not "_IGNORE_" in entities: entities.insert(0,"_IGNORE_")
        
    #If SPACY isn't specified in the running order then add it last. This keeps backwards compatibility.
    if not "_SPACY_" in redaction_order: redaction_order.append("_SPACY_")
    if not "_SPACY_" in entities: entities.append("_SPACY_")
    
    #Get a list of the entities in the level specified on the command line ordered by the redaction_order.
    rule_order=[x for x in redaction_order if x in entities]

    #Now run redaction on the ordered list of redactors that are needed to meet the current redaction level.
    if not args.noredaction:
        print("Starting redaction at anonymization level:",entity_rules.level)

        for rule in rule_order:
            #Get the custom redactor model for this rule_label. (The redactor model will get the modality from the args if it is modality specific.)
            try:
                _model=entity_rules.get_redactor_model(rule)
                print("Redacting ",rule,"...")
                texts, entity_map, curr_id, ids, entity_values = _model.redact(texts, entity_map, curr_id, ids, entity_values)
            except(er.NotSupportedException) as e:
                print("Skipping ",rule,"...")

    #Put the text back that we do not want to allow to be redacted
    #texts = redact.replace_ignore(texts,entity_values)
   
    # clear the entity map.  It will be used the other way round for anonymization.
    entity_map=em.EntityMap()
    
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
            _model=entity_rules.get_anonomizer_model(rule)
            print("Anonymizing ",rule,"...")
            texts, entity_map=_model.anonymize(texts, ids, entity_map, entity_values)
        except(er.NotSupportedException) as e:
            print("Skipping ",rule,"...")

    # data cleanup
    texts = redact.clean(texts) # chats-yes, voice-yes

    if args.uppercase:
        texts = redact.convert_to_uppercase(texts)

    # write the redacted data back to the Dataframe
    df.iloc[:, args.column-1] = texts

    # write the updated CSV to disk
    df.to_csv(args.outputfile, index=False)

    # write audit log
    if args.log:
        filepath=os.getcwd() + "/" + args.log
        print("Writing log to " + filepath)
        entity_values.write_csv(filepath)

    print("Done. Output file is",args.outputfile)


if __name__ == "__main__":
    main()