# RedactoMatic

RedactoMatic is a command-line Python script that removes personally identifiable information (PII) from conversation data between agents and customers or bots and customers. It works with transcribed voice calls AND chat logs in a CSV format.

## Purpose

Many companies have security, privacy, and regulatory standards that require them to mask and/or remove PII information before it can be used and shared for data science purposes internally or externally. Redactomatic has been tested with NICE Nexidia voice transcriptions as well as LivePerson chat logs. I fully expect that it will work with other voice transcription, speech to text, live chat, chatbot, and IVR vendors with some work. I plan to add the ability to specify a particular vendor as I am provided with new vendor examples. Please let me know if you'd like me to add support for a particular vendor and I will be happy to do so. I only need a small data sample for testing purposes to add support for new vendors. I am especially interested in samples for Nuance, Avaya, Genesys, Cisco, and Verint. Please report bugs and feel free to make feature requests.

## How it works

Redactomatic is a multi-pass redaction tool with an optional anonymization function and reads in CSV files as input. When PII is detected, it is removed and replaced with an entity tag, like **[ORDINAL]**. If the *--anonymization* flag is added, Redactomatic will replace PII entity tags with randomized values. For example, **[PERSON]** might be replaced by the name John. This is useful when sharing datasets that need PII removed but also need some real world like value. The first redaction pass utilizes the Spacy 3 named entity recognition library. You have the option of using the large Spacy library if you add the *--large* command-line parameter, which will increase the number of correctly recognized PII entities, but will also take longer. After the Spacy NER pass, the subsequent passes utilize regular expressions. The reason multiple passes are needed is that machine learning libraries like Spacy are not reliable and cannot catch all PII. That is obviously not acceptable for financial services and other regulated industries. While large companies use this tool for mission critical applications, please test and validate the results before using it in production and report any anomalies to the authors.

### Redaction

