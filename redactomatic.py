import redact
import anonymize

def main():
    # get command line params
    args = redact.config_args()

    # load data into a Pandas Dataframe
    df = redact.df_load_files(args)

    # redact specified column
    texts = redact.ner_ml(df, args)
    texts = redact.ccard(texts) # chat-yes, voice-no
    texts = redact.address(texts) # chat-yes, voice-no
    texts = redact.zip(texts) # chat-yes, voice-no supports US zip+4 and Canadian postal codes
    texts = redact.phone(texts) # chat-yes, voice-no
    texts = redact.ordinal(texts) # voice-yes, chat-yes
    texts = redact.cardinal(texts) # voice-yes, chat-yes

    # anonymize if flag was passed
    if args.anonymize:
        texts = anonymize.cardinal(texts) # chats-yes, voice=yes
        texts = anonymize.ordinal(texts) # chats-yes, voice=yes
        texts = anonymize.quantity(texts) # chats-yes, voice=yes
        texts = anonymize.zip(texts) # chats-no, voice=yes
        texts = anonymize.company(texts) # chats-yes, voice=yes
        texts = anonymize.person(texts) # chats-yes, voice=yes
        texts = anonymize.adate(texts) # chats-yes, voice=yes
        texts = anonymize.gpe(texts) # chats-yes, voice=yes
        texts = anonymize.work_of_art(texts) # chats-yes, voice=yes
        texts = anonymize.event(texts) # chats-yes, voice=yes
        texts = anonymize.norp(texts) # chats-yes, voice=yes
        texts = anonymize.money(texts) # chats-yes, voice=yes
        texts = anonymize.time(texts) # chats-yes, voice=yes
        texts = anonymize.laughter(texts) # chats-yes, voice=yes
        texts = anonymize.product(texts) # chats-yes, voice=yes
        texts = anonymize.language(texts) # chats-yes, voice=yes
        texts = anonymize.law(texts) # chats-yes, voice=yes
        texts = anonymize.fac(texts) # chats-yes, voice=yes
        texts = anonymize.loc(texts) # chats-yes, voice=yes
        # add ability to anonymize only


        
    # data cleanup
    texts = redact.clean(texts) # chats-yes, voice-yes

    # write the redacted data back to the Dataframe
    df.iloc[:, args.column-1] = texts

    # write the updated CSV to disk
    df.to_csv(args.outputfile, index=False)

    print("Done. Output file is",args.outputfile)


if __name__ == "__main__":
    main()