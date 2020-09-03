## Copyright 2020 Discourse.ai, Inc.
## Author: Jonathan Eisenzopf
## See LICENSE for licensing terms

import spacy
import csv
import sys
import re
from spacy.lang.en import English
from spacy.pipeline import EntityRuler

## FUNCTIONS
def redact_date(text):
    docx = nlp(text)
    redacted_sentences = []
    for ent in docx.ents:
        ent.merge()
    for token in docx:
        if token.ent_type_ == 'DATE':
            redacted_sentences.append("[DATE]")
        else:
            redacted_sentences.append(token.string)
    return "".join(redacted_sentences)

def redact_place(text):
    docx = nlp(text)
    redacted_sentences = []
    for ent in docx.ents:
        ent.merge()
    for token in docx:
        if token.ent_type_ == 'GPE':
            redacted_sentences.append("[GPE]")
        else:
            redacted_sentences.append(token.string)
    return "".join(redacted_sentences)

def redact_money(text):
    docx = nlp(text)
    redacted_sentences = []
    for ent in docx.ents:
        ent.merge()
    for token in docx:
        if token.ent_type_ == 'MONEY':
            redacted_sentences.append("[MONEY]")
        else:
            redacted_sentences.append(token.string)
    return "".join(redacted_sentences)

def redact_person(text):
    docx = nlp(text)
    redacted_sentences = []
    for ent in docx.ents:
        ent.merge()
    for token in docx:
        if token.ent_type_ == 'PERSON':
            redacted_sentences.append("[PERSON]")
        else:
            redacted_sentences.append(token.string)
    return "".join(redacted_sentences)

def redact_org(text):
    docx = nlp(text)
    redacted_sentences = []
    for ent in docx.ents:
        ent.merge()
    for token in docx:
        if token.ent_type_ == 'ORG':
            redacted_sentences.append("[ORG]")
        else:
            redacted_sentences.append(token.string)
    return "".join(redacted_sentences)

## MAIN
nlp = spacy.load("en_core_web_lg")
#nlp = English()
ruler = EntityRuler(nlp)
patterns = [{"label": "ORG", "pattern": "Apple"},
            {"label": "ORG", "pattern": "TracFone Wireless"},
            {"label": "ORG", "pattern": [{"LOWER": "FedEX"}]},
            {"label": "ORG", "pattern": "TracFone Wireless"},
            {"label": "ORG", "pattern": [{"LOWER": "Virgin"},{"LOWER": "Mobile"}]},
            {"label": "ORG", "pattern": "Virgin Mobile"},
            {"label": "ORG", "pattern": "Straight Talk"},
            {"label": "ORG", "pattern": "Straight Talk Wireless"},
            {"label": "ORG", "pattern": "Candy Crush LOL"},
            {"label": "ORG", "pattern": "Auto-Refill"},
            {"label": "ORG", "pattern": "SafeLink Wireless"},
            {"label": "ORG", "pattern": "Verizon"},
            {"label": "ORG", "pattern": "Levi"},
            {"label": "ORG", "pattern": "NET10"},
            {"label": "PERSON", "pattern": "Cherry"},
            {"label": "PERSON", "pattern": "Cris"},
            {"label": "PERSON", "pattern": "Ana"},
            {"label": "PERSON", "pattern": "Cristy"},
            {"label": "PERSON", "pattern": "Leonel"},
            {"label": "PERSON", "pattern": "Bob"},
            {"label": "ORG", "pattern": "Fedex"},
            {"label": "ORG", "pattern": "FedEx"},
            {"label": "ORG", "pattern": "WiFi"},
            {"label": "ORG", "pattern": "Wi-Fi"},
            {"label": "GPE", "pattern": [{"LOWER": "san"}, {"LOWER": "francisco"}]}]
ruler.add_patterns(patterns)
nlp.add_pipe(ruler)

## redaction patterns
engagement_id = re.compile('\d+')
imei = re.compile('\d{14,20}')
zip = re.compile('^\d{5}(-\d{4})?$')
last_four = re.compile('\d{4}')

for arg in sys.argv[1:]:
    filename = arg
    #print(filename)

    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if len(row) < 3:
                continue
            if line_count == 0:
                # Find conversation id
                conversation_id = engagement_id.search(row[0])
                #print ("engagement id =",conversation_id.group())
            elif line_count > 1:
                # Parse text
                text = row[2]
                from commonregex import CommonRegex
                parsed_text = CommonRegex(text)

                # Redact IMEI
                imei_number = imei.search(text)
                if imei_number:
                    text = text.replace(imei_number.group(),"[IMEI]",5)
                    #print("IMEI:",imei_number.group())

                # Redact phone numbers
                if parsed_text.phones:
                    for phone in parsed_text.phones:
                        text = text.replace(phone,"[PHONE]",5)
                        #print(phone)

                # Redact addresses
                if parsed_text.street_addresses:
                    for address in parsed_text.street_addresses:
                        text = text.replace(address,"[ADDRESS]")
                        #print(address)

                # Redact emails
                if parsed_text.emails:
                    for email in parsed_text.emails:
                        text = text.replace(email,"[EMAIL]",5)
                        #print(email)

                # Redact zip
                zip_code = zip.search(text)
                if zip_code:
                    text = text.replace(zip_code.group(),"[ZIP]",5)
                    #print("Zip:",zip_code.group())

                # Redact dates
                text = redact_date(text)

                # Redact money
                text = redact_money(text)

                # Redact last 4 of phone, PIN, or card
                last_four_num = last_four.search(text)
                if last_four_num:
                    text = text.replace(last_four_num.group(),"[LAST_FOUR]",5)
                    #print("Last Four:",last_four_num.group())

                # Redact Names
                text = redact_person(text)

                # Set speaker
                if re.match('Agent',row[1]):
                    speaker = "agent"
                else:
                    speaker = "client"

                # print CSV
                print(f'"{conversation_id.group()}","{speaker}","{row[0]}","{text}"')

                ##print(results)
                ##print(f'{row[1]}: {row[2]}')
                #doc = nlp(row[2])
                #for ent in doc.ents:
                    #if ent.label_ == 'PERSON' or ent.label_ == 'ORG':
                        #print(f'{engagement_id.group()} {ent.label_} {ent.text}')
                    ##print(ent.text, ent.start_char, ent.end_char, ent.label_)
            line_count += 1
