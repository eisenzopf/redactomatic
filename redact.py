import csv
import json
import os
import sys
import spacy
import regex
import pandas as pd
import numpy as np
import entity_map as em

#Tracking ID-TEXT connection, find match to pattern of type label; keeping entities map updated
# pattern: the regex used to match the target entity.
# label: contains IGNORE,ADDRESS,CCARD,EMAIL,PHONE,PIN,SSN,ZIP
# texts : an array of texts to be redacted
# entity_map : a map to keep track of indexes assoigned to redacted words to enable restoration of consitent anonymized words later.
# eCount : a unique entity key, ready for the next discovered entity
# ids: an array of conversation-ids (aligns with the texts in length and content)
# entity_values: a dictionary to keep the substituted entity values keyed by their substituted labels (e.g. ) entity_values["PIN-45"=1234]
# group:  contains the target match group for the regex. By default the whole match is used but this can be a named match (e.g. group='zip')

def the_redactor(pattern, label, texts, entity_map, eCount, ids, entity_values, group=1):
    new_texts = []
    for text, d_id in zip(texts,ids):
        matches = list(pattern.finditer(text))
        newString = text
        for e in reversed(matches): #reversed to not modify the offsets of other entities when substituting
            #name=entity-text found by pattern
            if group != 1 and e.captures(group):
                    name = e.captures(group)[0]
                    start = e.span(group)[0]
            else:
                name = e.group()
                start = e.span()[0]

            if not (label == "CARDINAL" and "[" in name and "]" in name): #not capture label ids as cardinal
                c = entity_map.update_entities(name,d_id,eCount,label)
                end = start + len(name)
                newLabel = label+ "-"+str(c)
                newString = newString[:start] + "["+ newLabel + "]" + newString[end:]
                entity_values = update_entity_values(newLabel,name,entity_values)
                eCount += 1
        new_texts.append(newString)
    return new_texts, entity_map, eCount, entity_values

def update_entity_values(id,value,entity_values):
    if id not in entity_values:
        entity_values[id] = value
    return entity_values

def ner_ml(texts, entity_map, eCount, ids, entity_values, args, entities):
    print("Redacting named entities (ML)...")
    from spacy.lang.en import English
    spacy_multiword_labels = ["PERSON"]
    if args.large:
        nlp = spacy.load("en_core_web_lg")
    else:
        nlp = spacy.load("en_core_web_sm")
    new_texts = []
    #Spacy version of the_redactor function...
    for doc, d_id in zip(nlp.pipe(texts, disable=["tagger", "parser", "lemmatizer"], n_process=4, batch_size=1000),ids):
        newString = doc.text
        for e in reversed(doc.ents): #reversed to not modify the offsets of other entities when substituting
            # redact if the recognized entity is in the list of entities from the config.json file
            if e.label_ in entities:
                name = e.text
                value = name
                # split name if we have a first and last name ( [PERSON] )
                if e.label_ in spacy_multiword_labels and " " in name:
                    broken = name.split()
                    for i,n, in enumerate(reversed(broken)):
                        i = len(broken)-1 -i
                        name = n
                        start = e.start_char + sum([len(w)+1 for w in broken[:i]])
                        end = start + len(name)
                        c = entity_map.update_entities(name,d_id,eCount,e.label_)
                        newString = newString[:start] + " [" + e.label_ +"-"+ str(c) + "]" + newString[end:]
                        eCount += 1
                else:
                    c = entity_map.update_entities(name,d_id,eCount,e.label_)
                    start = e.start_char
                    end = start + len(name)
                    newLabel = e.label_ +"-"+ str(c)
                    newString = newString[:start] + "[" + newLabel + "]" + newString[end:]
                    entity_values = update_entity_values(newLabel,value,entity_values)
                    eCount += 1
        newString = newString.replace('$','')
        new_texts.append(newString)
    return new_texts, entity_map, eCount, ids, entity_values


