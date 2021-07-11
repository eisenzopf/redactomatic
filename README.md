# RedactoMatic

RedactoMatic is a command-line Python script that removes personally identifiable information (PII) from conversation data between agents and customers or bots and customers. It works with transcribed voice calls AND chat logs in a CSV format.

## Purpose

Many companies have security, privacy, and regulatory standards that require them to mask and/or remove PII information before it can be used and shared for data science purposes internally or externally. Redactomatic has been tested with NICE Nexidia voice transcriptions as well as LivePerson chat logs. I fully expect that it will work with other voice transcription, speech to text, live chat, chatbot, and IVR vendors with some work. I plan to add the ability to specify a particular vendor as I am provided with new vendor examples. Please let me know if you'd like me to add support for a particular vendor and I will be happy to do so. I only need a small data sample for testing purposes to add support for new vendors. I am especially interested in samples for Nuance, Avaya, Genesys, Cisco, and Verint. Please report bugs and feel free to make feature requests.

## How it works

Redactomatic is a multi-pass redaction tool with an optional anonymization function. The first redaction pass utilizes the Spacy 2 named entity recognition library. The Subsequent passes utilize regular expressions. The reason two passes are needed is that Spacy does not always match every entity that it needs to. The second pass usually catches what Spacy misses. However, we can't guarantee that it will catch every entity. Testing and validating the output for your data is highly recommended.

### Redaction

It currently assumes that each row in the input CSV file specified by *--inputfile* consists of a piece of text in the *--column* command line parameter. It does not currently support other input formats like JSON. Only one column may be specifed at a time from the command line and no other columns will be reviewed other than the one that has been specified. The script writes a new CSV file specified by *--outputfile* command-line parameter. Other than the column that is redacted and specified by *--column*, the output CSV will be in the same format with the same information as the inputfile. As Redactomatic processes each row of an input CSV file, it replaces each recognized entity in the text with an entity type tag such as **[PHONE]**, **[ZIP]**, or **[CARDINAL**.

### Anonymization

If the optional command-line *--anonymize* switch is included, Redactomatic will replace all entity type tags with a randomized value. Numerical entity tags are anonymized using a random number generator. Text based entity tags are replaced using a random value from a corresponding data file in the [data/](data/) directory of this distribution.

## Installation

To install RedactoMatic, run:

```sh
sh setup.sh
```

This will install required Python libraries and download the small (en_core_web_sm) and large (en_core_web_lg) Spacy models.

## Usage

The current iteration of the code expects you to provide a CSV file from the commandline.

```sh
usage: redactomatic.py [-h] --column COLUMN --idcolumn COLUMN --inputfile INPUTFILE [INPUTFILE ...] --outputfile OUTPUTFILE [--anonymize] [--large]
```

### Basic Example

You can specify one or more input files but only one output file. You must also specify which column in the input CSV(s) to redact. For example, if the CSV input file(s) contain text in the 2nd column that you would like to redact, you would set the  *--column* flag to 2.

```sh
Ex.: python redactomatic.py --column 2 --inputfile input.csv --outputfile output.csv
```

### Anonymization Example

You can optionally anonymize redacted information by including the *--anonymize* switch. This replaces the redaction entity tags with a randomized value as described above.

```sh
Ex.: python redactomatic.py --column 2 --inputfile input.csv --outputfile output.csv --anonymize
```

### Large NER Model Example

By default, Redactomatic will use the Spacy 2 *en_core_web_sm* NER model. It's fast but does not work as well as the larger *en_core_web_lg* NER model. You can tell Redactomatic to use the larger model with the *--large* switch.

```sh
Ex.: python redactomatic.py --column 2 --inputfile input.csv --outputfile output.csv --large
```

## Supported Languages and Regions

Redactomatic currently supports English. Most entities support the US and Canada. If you would like to contribute additional languages and regions, please contact me.

## Supported Entities

The following entities are supported by Redactomatic. The Spacy [English NER model](https://spacy.io/models/en) is trained from the [Ontonotes 5.0 corpus](https://catalog.ldc.upenn.edu/docs/LDC2013T19/OntoNotes-Release-5.0.pdf) and therefore uses the 18 entity types from that corpus plus the additional entity types that were added to Redactomatic. The *[LAUGHTER]* tag is specific to NICE Nexidia transcription. Some numeric types such as *[ADDRESS]*, *[CCARD]*, and *[PHONE]* are not supported for voice transcriptions yet. However, they will still end up being redacted by *[ORDINAL]* or *[CARDINAL]* entity types. If an entity cannot be anonymized, in the case of a text entity, the redaction tag will be deleted and replaced with an empty string; in the case of numeric entity types like *[CCARD]* and *[ZIP]*, the numbers will be replaced by randomly generated cardinals.

| Entity Type | Redaction Tag  | Parsers      | Voice Support | Chat Support | Can be Anonymized |
|-------------|----------------|--------------|-----|-----|-----|
| Address     | [ADDRESS]      | Regex        | No  | Yes | No  |
| Credit Card Number | [CCARD] | Regex        | No  | Yes | No  |
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
| Percent     | [PERCENT]      | Spact        | Yes | Yes | No  |
| Person      | [PERSON]       | Spacy        | Yes | Yes | Yes |
| Phone       | [PHONE]        | Regex        | No  | Yes | No  |
| Product     | [PRODUCT]      | Spacy        | Yes | Yes | No  |
| Quantity    | [QUANTITY]     | Spacy        | Yes | Yes | No  |
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
