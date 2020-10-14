import redact

def main():
    args = redact.config_args()
    df = redact.df_load_files(args)
    texts = redact.ner_ml(df, args)
    texts = redact.ccard(texts) # chat-yes, voice-no
    texts = redact.address(texts) # chat-yes, voice-no
    texts = redact.zip(texts) # chat-yes, voice-no supports US zip+4 and Canadian postal codes
    texts = redact.phone(texts) # chat-yes, voice-no
    texts = redact.ordinal(texts) # voice-yes, chat-yes
    texts = redact.cardinal(texts) # voice-yes, chat-yes
    texts = redact.clean(texts) # chats-yes, voice-yes

    df.iloc[:, args.column-1] = texts
    #print(df.to_csv(index=False))
    df.to_csv(args.outputfile, index=False)

    print("Done. Output file is",args.outputfile)


if __name__ == "__main__":
    main()