def address(texts, entity_map, eCount, ids, entity_values):
    print("Redacting address (Regex)...")
    pattern = regex.compile("""(?<address1>(?>\d{1,6}(?>\ 1\/[234])?( (N(orth)?|S(outh)?)? ?(E(ast)?|W(est)?))?((?> \d+ ?(th|rd|st|nd))|(?> [A-Z](?>[a-z])+)+) (?>(?i)THROUGHWAY|TRAFFICWAY|CROSSROADS|EXPRESSWAY|BOULEVARD|CROSSROAD|EXTENSION|JUNCTIONS|MOUNTAINS|STRAVENUE|UNDERPASS|CAUSEWAY|CRESCENT|CROSSING|JUNCTION|MOTORWAY|MOUNTAIN|OVERPASS|PARKWAYS|TURNPIKE|VILLIAGE|VILLAGES|CENTERS|CIRCLES|COMMONS|CORNERS|ESTATES|EXPRESS|FORESTS|FREEWAY|GARDENS|GATEWAY|HARBORS|HIGHWAY|HOLLOWS|ISLANDS|JUNCTON|LANDING|MEADOWS|MOUNTIN|ORCHARD|PARKWAY|PASSAGE|PRAIRIE|RANCHES|SPRINGS|SQUARES|STATION|STRAVEN|STRVNUE|STREETS|TERRACE|TRAILER|TUNNELS|VALLEYS|VIADUCT|VILLAGE|ALLEE|ARCADE|AVENUE|BLUFFS|BOTTOM|BRANCH|BRIDGE|BROOKS|BYPASS|CANYON|CAUSWA|CENTER|CENTRE|CIRCLE|CLIFFS|COMMON|CORNER|COURSE|COURTS|CRSENT|CRSSNG|DIVIDE|DRIVES|ESTATE|EXTNSN|FIELDS|FOREST|FORGES|FREEWY|GARDEN|GATEWY|GATWAY|GREENS|GROVES|HARBOR|HIGHWY|HOLLOW|ISLAND|ISLNDS|JCTION|JUNCTN|KNOLLS|LIGHTS|MANORS|MEADOW|MEDOWS|MNTAIN|ORCHRD|PARKWY|PLAINS|POINTS|RADIAL|RADIEL|RAPIDS|RIDGES|SHOALS|SHOARS|SHORES|SKYWAY|SPRING|SPRNGS|SQUARE|STRAVN|STREAM|STREME|STREET|SUMITT|SUMMIT|TRACES|TRACKS|TRAILS|TUNNEL|TURNPK|UNIONS|VALLEY|VIADCT|VILLAG|ALLEE|ALLEY|ANNEX|AVENU|AVNUE|BAYOO|BAYOU|BEACH|BLUFF|BOTTM|BOULV|BRNCH|BRDGE|BROOK|BURGS|BYPAS|CANYN|CENTR|CNTER|CIRCL|CRCLE|CLIFF|COURT|COVES|CREEK|CRSNT|CREST|CURVE|DRIVE|FALLS|FERRY|FIELD|FLATS|FORDS|FORGE|FORKS|FRWAY|GARDN|GRDEN|GRDNS|GTWAY|GLENS|GREEN|GROVE|HARBR|HRBOR|HAVEN|HIWAY|HILLS|HOLWS|ISLND|ISLES|JCTNS|KNOLL|LAKES|LNDNG|LIGHT|LOCKS|LODGE|LOOPS|MANOR|MILLS|MISSN|MOUNT|MNTNS|PARKS|PKWAY|PKWYS|PATHS|PIKES|PINES|PLAIN|PLAZA|POINT|PORTS|RANCH|RNCHS|RAPID|RIDGE|RIVER|ROADS|ROUTE|SHOAL|SHOAR|SHORE|SPRNG|SPNGS|SPURS|STATN|STRAV|STRVN|SUMIT|TRACE|TRACK|TRAIL|TRLRS|TUNEL|TUNLS|TUNNL|TRNPK|UNION|VALLY|VIEWS|VILLG|VILLE|VISTA|WALKS|WELLS|ALLY|ANEX|ANNX|AVEN|BEND|BLUF|BLVD|BOUL|BURG|BYPA|BYPS|CAMP|CNYN|CAPE|CSWY|CENT|CNTR|CIRC|CRCL|CLFS|CLUB|CORS|CRSE|COVE|CRES|XING|DALE|DRIV|ESTS|EXPR|EXPW|EXPY|EXTN|EXTS|FALL|FRRY|FLDS|FLAT|FLTS|FORD|FRST|FORG|FORK|FRKS|FORT|FRWY|GRDN|GDNS|GTWY|GLEN|GROV|HARB|HIWY|HWAY|HILL|HLLW|HOLW|INLT|ISLE|JCTN|JCTS|KEYS|KNOL|KNLS|LAKE|LAND|LNDG|LANE|LOAF|LOCK|LCKS|LDGE|LODG|LOOP|MALL|MNRS|MDWS|MEWS|MILL|MSSN|MNTN|MTIN|NECK|ORCH|OVAL|PARK|PKWY|PASS|PATH|PIKE|PINE|PNES|PLNS|PLZA|PORT|PRTS|RADL|RAMP|RNCH|RPDS|REST|RDGE|RDGS|RIVR|ROAD|SHLS|SHRS|SPNG|SPGS|SPUR|SQRE|SQRS|STRA|STRM|STRT|TERR|TRCE|TRAK|TRKS|TRLS|TRLR|TUNL|VLLY|VLYS|VDCT|VIEW|VILL|VLGS|VIST|VSTA|WALK|WALL|WAYS|WELL|ALY|ANX|ARC|AVE|AVN|BCH|BND|BLF|BOT|BTM|BRG|BRK|BYP|CMP|CPE|CEN|CTR|CIR|CLF|CLB|COR|CTS|CRK|DAM|DIV|DVD|DRV|EST|EXP|EXT|FLS|FRY|FLD|FLT|FRD|FRG|FRK|FRT|FWY|GLN|GRN|GRV|HBR|HVN|HTS|HWY|HLS|ISS|JCT|KEY|KYS|KNL|LKS|LGT|LCK|LDG|MNR|MDW|MNT|MTN|NCK|OVL|PRK|PKY|PLN|PLZ|PTS|PRT|PRR|RAD|RPD|RST|RDG|RIV|RVR|RDS|ROW|RUE|RUN|SHL|SHR|SPG|SQR|SQU|STA|STN|STR|SMT|TER|TRK|TRL|VLY|VIA|VWS|VLG|VIS|VST|WAY|WLS|AV|BR|CP|CT|CV|DL|DM|DV|DR|FT|HT|HL|IS|KY|LK|LN|LF|MT|PL|PT|PR|RD|SQ|ST|UN|VW|VL|WY))( (N(orth)?|S(outh)?)? ?(E(ast)?|W(est)?)?)?)""", regex.IGNORECASE)
    return the_redactor(pattern, "ADDRESS", texts, entity_map, eCount, ids, entity_values)
    

