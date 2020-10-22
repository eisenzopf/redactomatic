import redact
import anonymize

def main():
    # get command line params
    args = redact.config_args()

    # load data into a Pandas Dataframe
    df = redact.df_load_files(args)

    # Redact specified column
    texts = redact.ner_ml(df, args)
    texts = redact.ccard(texts) # chat-yes, voice-no
    texts = redact.address(texts) # chat-yes, voice-no
    texts = redact.zip(texts) # chat-yes, voice-no supports US zip+4 and Canadian postal codes
    texts = redact.phone(texts) # chat-yes, voice-no
    texts = redact.ordinal(texts) # voice-yes, chat-yes
    texts = redact.cardinal(texts) # voice-yes, chat-yes

    # Anonymize
    if args.anonymize:
        texts = anonymize.cardinal(texts) # chats-no, voice=yes
        texts = anonymize.ordinal(texts) # chats-no, voice=yes
        texts = anonymize.zip(texts) # chats-no, voice=yes
        texts = anonymize.company(texts) # chats-no, voice=yes
        texts = anonymize.person(texts) # chats-no, voice=yes
        texts = anonymize.date(texts) # chats-no, voice=yes
        texts = anonymize.gpe(texts) # chats-no, voice=yes
        
    # Data Cleanup
    texts = redact.clean(texts) # chats-yes, voice-yes

    # write the redacted data back to the Dataframe
    df.iloc[:, args.column-1] = texts

    # anonymize if the flag was passed

    # write the updated CSV to disk
    df.to_csv(args.outputfile, index=False)

    print("Done. Output file is",args.outputfile)


if __name__ == "__main__":
    main()