Redactomatic assumes that each row in the input CSV file specified by *--inputfile* consists of a piece of text in the *--column* command line parameter. It does not currently support other input formats like JSON. Only one column may be specifed at a time from the command line and no other columns will be reviewed other than the one that has been specified. The script writes a new CSV file specified by the *--outputfile* command-line parameter. Other than the column that is redacted and specified by *--column*, the output CSV will be in the same format with the same information as the inputfile. As Redactomatic processes each row of an input CSV file, it replaces each recognized entity in the text with an entity type tag such as **[PHONE]**, **[ZIP]**, or **[CARDINAL**.

### Anonymization

If the optional command-line *--anonymize* switch is included, Redactomatic will replace all entity type tags with a randomized value. Numerical entity tags are anonymized using a random number generator. Text based entity tags are replaced using a random value from a corresponding data file in the [data/](data/) directory of this distribution. There are quite a few different anonymization types, but not all PII entity types are supported. Please refer to the list of supported PII entities below.

### Support for voice and text

Redactomatic supports both transcribed voice and chat conversation types. This is especially important as most other tools do not properly support ordinals, cardinals, currency, and other numeric types that used spelled numbers. For example, *five nine six eight* might not be correctly recognized and redacted by some other tools. Redactomatic supports both numeric and spelled cardinals and ordinals and operates in either *text* or *voice* mode as specified by the *--modality* command-line parameter.

### Dictionary of phrases to ignore

Redactomatic includes the ability to ignore key phrases. This comes in handy when redactomatic would otherwise tag something as PII that shouldn't be. For example, if a conversation includes the phrase, *"May I please have your first and last name"*, is the word *first* an ordinal? No it's not. Under normal conditions, Redactomatic would redact the word *first*. In the case where we use the *--anonymize* flag, it would assign a random ordinal in it's place. For example, the previous phrase might have been replaced with, *"May I please have your eighth and last name"*. This obviously doesn't make any sense. We can solve this problem by configuring Redactomatic to ignore the phrase, *"first and"*. We would do this by adding it to the file *ignore.json*. Every time Redactomatic runs, it will load the ignore dictionary from this file. You can add as many additional phrases as you like.

## Installation

To install RedactoMatic, run:

```sh
sh setup.sh
```

This will install required Python libraries and download the small (en_core_web_sm) and large (en_core_web_lg) Spacy models.

## Usage

Once installed, redactomatic needs at a minimum the 1. name of the input conversation file (--inputfile) in CSV format, 2. the modaility (--modality which must be voice or text), and 3. the column in the CSV containing the text to redact (--column), the column containing the conversation ID (--idcolumn).

```sh
usage: redactomatic.py [-h] --column COLUMN --idcolumn COLUMN --inputfile INPUTFILE [INPUTFILE ...] --outputfile OUTPUTFILE --modality voice|text [--anonymize] [--large] [--log LOG_FILE]
```

### Command Line Parameters

| Paramter | Description | Required?  |
|--------------|--------------|----------|
| column     | The column number containing the text to redact |  yes |
| idcolumn   | the column number containing the unique conversation id | yes |
| inputfile | The filename containing the conversations to process | yes |
| outputfile | The filename that will contain the redacted output | yes |
| modality | Can be voice or text depending on the type of conversations contained in the inputfile | yes |
| anonymize | If included will replace redaction tags with randomized values. Useful if you need simulated data. | no |
| large | If included will use the large Spacy language model. Not recommended unless you have a GPU or don't mind waiting a long time. | no |
| log | Logs all recognized entities that have been redacted including the unique entity ID and the entity value. Can be use for audit purposes. | no |
| uppercase | If included will convert all letters to uppercase. Useful when using NICE or other speech to text engines that transcribe voice to all caps. | no |

### Example 1: Redact a text file

The following command will use the sample input file included in the Redactomatic distribution [data/sample_data.csv](data/sample_data.csv) and create an output file called output.csv:

```sh
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile output.csv
```

If you review the sample data file, you will notice that the first column contains the conversation ID and that the fourth column contains the text we want to redact.

### Example 2: Anonymize a voice transcribed file with anonymization

In this second example, we are going to use a sample voice transcribed conversation and we are going to also anonymize the PII tags. This will replaced all PII with randomized values with context. When we say "with context", we mean that Redactomatic temporarily remembers when the same PII entity value has been used in the conversation and will replace it with the same randomized value. For example, If Mary is talking to John, we would first redact Mary as [PERSON-1] and John as [PERSON-2]. If we turn on anonymization via the *--anonymization* command-line parameter, Redactomatic will replace all instances of [PERSON-1] with the same randomized name so that the anonymized output is more coherent.

```sh
python3 redactomatic.py --column 4 --idcolumn 1 --modality voice --inputfile ./data/sample_data.csv --outputfile output.csv --anonymize
```

Notice that the *--modality* parameter is now *voice* and that we have added the *--anonymize parameter, which replaces all redaction tags with randomized values.

### Example 3: Using the large NER Model Example

By default, Redactomatic will use the Spacy 3 *en_core_web_sm* NER model. It's fast but does not work as well as the larger *en_core_web_lg* NER model. You can tell Redactomatic to use the larger model with the *--large* switch.

```sh
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile output.csv --large
```

### Example 4: Logging recognized PII values

In some cases, your security officer may want to see proof that Redactomatic has successfully removed all instances of PII data. You can turn on an audit log with the *--log* switch, but please be sure to secure the file because it will contain PII information. This feature will write a CSV file containing the redaction tag and PII entity value, one per rown.

```sh
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile output.csv --log audit.csv
```

## Supported Languages and Regions

Redactomatic currently supports English. Most entities support the US and Canada. If you would like to contribute additional languages and regions, we welcome the contribution.

## Supported Entities

The following entities are supported by Redactomatic. The Spacy [English NER model](https://spacy.io/models/en) is trained from the [Ontonotes 5.0 corpus](https://catalog.ldc.upenn.edu/docs/LDC2013T19/OntoNotes-Release-5.0.pdf) and therefore uses the 18 entity types from that corpus plus the additional entity types that were added to Redactomatic. The *[LAUGHTER]* tag is specific to NICE Nexidia transcription. Some numeric types such as *[ADDRESS]*, *[CCARD]*, and *[PHONE]* are not supported for voice transcriptions yet. However, they will still end up being redacted by *[ORDINAL]* or *[CARDINAL]* entity types. If an entity cannot be anonymized, in the case of a text entity, the redaction tag will be deleted and replaced with an empty string; in the case of numeric entity types like *[CCARD]* and *[ZIP]*, the numbers will be replaced by randomly generated cardinals.

| Entity Type | Redaction Tag  | Parsers      | Voice Support | Chat Support | Can be Anonymized |
|-------------|----------------|--------------|-----|-----|-----|
| Address     | [ADDRESS]      | Regex        | No  | Yes | Yes |
| Credit Card Number | [CCARD] | Regex        | No  | Yes | Yes |
| Cardinal    | [CARDINAL]     | Spacy, Regex | Yes | Yes | Yes |
| Date        | [DATE]         | Spacy        | Yes | Yes | Yes |
| Event       | [EVENT]        | Spacy        | Yes | Yes | Yes |
| Facility    | [FAC]          | Spacy        | Yes | Yes | No  |
| Country, City, State | [GPE] | Spacy        | Yes | Yes | No  |
| Language    | [LANGUAGE]     | Spacy        | Yes | Yes | Yes |
| Laughter    | [LAUGHTER]     | NICE         | Yes | No  | No  |
| Law         | [LAW]          | Spacy        | Yes | Yes | No  |
| Money       | [MONEY]        | Spacy        | Yes | Yes | Yes |
| Nationality, Religious or Political Organization | [NORP] | Spacy | Yes | Yes | Yes |
| Organization| [ORG]          | Spacy        | Yes | Yes | Yes |
| Ordinal     | [ORDINAL]      | Spacy, Regex | Yes | Yes | Yes |
| Percent     | [PERCENT]      | Spact        | Yes | Yes | Yes |
| Person      | [PERSON]       | Spacy        | Yes | Yes | Yes |
| Phone       | [PHONE]        | Regex        | No  | Yes | Yes |
| Product     | [PRODUCT]      | Spacy        | Yes | Yes | No  |
| Quantity    | [QUANTITY]     | Spacy        | Yes | Yes | Yes |
| Time        | [TIME]         | Spacy        | Yes | Yes | Yes |
| Work of Art | [WORK_OF_ART]  | Spacy        | Yes | Yes | Yes |
| Zip Code    | [ZIP]          | Regex        | No  | Yes | Yes |

## Data Files

The [data/](data/) directory contains a number of files that are used to anonymize recognized entities. As additional entity types are added for different geographies and languages, the number and size of files will grow. Please see the [data file README](data/README.md) for more information.

## License

Please see the [LICENSE](LICENSE)

## Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the MIT license, shall
be licensed as above, without any additional terms or conditions.

Please see the [Contribution Guidelines](CONTRIBUTING.md).

## Authors

Jonathan Eisenzopf

## Copyright

Copyright 2020, Jonathan Eisenzopf, All rights reserved.

## Contributors

Thanks to [@kavdev](https://github.com/kavdev) for reviewing the code and submitting bug fixes.
Thanks to [@wmjg-alt](https://github.com/wmjg-alt) for adding context to anonymization functions.