def cardinal(texts, entity_map, eCount, ids, entity_values):
    print("Redacting cardinals (Regex)...")
    pattern = regex.compile("""
(?xi)           # free-spacing mode
  (?(DEFINE)
  (?<one_to_9>  
  (?:\m(one|two|three|four|five|six|seven|eight|nine)\M)
  ) # end one_to_9 definition

  (?<ten_to_19>  
  (?:\m(ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen)\M) 
  ) # end ten_to_19 definition

  (?<two_digit_prefix>
  (?:\m(s(?:even|ix)|t(?:hir|wen)|f(?:if|or)|eigh|nine)ty)\M
  ) # end two_digit_prefix definition

  (?<one_to_99>
  (?&two_digit_prefix)(?:[- ](?&one_to_9))?|(?&ten_to_19)|
                                              (?&one_to_9)
  ) # end one_to_99 definition

  (?<one_to_999>
  (?&one_to_9)[ ]hundred(?:[ ](?:and[ ])?(?&one_to_99))?|
                                            (?&one_to_99)
  ) # end one_to_999 definition

  (?<one_to_999_999>
  (?&one_to_999)[ ]thousand(?:[ ](?&one_to_999))?|
                                    (?&one_to_999)
  ) # end one_to_999_999 definition

  (?<one_to_999_999_999>
  (?&one_to_999)[ ]million(?:[ ](?&one_to_999_999))?|
                                   (?&one_to_999_999)
  ) # end one_to_999_999_999 definition

  (?<one_to_999_999_999_999>
  (?&one_to_999)[ ]billion(?:[ ](?&one_to_999_999_999))?|
                                   (?&one_to_999_999_999)
  ) # end one_to_999_999_999_999 definition

  (?<one_to_999_999_999_999_999>
  (?&one_to_999)[ ]trillion(?:[ ](?&one_to_999_999_999_999))?|
                                    (?&one_to_999_999_999_999)
  ) # end one_to_999_999_999_999_999 definition

  (?<bignumber>
  ((\mzero\M|\moh\M|(?&one_to_999_999_999_999_999)))
  ) # end bignumber definition

  (?<zero_to_9>
  (?&one_to_9)
  ) # end zero to 9 definition

  (?<decimals>
  point(?:[ ](?&zero_to_9))+
  ) # end decimals definition
  
) # End DEFINE


####### The Regex Matching Starts Here ########
#(?&bignumber)(?:[ ](?&decimals))?

### Other examples of groups we could match ###
\[\w+-\d+\]|(?&bignumber)|(\d+)
# (?&one_to_99)
# (?&one_to_999)
# (?&one_to_999_999)
# (?&one_to_999_999_999)
# (?&one_to_999_999_999_999)
# (?&one_to_999_999_999_999_999)
""")
    return the_redactor(pattern, "CARDINAL", texts, entity_map, eCount, ids, entity_values)


