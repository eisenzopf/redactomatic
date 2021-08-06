import redact
import anonymize

def main():
    #initialize entity map
    entity_map = {} 

    # initialize entity value dict
    entity_values = {}

    # unique entity key
    curr_id = 0
    
    # get command line params
    args = redact.config_args()

    # validate command line params
    if args.modality == "text":
        pass
    elif args.modality == "voice":
        pass
    else:
        print("--modality command line value must be either text or voice")
        exit()

    # load data into a Pandas Dataframe
    df, texts, ids = redact.df_load_files(args)

    # first pass replaces text phrases that should be ignored and stored them in entity_values
    texts, entity_map, curr_id, entity_values  = redact.ignore_phrases(texts, entity_map, curr_id, ids, entity_values)

    # redact specified column with Spacy Entities
    texts, entity_map, curr_id, ids, entity_values = redact.ner_ml(texts, entity_map, curr_id, ids, entity_values, args)

    # redact specified column with regex methods, for chat and NOT voice
    texts, entity_map, curr_id, entity_values = redact.ccard(texts, entity_map, curr_id, ids, entity_values) # chat-yes, voice-no
    texts, entity_map, curr_id, entity_values = redact.address(texts, entity_map, curr_id, ids, entity_values) # chat-yes, voice-no
    texts, entity_map, curr_id, entity_values = redact.zipC(texts, entity_map, curr_id, ids, entity_values) # chat-yes, voice-no supports US zip+4 and Canadian postal codes
    texts, entity_map, curr_id, entity_values = redact.phone(texts, entity_map, curr_id, ids, entity_values) # chat-yes, voice-no

    # redact specified column with regex methods, for chat AND voice
    texts, entity_map, curr_id, entity_values = redact.ordinal(texts, entity_map, curr_id, ids, entity_values) # voice-yes, chat-yes
    texts, entity_map, curr_id, entity_values = redact.cardinal(texts, entity_map, curr_id, ids, entity_values) # voice-yes, chat-yes
    
    #reverse keys and values in entity_map for anonymization
    entity_map = {c_id:{v:"" for k,v in e_map.items()} for c_id,e_map in entity_map.items()}

    # anonymize if flag was passed
    if args.anonymize:
        texts, entity_map = anonymize.address(texts, entity_map, ids, args.modality) # text-yes, voice=yes
        texts, entity_map = anonymize.ccard(texts, entity_map, ids, args.modality) # text-yes, voice=yes
        texts, entity_map = anonymize.phone(texts, entity_map, ids, args.modality) # text-yes, voice=yes
        texts, entity_map = anonymize.cardinal(texts, entity_map, ids, args.modality) # text-yes, voice=yes
        texts, entity_map = anonymize.ordinal(texts, entity_map, ids, args.modality) # chats-yes, voice=yes
        texts, entity_map = anonymize.zipC(texts, entity_map, ids, args.modality) # chats-yes, voice=yes
        texts, entity_map = anonymize.company(texts, entity_map, ids) # chats-yes, voice=yes
        texts, entity_map = anonymize.person(texts, entity_map, ids) # chats-yes, voice=yes
        texts, entity_map = anonymize.atime(texts, entity_map, ids, args.modality) # chats-yes, voice=yes
        texts, entity_map = anonymize.adate(texts, entity_map, ids, args.modality) # chats-yes, voice=yes
        texts, entity_map = anonymize.gpe(texts, entity_map, ids) # chats-yes, voice=yes
        texts, entity_map = anonymize.work_of_art(texts, entity_map, ids) # chats-yes, voice=yes
        texts, entity_map = anonymize.language(texts, entity_map, ids) # chats-yes, voice=yes
        texts, entity_map = anonymize.event(texts, entity_map, ids) # chats-yes, voice=yes
        texts, entity_map = anonymize.norp(texts, entity_map, ids) # chats-yes, voice=yes
        texts, entity_map = anonymize.money(texts, entity_map, ids, args.modality) # chats-yes, voice=yes
        texts, entity_map = anonymize.perc(texts, entity_map, ids, args.modality) # chats-yes, voice=yes

        # These anonymizers are for spacy labels that we have anonymized to "[]" unless its a mislabeled match to another label
        texts, entity_map = anonymize.laughter(texts, entity_map, ids) # chats-yes, voice=yes
        texts, entity_map = anonymize.product(texts, entity_map, ids) # chats-yes, voice=yes
        texts, entity_map = anonymize.quantity(texts, entity_map, ids) # chats-yes, voice=yes
        texts, entity_map = anonymize.law(texts, entity_map, ids) # chats-yes, voice=yes
        texts, entity_map = anonymize.fac(texts, entity_map, ids) # chats-yes, voice=yes
        texts, entity_map = anonymize.loc(texts, entity_map, ids) # chats-yes, voice=yes

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