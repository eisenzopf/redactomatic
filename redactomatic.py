import redact
import anonymize
import pandas as pd
import numpy as np
import os

def main():
    #initialize entity map
    entity_map = {} 

    # initialize entity value dict
    entity_values = {}

    # initialize list of entities we want to redact
    entities = []

    # unique entity key
    curr_id = 0

    # load names file
    names = pd.read_csv(os.getcwd() + '/data/baby-names.csv')
    
    # get command line params
    args = redact.config_args()

    # set default redaction level to 2
    if bool(args.level) == False:
        args.level = 2

    # validate command line params
    if args.modality == "text":
        pass
    elif args.modality == "voice":
        pass
    else:
        print("--modality command line value must be either text or voice")
        exit()

    # get list of entities to redact from config.json
    entities, redaction_order, anon_map, token_map = redact.load_config(args.level)

    # load data into a Pandas Dataframe
    df, texts, ids = redact.df_load_files(args)

    # first pass replaces text phrases that should be ignored and stored them in entity_values
    texts, entity_map, curr_id, entity_values  = redact.ignore_phrases(texts, entity_map, curr_id, ids, entity_values)

    if args.noredaction:
        pass
    else:
        for redactor in redaction_order:
        # redact specified column with regex methods, for chat and NOT voice
            if redactor == "SSN" and "SSN" in entities: texts, entity_map, curr_id, entity_values = redact.ssn(texts, entity_map, curr_id, ids, entity_values) # chat-yes, voice-no
            if redactor == "CCARD" and "CCARD" in entities: texts, entity_map, curr_id, entity_values = redact.ccard(texts, entity_map, curr_id, ids, entity_values) # chat-yes, voice-no
            if redactor == "ADDRESS" and "ADDRESS" in entities: texts, entity_map, curr_id, entity_values = redact.address(texts, entity_map, curr_id, ids, entity_values) # chat-yes, voice-no
            if redactor == "ZIP" and "ZIP" in entities: texts, entity_map, curr_id, entity_values = redact.zipC(texts, entity_map, curr_id, ids, entity_values) # chat-yes, voice-no supports US zip+4 and Canadian postal codes
            if args.modality == 'voice' and redactor == "ZIP" and "ZIP" in entities: texts, entity_map, curr_id, entity_values = redact.zip_voice(texts, entity_map, curr_id, ids, entity_values) # chat-no, voice-yes
            if redactor == "PHONE" and "PHONE" in entities: texts, entity_map, curr_id, entity_values = redact.phone(texts, entity_map, curr_id, ids, entity_values) # chat-yes, voice-no
            if args.modality == 'voice' and redactor == "PHONE" and "PHONE" in entities: texts, entity_map, curr_id, entity_values = redact.phone_voice(texts, entity_map, curr_id, ids, entity_values) # chat-no, voice-yes
            if redactor == "EMAIL" and "EMAIL" in entities: texts, entity_map, curr_id, entity_values = redact.email(texts, entity_map, curr_id, ids, entity_values) # chat-yes, voice-yes
            if redactor == "ORDINAL" and "ORDINAL" in entities: texts, entity_map, curr_id, entity_values = redact.ordinal(texts, entity_map, curr_id, ids, entity_values) # voice-yes, chat-yes
            if redactor == "CARDINAL" and "CARDINAL" in entities: texts, entity_map, curr_id, entity_values = redact.cardinal(texts, entity_map, curr_id, ids, entity_values) # voice-yes, chat-yes
            if redactor == "PIN" and "PIN" in entities: texts, entity_map, curr_id, entity_values = redact.pin(texts, entity_map, curr_id, ids, entity_values) # chat-yes, voice-no
            if args.modality == 'voice' and redactor == "PIN" and "PIN" in entities: texts, entity_map, curr_id, entity_values = redact.pin_voice(texts, entity_map, curr_id, ids, entity_values) # chat-no, voice-yes

        # redact specified column with Spacy Entities
        texts, entity_map, curr_id, ids, entity_values = redact.ner_ml(texts, entity_map, curr_id, ids, entity_values, args, entities)

    #reverse keys and values in entity_map for anonymization
    entity_map = {c_id:{v:"" for k,v in e_map.items()} for c_id,e_map in entity_map.items()}

    # anonymize if flag was passed
    if args.anonymize:
        if "ADDRESS" in entities: texts, entity_map = anonymize.address(texts, entity_map, ids, args.modality, anon_map, token_map) # text-yes, voice=yes
        if "CCARD" in entities: texts, entity_map = anonymize.ccard(texts, entity_map, ids, args.modality, anon_map, token_map) # text-yes, voice=yes
        if "PHONE" in entities: texts, entity_map = anonymize.phone(texts, entity_map, ids, args.modality, anon_map, token_map) # text-yes, voice=yes
        #if "CARDINAL" in entities: texts, entity_map = anonymize.cardinal(texts, entity_map, ids, args.modality, anon_map, token_map) # text-yes, voice=yes
        if "ORDINAL" in entities: texts, entity_map = anonymize.ordinal(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "ZIP" in entities: texts, entity_map = anonymize.zipC(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "ORG" in entities: texts, entity_map = anonymize.company(texts, entity_map, ids, anon_map, token_map) # chats-yes, voice=yes
        if "PERSON" in entities: texts, entity_map = anonymize.person(texts, entity_map, ids, names, anon_map, token_map) # chats-yes, voice=yes
        if "TIME" in entities: texts, entity_map = anonymize.atime(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "DATE" in entities: texts, entity_map = anonymize.adate(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "GPE" in entities: texts, entity_map = anonymize.gpe(texts, entity_map, ids, anon_map, token_map) # chats-yes, voice=yes
        if "WORK_OF_ART" in entities: texts, entity_map = anonymize.work_of_art(texts, entity_map, ids, anon_map, token_map) # chats-yes, voice=yes
        if "LANGUAGE" in entities: texts, entity_map = anonymize.language(texts, entity_map, ids, anon_map, token_map) # chats-yes, voice=yes
        if "EVENT" in entities: texts, entity_map = anonymize.event(texts, entity_map, ids, anon_map, token_map) # chats-yes, voice=yes
        if "NORP" in entities: texts, entity_map = anonymize.norp(texts, entity_map, ids, anon_map, token_map) # chats-yes, voice=yes
        if "MONEY" in entities: texts, entity_map = anonymize.money(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "PERCENT" in entities: texts, entity_map = anonymize.perc(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "SSN" in entities: texts, entity_map = anonymize.ssn(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "EMAIL" in entities: texts, entity_map = anonymize.email(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes
        if "PIN" in entities: texts, entity_map = anonymize.pin(texts, entity_map, ids, args.modality, anon_map, token_map) # chats-yes, voice=yes

        # These anonymizers are for spacy labels that we have anonymized to "[]" unless its a mislabeled match to another label
        if "LAUGHTER" in entities: texts, entity_map = anonymize.laughter(texts, entity_map, ids, anon_map, token_map) # chats-yes, voice=yes
        if "PRODUCT" in entities: texts, entity_map = anonymize.product(texts, entity_map, ids, anon_map, token_map) # chats-yes, voice=yes
        if "QUANTITY" in entities: texts, entity_map = anonymize.quantity(texts, entity_map, ids, anon_map, token_map) # chats-yes, voice=yes
        if "LAW" in entities: texts, entity_map = anonymize.law(texts, entity_map, ids, anon_map, token_map) # chats-yes, voice=yes
        if "FAC" in entities: texts, entity_map = anonymize.fac(texts, entity_map, ids, anon_map, token_map) # chats-yes, voice=yes
        if "LOC" in entities: texts, entity_map = anonymize.loc(texts, entity_map, ids, anon_map, token_map) # chats-yes, voice=yes

    # data cleanup
    texts = redact.replace_ignore(texts,entity_values)
    texts = redact.clean(texts) # chats-yes, voice-yes

    if args.uppercase:
        texts = redact.convert_to_uppercase(texts)

    # write the redacted data back to the Dataframe
    df.iloc[:, args.column-1] = texts

    # write the updated CSV to disk
    df.to_csv(args.outputfile, index=False)

    # write audit log
    if args.log:
        redact.write_audit_log(args.log, entity_values)

    print("Done. Output file is",args.outputfile)


if __name__ == "__main__":
    main()