def ccard(texts, entity_map, eCount, ids, entity_values):
    print("Redacting credit card (Regex)...")
    pattern = regex.compile("""(?:\d[ -]*?){13,16}""", regex.IGNORECASE)
    return the_redactor(pattern, "CCARD", texts, entity_map, eCount, ids, entity_values)


def clean(texts):
    print("Cleaning text (Regex)...")
    spaces = regex.compile('\s+')
    dotdot = regex.compile(r'\.\.\.')
    unknown = regex.compile(r'\<UNK\>')
    add_space = regex.compile(r'(\]\[)')
    add_space2 = regex.compile(r'((\w+)\[)')
    add_space3 = regex.compile(r'(\](\w+))')
    new_texts = []
    for text in texts:
        new_text = dotdot.sub('', text, concurrent=True)
        new_text = spaces.sub(' ', new_text, concurrent=True)
        new_text = unknown.sub('', new_text, concurrent=True)
        new_text = add_space.sub('] [', new_text, concurrent=True)
        new_text = add_space2.sub(r'\2 [', new_text, concurrent=True)
        new_text = add_space3.sub(r'] \2', new_text, concurrent=True)
        new_text = new_text.strip()
        new_texts.append(new_text)
    return new_texts


def convert_to_uppercase(texts):
    print("Converting letters to uppercase...")
    new_texts=[]
    for text in texts:
        new_text = text.upper()
        new_texts.append(new_text)
    return new_texts


def dates(texts,entity_map,eCount,ids):
    print("Redacting dates (Regex) ...")
    pattern = ""
    pass


def email(texts, entity_map, eCount, ids, entity_values):
    print("Redacting email (Regex)...")
    pattern = regex.compile("""[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}""", regex.IGNORECASE)
    return the_redactor(pattern, "EMAIL", texts, entity_map, eCount, ids, entity_values)


def ignore_phrases(texts, entity_map, eCount, ids, entity_values):
    print("Redacting ignore phrases (Regex)...")
    entity_values = {}
    with open(os.getcwd() + '/ignore.json') as json_file:
        phrases = json.load(json_file)
    for phrase in phrases:
        pattern = regex.compile(phrase,regex.IGNORECASE)
        texts, entity_map, eCount, entity_values = the_redactor(pattern, "IGNORE", texts, entity_map, eCount, ids, entity_values)
    return texts, entity_map, eCount, entity_values


def load_config(level):
    print("Loading configuration...")
    config = {}
    entities = []
    with open(os.getcwd() + '/config.json') as json_file:
        config = json.load(json_file)
    if level == 1:
        entities = config['level-1']
    elif level == 2:
        entities = config['level-2']
    elif level == 3:
        entities = config['level-3']
    return entities, config['redaction-order'], config['anon-map'], config['token-map']


