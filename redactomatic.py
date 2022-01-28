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
    parser.add_argument('--rulefile', nargs="*", required=False, help='a YAML file containing definitions for entity rules; default is data/core-rules.yaml')

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
    #initialize entity map and rules base
    entity_map = em.EntityMap()
    entity_rules = er.EntityRules()    
    entity_values = ev.EntityValues()

    # initialize list of entities we want to redact
    entities = []

    # unique entity key
    curr_id = 0
    
    # get command line params
    args = config_args()

    # set redaction level (default it set to 2 in the properties reader.)
    entity_rules.level=args.level 

    # set whether we want to use large or small ML models.
    # this could be moved to the model-definition files at a later date
    entity_rules.large=args.large

    # load config.json into the entity rules base.
    entity_rules.load_configfile_json(os.getcwd() + '/config.json')
    entities=entity_rules.entities
    redaction_order=entity_rules.redaction_order
    anon_map=entity_rules.anon_map
    token_map=entity_rules.token_map

    #Load the YAML rules files into the entity rules base. Use data/core-defs.yml if no rules files are given.
    for file in args.rulefile or [os.getcwd() + '/data/core-defs.yml']:
        print("Loading rulefile " + file + "...")
        entity_rules.load_rulefile_yaml(file)

    # load data into a Pandas Dataframe
    df, texts, ids = df_load_files(args)

    #Now run redaction on the ordered list of redactors that are needed to meet the current redaction level.
    if not args.noredaction:
        print("Starting redaction at anonymization level:",entity_rules.level)

        #If SPACY isn't specified in the running order then add it last. This keeps backwards compatibility.
        if not "_SPACY_" in redaction_order: redaction_order.append("_SPACY_")
        if not "_SPACY_" in entities: entities.append("_SPACY_")

        #Put the IGNORE step first unless it has been explicitly specified in the config file to be somewhere else.
        if not "_IGNORE_" in redaction_order: redaction_order.insert(0,"_IGNORE_")
        if not "_IGNORE_" in entities: entities.insert(0,"_IGNORE_")
            
        #Get a list of the entities in the desired level ordered by the redaction_order.
        rule_order=[x for x in redaction_order if x in entities]
        for redactor in rule_order:
            redactor_model=entity_rules.get_redactor_model(redactor,args.modality)
            if redactor_model is not None:
                print("Redacting ",redactor,"...")
                texts, entity_map, curr_id, ids, entity_values = redactor_model.redact(texts, entity_map, curr_id, ids, entity_values)
 
    #Put the text back that we do not want to allow to be redacted
    texts = redact.replace_ignore(texts,entity_values)
   
    # anonymize if flag was passed
    entity_map=em.EntityMap()
    if args.anonymize:
        #Seed the random number generator if determinism is required
        if (args.seed is not None):
            print("Using fixed random seed: ",args.seed)
            random.seed(args.seed)

        if "ADDRESS" in entities: texts, entity_map =   anonymize.address(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "CCARD" in entities: texts, entity_map =     anonymize.ccard(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "PHONE" in entities: texts, entity_map =     anonymize.phone(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "CARDINAL" in entities: texts, entity_map = anonymize.cardinal(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-no, voice=no   
        if "ORDINAL" in entities: texts, entity_map =   anonymize.ordinal(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "ZIP" in entities: texts, entity_map =       anonymize.zipC(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "ORG" in entities: texts, entity_map =       anonymize.company(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "PERSON" in entities: texts, entity_map =    anonymize.person(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "TIME" in entities: texts, entity_map =      anonymize.atime(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "DATE" in entities: texts, entity_map =      anonymize.adate(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "GPE" in entities: texts, entity_map =       anonymize.gpe(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "WORK_OF_ART" in entities: texts, entity_map = anonymize.work_of_art(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "LANGUAGE" in entities: texts, entity_map =  anonymize.language(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "EVENT" in entities: texts, entity_map =     anonymize.event(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "NORP" in entities: texts, entity_map =      anonymize.norp(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "MONEY" in entities: texts, entity_map =     anonymize.money(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "PERCENT" in entities: texts, entity_map =   anonymize.perc(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "SSN" in entities: texts, entity_map =       anonymize.ssn(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "EMAIL" in entities: texts, entity_map =     anonymize.email(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "PIN" in entities: texts, entity_map =       anonymize.pin(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes

        # These anonymizers are for spacy labels that we have anonymized to "[]" unless its a mislabeled match to another label
        if "LAUGHTER" in entities: texts, entity_map = anonymize.laughter(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "PRODUCT" in entities: texts, entity_map = anonymize.product(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "QUANTITY" in entities: texts, entity_map = anonymize.quantity(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "LAW" in entities: texts, entity_map = anonymize.law(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "FAC" in entities: texts, entity_map = anonymize.fac(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "LOC" in entities: texts, entity_map = anonymize.loc(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes

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