def ordinal(texts, entity_map, eCount, ids, entity_values):
    print("Redacting ordinals (Regex)...")
    pattern = regex.compile("""
    (?x)           # free-spacing mode
(?(DEFINE)
  (?<one_to_9>  
  (fir|seco|thi|four|fif|six|seven|eigh|nin|[1-9])(?:st|nd|rd|th)
  ) # end one_to_9 definition

  (?<ten_to_19> 
  (?:(?:(ten|eleven|twelf)|((?:thir|four|fif|six|seven|eigh|nine)teen))th|((10|11|12|13|14|15|16|17|18|19)th))
  ) # end ten_to_19 definition

  (?<two_digit_ordinal_prefix>
  ((?:s(?:even|ix)|t(?:hir|wen)|f(?:if|or)|eigh|nine)tieth)|((2|3|4|5|6|7|8|9)0)th
  ) # end two_digit_prefix definition

  (?<two_digit_prefix>
  ((?:s(?:even|ix)|t(?:hir|wen)|f(?:if|or)|eigh|nine)ty)
  ) # end two_digit_prefix definition

  (?<numeric_ordinal>
  ([2-9][1-9](st|nd|rd|th))
  )

  (?<one_to_99>
  (?&two_digit_ordinal_prefix)|(?&numeric_ordinal)|(?&two_digit_prefix)(?:[- ](?&one_to_9))|(?&ten_to_19)|(?&one_to_9)
  ) # end one_to_99 definition

  (?<one_to_999>
  (?&one_to_9)[ ]hundred(?:[ ](?:and[ ])?(?&one_to_99))?|
                                            (?&one_to_99)
  ) # end one_to_999 definition

  (?<one_to_999_999>
  (?&one_to_999)[ ]thousand(?:[ ](?&one_to_999))?|
                                    (?&one_to_999)
  ) # end one_to_999_999 definition

  (?<one_to_999_999_999>
  (?&one_to_999)[ ]million(?:[ ](?&one_to_999_999))?|
                                   (?&one_to_999_999)
  ) # end one_to_999_999_999 definition

  (?<one_to_999_999_999_999>
  (?&one_to_999)[ ]billion(?:[ ](?&one_to_999_999_999))?|
                                   (?&one_to_999_999_999)
  ) # end one_to_999_999_999_999 definition

  (?<one_to_999_999_999_999_999>
  (?&one_to_999)[ ]trillion(?:[ ](?&one_to_999_999_999_999))?|
                                    (?&one_to_999_999_999_999)
  ) # end one_to_999_999_999_999_999 definition

  (?<bignumber>
  (?&one_to_999_999_999_999_999)
  ) # end bignumber definition

  (?<zero_to_9>
  (?&one_to_9)
  ) # end zero to 9 definition

  (?<decimals>
  point(?:[ ](?&zero_to_9))+
  ) # end decimals definition
  
) # End DEFINE


####### The Regex Matching Starts Here ########
#(?&bignumber)(?:[ ](?&decimals))?

### Other examples of groups we could match ###
(?&bignumber)
# (?&one_to_99)
# (?&one_to_999)
# (?&one_to_999_999)
# (?&one_to_999_999_999)
# (?&one_to_999_999_999_999)
# (?&one_to_999_999_999_999_999)
""", regex.IGNORECASE)
    return the_redactor(pattern, "ORDINAL", texts, entity_map, eCount, ids, entity_values)


def phone(texts, entity_map, eCount, ids, entity_values):
    print("Redacting phone (Regex)...")
    pattern = regex.compile("""((?:(?<![\d-])(?:\+?\d{1,3}[-.\s*]?)?(?:\(?\d{3}\)?[-.\s*]?)?\d{3}[-.\s*]?\d{4}(?![\d-]))|(?:(?<![\d-])(?:(?:\(\+?\d{2}\))|(?:\+?\d{2}))\s*\d{2}\s*\d{3}\s*\d{4}(?![\d-])))""", regex.IGNORECASE)
    return the_redactor(pattern, "PHONE", texts, entity_map, eCount, ids, entity_values)


def phone_voice(texts, entity_map, eCount, ids, entity_values):
    print("Redacting voice transcribed phone (Regex)...")
    pattern = regex.compile("""
    (?xi)           # free-spacing mode
    (?(DEFINE)
        (?<one_to_9>  
        (?:(one|two|three|four|five|six|seven|eight|nine|0z|oh))
        ) # end one_to_9 definition
    )
    (^|\s)(?:(?&one_to_9)\s?(?&one_to_9)\s?(?&one_to_9)[\s,]{1,2}
    (?&one_to_9)\s?(?&one_to_9)\s?(?&one_to_9)[\s,]{1,2}
    (?&one_to_9)\s?(?&one_to_9)\s?(?&one_to_9)\s?(?&one_to_9))(?!\s*)?
    """, regex.IGNORECASE)
    return the_redactor(pattern, "PHONE", texts, entity_map, eCount, ids, entity_values)


def pin(texts, entity_map, eCount, ids, entity_values):
    print("Redacting pin (Regex)...")
    pattern = regex.compile("""(^|\s)(?:(\d{4}))\s*?""", regex.IGNORECASE)
    return the_redactor(pattern, "PIN", texts, entity_map, eCount, ids, entity_values)


def pin_voice(texts, entity_map, eCount, ids, entity_values):
    print("Redacting voice transcribed pin (Regex)...")
    pattern = regex.compile("""
    (?xi)           # free-spacing mode
    (?(DEFINE)
        (?<one_to_9> 
        (?:(one|two|three|four|five|six|seven|eight|nine|0z))
        ) # end one_to_9 definition
    )
    (^|\s)(?:(?&one_to_9)\s?(?&one_to_9)\s?(?&one_to_9)\s?(?&one_to_9))(?!\s*)?
    """, regex.IGNORECASE)
    return the_redactor(pattern, "PIN", texts, entity_map, eCount, ids, entity_values)


def replace_ignore(texts,entity_values):
    print("Re-inserting ignored text...")
    new_texts = []
    pattern = regex.compile(r'(\[(IGNORE\-\d+)\])')

    for text in texts:
        matches = list(pattern.finditer(text))
        newString = text
        for e in reversed(matches):
            name = e.group(2)
            start = e.span()[0]
            end = start + len(e.group())
            newString = newString[:start] + entity_values[name] + newString[end:]
        new_texts.append(newString)
    return new_texts


def ssn(texts, entity_map, eCount, ids, entity_values):
    print("Redacting SSN (Regex)...")
    pattern = regex.compile("""(^|\s)(?<ssn>(?!000|666)[0-8][0-9]{2}(-|\s)?(?!00)[0-9]{2}(-|\s)?(?!0000)[0-9]{4})(\s|$|\.)""", regex.IGNORECASE)
    return the_redactor(pattern, "SSN", texts, entity_map, eCount, ids, entity_values,"ssn")


def write_audit_log(filename, entity_values):
    print("Writing log to " + filename)
    a_file = open(os.getcwd() + "/" + filename, "w")
    writer = csv.writer(a_file)
    for key, value in entity_values.items():
        writer.writerow([key, value])
    a_file.close()


def zipC(texts, entity_map, eCount, ids, entity_values):
    print("Redacting zip (Regex)...")
    pattern = regex.compile("""((?<full>(?<part1>[ABCEGHJKLMNPRSTVXY]{1}\d{1}[A-Z]{1})(?:[ ](?=\d))?(?<part2>\d{1}[A-Z]{1}\d{1}))$)|((^|\s{1})(?<zip>(?!00[02-5]|099|213|269|34[358]|353|419|42[89]|51[789]|529|53[36]|552|5[67]8|5[78]9|621|6[348]2|6[46]3|659|69[4-9]|7[034]2|709|715|771|81[789]|8[3469]9|8[4568]8|8[6-9]6|8[68]7|9[02]9|987)\d{5})(\s|\.|$|\-(?<plus4>[0-9]{4})?))""", regex.IGNORECASE)
    return the_redactor(pattern, "ZIP", texts, entity_map, eCount, ids, entity_values, "zip")


def zip_voice(texts, entity_map, eCount, ids, entity_values):
    print(" Redacting voice transcribed zip (Regex)...")
    pattern = regex.compile("""
    (?xi)           # free-spacing mode
    (?(DEFINE)
        (?<one_to_9>  
        (?:(one|two|three|four|five|six|seven|eight|nine|0z))
        ) # end one_to_9 definition
    )
    (^|\s)(?:(?&one_to_9)\s?(?&one_to_9)\s?(?&one_to_9)\s?(?&one_to_9)\s?(?&one_to_9))(?!\s*)?
    """, regex.IGNORECASE)
    return the_redactor(pattern, "ZIP", texts, entity_map, eCount, ids, entity_values)