# RedactoMatic

RedactoMatic is a command-line Python script that removes personally identifiable information (PII) from conversation data between agents and customers or bots and customers. It works with transcribed voice calls AND chat logs in a CSV format.

## Purpose

Many companies have security, privacy, and regulatory standards that require them to mask and/or remove PII information before it can be used and shared for data science purposes internally or externally. Redactomatic has been tested with NICE Nexidia voice transcriptions as well as LivePerson chat logs. I fully expect that it will work with other voice transcription, speech to text, live chat, chatbot, and IVR vendors with some work. I plan to add the ability to specify a particular vendor as I am provided with new vendor examples. Please let me know if you'd like me to add support for a particular vendor and I will be happy to do so. I only need a small data sample for testing purposes to add support for new vendors. I am especially interested in samples for Nuance, Avaya, Genesys, Cisco, and Verint. Please report bugs and feel free to make feature requests.

## How it works

Redactomatic is a multi-pass redaction tool with an optional anonymization function and reads in CSV files as input. When PII is detected, it is removed and replaced with an entity tag, like **[ORDINAL]**. If the `--anonymization` flag is added, Redactomatic will replace PII entity tags with randomized values. For example, **[PERSON]** might be replaced by the name John. This is useful when sharing datasets that need PII removed but also need some real world like value.  By default, a redaction pass will be made using the Spacy 3 named entity recognition library.  You have the option of using the large Spacy library if you add the `--large` command-line parameter, which will increase the number of correctly recognized PII entities, but will also take longer. In addition to the Spacy NER pass, passes are made using regular expressions. The reason multiple passes are needed is that machine learning libraries like Spacy are not reliable and cannot catch all PII. That is obviously not acceptable for financial services and other regulated industries. While large companies use this tool for mission critical applications, please test and validate the results before using it in production and report any anomalies to the authors.

The tool is completely configurable.  Redaction and anonymization rules can be added or removed and new rules can be defined.  The redaction and anonymization rules are defined by JSON or YAML files.  By default these are looked for in the [rules/](../rules/) directory.  The

### Redaction

Redactomatic assumes that each row in the input CSV file specified by `--inputfile`. Only two columns in this file are used.

- The text to be redacted.  Specified by either the `--column` command line parameter or the `--header` and  `--columnname` parameter (which is '**text**' by default)

- A unique identifier for the current conversation.  The `--idcolumn` command line parameter or the `--header` and `--idcolumnname` parameter (which is '**conversation_id**' by default)

Redactomatic does not currently support other input formats like JSON.

The script writes a new CSV file specified by the `--outputfile` command-line parameter. Other than the text column that is redacted, the output CSV will be in the same format with the same information as the inputfile.

As Redactomatic processes each row of an input CSV file, it replaces each recognized entity in the text with an entity type tag such as **[PHONE-*nn*]**, **[ZIP-nn]**, or **[CARDINAL-*nn*]**. The index number ***nn*** identifies unique occurences of specific entities.  For example if the name 'David' appears more than once in during the conversation each instance of it will be assigned the same index number.

### Anonymization

If the optional command-line `--anonymize` switch is included, Redactomatic will replace all entity type tags with a randomized value.  By default, subsequent occurrences of the same entities with the same index number in a given conversation will be assigned the same value.  This helps the anonymized conversation retain continuity.

Anonymization functions are supplied and you can add specific ones if required.  By default alpha-numerical entity tags are anonymized using a random number/text generator based on patterns (regex).

Text based entity tags are replaced using a random value from a corresponding data file in the data/ directory of this distribution.

There are quite a few different anonymization types, but not all PII entity types are supported. Please refer to the list of supported PII entities below.  Remember you can add support for new PII types via the rules file.

### Support for voice and text

Redactomatic supports both transcribed voice and chat conversation text types. This is especially important as most other tools do not properly support ordinals, cardinals, currency, and other numeric types that used spelled numbers generated by most speech to text engines. For example, *five nine six eight* might not be correctly recognized and redacted by some other tools. Redactomatic supports both numeric and spelled cardinals and ordinals and operates in either *text* or *voice* mode as specified by the `--modality` command-line parameter. If you are redacting transcribed voice text files use the `--modality voice` switch on the command line. For chat conversation text use the `--modality text` switch.

### Dictionary of phrases to ignore

Redactomatic includes the ability to ignore key phrases. This comes in handy when redactomatic would otherwise tag something as PII that shouldn't be. For example, if a conversation includes the phrase, *"May I please have your first and last name"*, is the word *first* an ordinal? No it's not. Under normal conditions, Redactomatic would redact the word *first*. In the case where we use the `--anonymize` flag, it would assign a random ordinal in it's place. For example, the previous phrase might have been replaced with, *"May I please have your eighth and last name"*. This obviously doesn't make any sense. We can solve this problem by configuring Redactomatic to ignore the phrase, *"first and"*.

Redactomatic implements this feature by first redacting the text to be ignored and then restoring it during anonymization.

By default, a special redaction entity  *\_IGNORE\_*  is defined in the file [rules/ignore.yml](../rules/ignore.yml)   





```
entities:
  _IGNORE_:
    redactor:
      redact.RedactorRegex
      text:
        phrase-list:
          - first name
          - first and
          - today
          - yesterday
          - CV
          - tomorrow
      voice:
        phrase-list:
          - first name
          - first and
          - today
          - yesterday
          - CV
          - tomorrow
          - (one|two|three|four|five|siz|seven|eight|nine) moment(s)+
          - (one|two|three|four|five|siz|seven|eight|nine) minute(s)+
          - (one|two|three|four|five|siz|seven|eight|nine) second(s)+
          - etc. etc....
    anonymizer:
      model-class: anonymize.AnonRestoreEntityText
```

**Example af a default `_IGNORE_ `entity showing the use of regular expressions.**

If you are interested in how this is implemented, notice how the definition of the  *\_IGNORE\_*  rule uses the regular expression redactor `redact.RedactorRegex`  to first redact the words to be ingored.  It then uses the anonymizer `anonymize.AnonRestoreEntityText `to restore the text again.  In addition to this the entity also needs to be added to the *`always -anonymize`* section of the configuration to ensure that it is anonymized even when the -`--anonymize` option is not set.    Each of these steps are explained in detail later in this document.

To change the ignore phrases or patterns you can edit this default file. Alternatively you can redefine the whole `_IGNORE_` entity definition in a custom rule which will override the default definition.   

You can use any kind of redactor to identify phrases to be ignored, and you can have more than one entity that is ignored.  To add extra ''ignore' entities define it in the custom configuration using an entities definition, ensuring that the anonymizer has the `model-class: anonymize.AnonRestoreEntityText` .   Then add this entity name to the `always-anonymize ` section of the configuration.

## Installation

To install RedactoMatic, run:

```sh
sh setup.sh
```

This will install required Python libraries and download the small (en_core_web_sm) and large (en_core_web_lg) Spacy models.

## Test

To test the new installation run:

```sh
cd test-scripts
sh test-redactomatic.sh
```

This should report a number of clean test results as shown below:

```
PASS: Is the regex test output file correct?
PASS: Is the L2 redacted text output file correct?
PASS: Is the L2 redacted and anonymized text output file correct?
PASS: Is the L2 voice redaction log correct?
PASS: Is the L2 redacted voice output file correct
PASS: Is the L2 redacted and anonymized voice output file correct?
PASS: Is the pure text anonymization file correct?
PASS: Is the pure voice anonymization file correct?
PASS: Is the checker debug file correct?
PASS: Is the checker report file correct?
PASS: Is sample-1 time correction output file as expected?
```

## Hardware Requirements

By default, Redactomatic will use the Spacy small ML model. However, if you plan to use the large model via the `--large` command line flag, be sure that the machine is utilizing a GPU capable of running large Transformer models.

Also, its easy to run out of memory.  if you don't chunk the file then you will need memory at least four times as large as the input data file. You can reduce this requirement by using the `--chunksize` command line option and process the file in smaller chunks at a time.

## Usage

Redactomatic needs at a minimum:

1. The name of the input conversation file (`--inputfile`) in CSV format,
2. The modaility (`--modality` which must be voice or text)
3. Either:
   
   1. The column in the CSV containing the text to redact (`--column`), the column containing the conversation ID (`--idcolumn`).
   
   2. The` --header` option which uses the first line of the CSV file as headers.  By default this will look for the columns named 'text' and 'conversation_id'.
4. The name of the output file (`--outputfile`) 

```
usage: redactomatic.py 
      [-h] 
      [--version]
      [--column COLUMN] 
      [--idcolumn IDCOLUMN] 
      [--inputfile INPUTFILE [INPUTFILE ..  [--outputfile OUTPUTFILE] 
      [--modality {text,voice}] 
      [--redact]
      [--no-redact] 
      [--anonymize] 
      [--no-anonymize]
      [--default_rules]
      [--no-default_rules]
      [--large] 
      [--log LOG]
      [--uppercase] 
      [--level LEVEL] 
      [--seed SEED] 
      [--rulefile [RULEFILE [RULEFILE ...]]] 
      [--regextest] 
      [--testoutputfile TESTOUTPUTFILE] 
      [--chunksize CHUNKSIZE] 
      [--chunklimit CHUNKLIMIT]  
      [--header]
      [--columnname COLUMNNAME] 
      [--idcolumnname IDCOLUMNNAME]
      [--verbose]
      [--no-verbose]
      [--traceback]
```
### Command Line Parameters
| Paramter            | Description                                                                                                                                        | Required/Default |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| `-h`,`--help`       | Print the usage                                                                                                                                    | *TERMINAL*       |         
| `--header`          | If set to True then the first line of the input files will be treated as a header and the output file will also have a header line. `              | no-header (*)    |
| `--column`          | The column number containing the text to redact                                                                                                    | *REQUIRED* (*)   |
| `--idcolumn`        | the column number containing the unique conversation id                                                                                            | *REQUIRED* (*)   |
| `--columnname`      | The name of the column to be redacted (used with `--header`)                                                                                       | text             |
| `--idcolumname`     | The name of the column containing the conversation IDs (used with `--header`)                                                                      | conversation_id  |
| `--inputfile`       | The filename containing the conversations to process                                                                                               | *REQUIRED*       |
| `--outputfile`      | The filename that will contain the redacted output                                                                                                 | *REQUIRED*       |
| `--modality`        | Can be voice or text depending on the type of conversations contained in the inputfile                                                             | *REQUIRED*       |
| `--chunksize`       | The number of lines to read in as a chunk before processing them.                                                                                  | 100000           |
| `--chunklimit`      | An integer number of chunks to process before stopping.   Included primarily to support benchmarking.   Default=None (i.e. all of them)            | None             |
| `--anonymize`</br>`--no-anonymize`  | Replace redaction tags with randomized values. Useful if you need simulated data.                                                  | no-anonymize     |
| `--redact`</br>`--no-redact`      | Redact the text (This is the default)                                                                                                | redact           |
| `--defaultrules` </br> `--no-defaultrules` | Use the default rules in addition to any rules specified using `--rulefile`                                                 | defaultrules     |
| `--large`           | Use the large Spacy language model instead of the small one. Not recommended unless you have a GPU or don't mind waiting a long time.              | small            |
| `--log`             | Logs all recognized entities that have been redacted including the unique entity ID and the entity value. Can be use for audit purposes.           | *OPTIONAL*       |
| `--uppercase`       | Convert all letters to uppercase. Useful when using NICE or other speech to text engines that transcribe voice to all caps.                        | *OPTIONAL*       |
| `--level`           | The redaction level. Choose 1,2, or 3 or a any custom level. See documentation below on what the levels mean.                                      | '2'              |
| `--seed`            | A seed value for anonymization random selection; default is None i.e. truly random.  Use this if you want deterministic results.                   | *OPTIONAL*       |
|`--rulefile`         | A list of filenames defining custom rules in YML or JSON. Add to or override default rules (see --defaultrules).  These are globbable.             | *OPTIONAL*       |
| `--regextest`       | Test the regular rexpressions defiend in the regex-test rules prior to any other processing.                                                       | *OPTIONAL*       |
| `--testoutputfile`  | The file to save the regular expression test results in.                                                                                           | *OPTIONAL*       |
| `--traceback`</br>`--no-traceback  `   | Give traceback information when an exceptin causes the program to halt.                                                         | no-traceback     |
| `--version`           |         Print the version and exit                       | *TERMINAL*       |
| `--verbose`</br>`--no-verbose` | Print the status of processing steps to standard output.                                                                                | verbose          |

(\*) ** *The command must either specifiy the --header option or give the --column and --idcolumn options.* **

### Example 1: Redact a text file with no header

The following command will use the sample input file included in the Redactomatic distribution [data/sample_data.csv](data/sample_data.csv) and create an output file called output.csv:

```sh
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile output.csv
```

If you review the sample data file, you will notice that the first column contains the conversation ID and that the fourth column contains the text we want to redact.

### Example 2: Anonymize a voice transcribed file with anonymization with a header

In this second example, we are going to use a sample voice transcribed conversation and we are going to also anonymize the PII tags. This will replaced all PII with randomized values with context. When we say "with context", we mean that Redactomatic temporarily remembers when the same PII entity value has been used in the conversation and will replace it with the same randomized value. For example, If Mary is talking to John, we would first redact Mary as [PERSON-1] and John as [PERSON-2]. If we turn on anonymization via the `--anonymization` command-line parameter, Redactomatic will replace all instances of [PERSON-1] with the same randomized name so that the anonymized output is more coherent.

```sh
python3 redactomatic.py --header --modality voice --inputfile ./data/sample_data.csv --outputfile output.csv --anonymize
```

Notice that the *`--modality`* parameter is now *voice* and that we have added the *`--anonymize`* parameter, which replaces all redaction tags with randomized values. note also that there is a `--header` option instead of ` --column` and `--idcolumn` options

### Example 3: Using the large NER Model Example

By default, Redactomatic will use the Spacy 3 *en_core_web_sm* NER model. It's fast but does not work as well as the larger *en_core_web_lg* NER model. You can tell Redactomatic to use the larger model with the `--large` switch.

```sh
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile output.csv --large
```

### Example 4: Logging recognized PII values

In some cases, your security officer may want to see proof that Redactomatic has successfully removed all instances of PII data. You can turn on an audit log with the `--log` switch, but please be sure to secure the file because it will contain PII information. This feature will write a CSV file containing the redaction tag and PII entity value, one per row.

```sh
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile output.csv --log audit.csv
```

### Example 5: Redaction and Anonymization in 2 separate passes

In some cases, you may want to redact a data file and inspect it before you anonymize it. This can be done by first redacting the data file, inspecting the data, and then using the output of redaction step as input to the anonymization step.

```sh
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile output.csv
```

```sh
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/output.csv --outputfile output2.csv --anonymize --no-redact
```

## Redaction Levels

You can define the entities that will be redacted (and hence anonymized). By default three levels are defined '1', '2', and '3'.  Level 1 means that Redactomatic will only use the machine learning NER parser, which captures many entities but is not reliable and does not match addresses, phone numbers, SSN, and other kinds of numbers that are probably important to recognize. Level 2 is the default level and matches most PII entities. However, it can miss numbers that aren't supported or are formatting in a way that Redactomatic hasn't seen before. If maximum security is needed where all kinds of numbers are always redacted whether they are a recognized type or not, you should use Level 3.

You can also define your own levels by editing the [config.yml](../rules/config.yml) or better still adding your own custom configuration file.   For example if you define the redaction labels that you want to redact in a new subsection of the `'level'` section called called `'custom' `then the command line switch `--level custom` will cause this new set of labels to be redacted or anonymized.

## Supported Languages and Regions

Redactomatic currently supports English. Most entities support the US and Canada. If you would like to contribute additional languages and regions, we welcome the contribution.

## Supported Entities

The following entities are supported by default by Redactomatic. The Spacy [English NER model](https://spacy.io/models/en) is trained from the [Ontonotes 5.0 corpus](https://catalog.ldc.upenn.edu/docs/LDC2013T19/OntoNotes-Release-5.0.pdf) and therefore uses the 18 entity types from that corpus.  Additional entity types are also added by Redactomatic. The *[LAUGHTER]* tag is specific to NICE Nexidia transcription. Some numeric types such as *[ADDRESS]*, are not supported for voice transcriptions yet.  If an entity cannot be anonymized, in the case of a text entity, the redaction tag will be deleted and replaced with an empty string.

The following entities are supported by the core configuration of redactomatic.  Other custom entities can be added by the user.

| Entity Type                                      | Redaction Tag | Parsers      | Voice Support | Chat Support | Can be Anonymized |
| ------------------------------------------------ | ------------- | ------------ | ------------- | ------------ | ----------------- |
| Address                                          | [ADDRESS]     | Regex        | No            | Yes          | Yes               |
| Credit Card Number                               | [CCARD]       | Regex        | Yes           | Yes          | Yes               |
| Cardinal                                         | [CARDINAL]    | Spacy, Regex | Yes           | Yes          | Yes               |
| Date                                             | [DATE]        | Spacy        | Yes           | Yes          | Yes               |
| Email                                            | [EMAIL]       | Regex        | No            | Yes          | Yes               |
| Event                                            | [EVENT]       | Spacy        | Yes           | Yes          | Yes               |
| Facility                                         | [FAC]         | Spacy        | Yes           | Yes          | No                |
| Country, City, State                             | [GPE]         | Spacy        | Yes           | Yes          | Yes               |
| Language                                         | [LANGUAGE]    | Spacy        | Yes           | Yes          | Yes               |
| Laughter                                         | [LAUGHTER]    | NICE         | Yes           | No           | No                |
| Law                                              | [LAW]         | Spacy        | Yes           | Yes          | No                |
| Location                                         | [LOC]         | Spacy        | Yes           | Yes          | Yes               |
| Money                                            | [MONEY]       | Spacy        | Yes           | Yes          | Yes               |
| Nationality, Religious or Political Organization | [NORP]        | Spacy        | Yes           | Yes          | Yes               |
| Organization                                     | [ORG]         | Spacy        | Yes           | Yes          | Yes               |
| Ordinal                                          | [ORDINAL]     | Spacy, Regex | Yes           | Yes          | Yes               |
| Percent                                          | [PERCENT]     | Spacy        | Yes           | Yes          | Yes               |
| Person                                           | [PERSON]      | Spacy        | Yes           | Yes          | Yes               |
| Phone                                            | [PHONE]       | Regex        | Yes           | Yes          | Yes               |
| Product                                          | [PRODUCT]     | Spacy        | Yes           | Yes          | Yes               |
| Quantity                                         | [QUANTITY]    | Spacy        | Yes           | Yes          | Yes               |
| SSN                                              | [SSN]         | Regex        | Yes           | Yes          | Yes               |
| Time                                             | [TIME]        | Spacy        | Yes           | Yes          | Yes               |
| Work of Art                                      | [WORK_OF_ART] | Spacy        | Yes           | Yes          | Yes               |
| Zip Code                                         | [ZIP]         | Regex        | Yes           | Yes          | Yes               |
| PIN Code                                         | [PIN]         | Regex        | Yes           | Yes          | Yes               |

## Data Files

### rules/

The [rules/](../rules/) directory contains default files used to define the core redaction.  

- [config.yml](../rules/config.yml) - fields to be redacted, anonymized, levels and anonymyzation order

- [core-defs.yml](../rules/core-defs.yml)- definitions for redaction and anonymization of all core fields

- [ignore.yml](../rules/ignore.yml) - an example file used to specify phrases to be protected

It is important to note that the core rules can all be re-defined or overriden. See below regarding the `--defaulrules` and `--rulesfile` options.

### data/

The [data/](../data/) directory contains a number of files that are used to anonymize recognized entities. As additional entity types are added for different geographies and languages, the number and size of files will grow. Please see the [data file README](../data/README.md) for more information.  The anonymization class AnonPhraseList and its sub-classes can be used to create your own anonymization types based on your own data files.

### test-scripts/

The [test-scripts/](../test-scripts/) directory contains a file [test-redactomatic.sh](../test-scripts/test-redactomatic.sh) which can be used to test the installation of redactomatic.

### test-expected/

The [test-expected/](../test-expected/) directory contains a number of files that are used to verify the test results (see the Test section). These files are not neccessary to the operation of Redactomatic.

## Creating and Customizing Models

### Loading default and custom rule files.

By default all of the files named `rules/*.json` or `rules/*.yml` are loaded.  If you put additional `.yml` or `.json` files into the default rules/ directory then they will be also be treated as default rules. We recommend that you use the `--rulesfile` option rather than changing the core configuration.

The `--rulesfile` option can be used used to load custom rules files in addition to the core rules files. These JSON or YML files can be placed anywhere, for example in your own custom rules directory. The paths that you give to the` --rulesfile` option are globbed so you can define things like `--rulefile myrulesdir/*.yml`

The `--no-defaultrules` option suppresses the core rules completely. If you use this option then you must define all the rules that are to be used using the `--rulesfile` option.  This allows you to completely ignore the default rules supplied with redactomatic, or specify exactly which of the default files you want to include in your configuration.  We do not recommend using this option unless you are an experienced user. 

Redactomatic configuration files can be in YAML format or JSON format and can be intermixed.  Note also that regular expressions are almost impossible to express in JSON. Use YAML for configuration containing regular expressions.

### Example Custom Rule File

```
  # Define a custom redaction level including our own additional ignore rules and email rules
  level:
      'my_custom_level': 
          - _IGNORE_
          - _CUSTOM_IGNORE_
          - _SPACY_
          - PHONE
          - PERSON
          - ADDRESS
          - CCARD
          - MONEY
          - SSN
          - PIN
          - CUSTOM_EMAIL

  # Restore phrases in the existing _IGNORE_ rule and also our new _CUSTOM_IGNORE_ rule.
  always-anonymize:
      - _IGNORE_
      - _CUSTOM_IGNORE_

  # Add _CUSTOM_IGNORE_ and CUSTOM_EMAIL rules to the core redaction order.
  redaction-order:
      - _IGNORE_
      - _CUSTOM_IGNORE_
      - PERSON
      - ADDRESS
      - CCARD
      - PHONE
      - SSN
      - ZIP
      - EMAIL
      - MONEY
      - LOC
      - DATE
      - EVENT
      - FAC
      - GPE
      - LANGUAGE
      - LAUGHTER
      - LAW
      - NORP
      - ORG
      - PERCENT
      - PRODUCT
      - QUANTITY
      - TIME
      - PIN
      - CUSTOM_EMAIL
      - _SPACY_
      - ORDINAL
      - CARDINAL

  #Map XML labels in your input that are already anonymized to built-in anonymization entities.
  token-map:
      PIN: [ "<PIN\/>", "<SEC_CODE\/>" ]
      CCARD: [ "<ccNum\/>" ]

  #Define _CUSTOM_IGNORE_ and CUSTOM_EMAIL entity rules.
  entities:
    _CUSTOM_IGNORE_:
      redactor:
        model-class: redact.RedactorRegex
        text:
          regex:
            - world one bank
        voice:
          regex:
            - world one bank
      anonymizer:
        model-class: anonymize.AnonRestoreEntityText

    CUSTOM_EMAIL:
      redactor:
        model-class: redact.RedactorRegex
        text:
          regex: ['[a-z]+@.onebank.com']
        voice:
          regex: ['[a-z]+ underscore [a-z]+ at one bank dot com']
      anonymizer:
        model-class: anonymize.AnonRegex
        text:
          regex: ['[a-z]{5}_[a-z]{5}@.onebank.com']
        voice:
          regex: ['[a-z]{5} underscore [a-z]{5} at one bank dot com']
```
**Example custom.yml rules file** 

An example custom rule file is shown above.  It can be loaded using the option `--rulesfile custom.yml`.  When redactomatic ruls it first loads the core rules files and then it loads the custom rules files.

The custom rules will be overlaid on top of the core rules.  Rules with the same ditionary path as the core rules will be overridden.   Rules with novel paths will be added into the relevant sections.

Reading the custom rules file above will do the following :

- Add an extra level `my_custom_level` to the built in list of '1', '2', and '3'.  This can then be invoked using the switch `--level my_custom_level`.
- Override the `always-anonymize` section to ensure that we restore the phrases identified using the `_CUSTOM_IGNORE_` rule in addition to keeping the core ones.
Override the `redaction-order` section to include the new rules `_CUSTOM_IGNORE_` and `_CUSTOM_EMAIL_`.  Note how we keep entities that are not defined in `my-custom-level` level so that core levels `1`, `2` and `3` continue to work if needed. If you don't want to keep this backwards compatiblity then its ok to include just the entities that are in the custom level.
- Map XML labels `\<PIN/>`, `\<SEC_CODE/>` and `\<ccNum/>` in the input data to the build in anonymizer labels.  This enables the anonymization of data that was already redacted by an external process prior to being input to redactomatic.
- Define a new entity `_CUSTOM_IGNORE_` which looks for the phrase *'one world bank'* and ensures that this phrase is never redacted.  
- Define a new entity `CUSTOM_EMAIL` which redacts email like *'amy_grant@onebank.com'* or spoken input of the form *'amy underscore grant at one bank dot com'*.   An anonymizer is also defined which anonymizes this entity to strings like *'anvfg_kujyg@onebank.com'* for text or *'anvfg underscore kujyg at one bank dot com'* for voice..

The following sections describe exactly how this configuration file works, and give a full explanation for how to use other features in the tool in your custom configurations.

### Top-level rules

The configuration can be spread arbitrarily across multiple files which are simply overlaid on top of each when they are read.  

The top-level dictionary keys are as follows:

- level
- redaction-order
- always-anonymize
- anonymization-order
- anon-map
- token-map
- entities
- regex
- regex-test

Each entry in a configuration dictionary file must have one of these keys as its head.  Configuration files are treated as a single common namespace.  This means that defintions can be mixed into one file or arbitrarily spread across multiple files.  You will not be warned however if one of your rules is overwriting another one so take care with naming.

In the default configuration in the release the top-six keys are present in the file [config.yml](../rules/config.yml) and the remaining two keys are defined in the file [core-defs.yml](../rules/core-defs.yml).

### level

```
level:
    '1':
        - _IGNORE_
        - _SPACY_
        - PHONE
        - PERSON
        - ADDRESS
        - CCARD
        - MONEY
        - SSN
        - PIN
    '2':
        - _IGNORE_
        - _SPACY_
        - PHONE
```

**Example level definition (YAML)**

Any number of level definitions may be set.  The defalt configuration files contain three level keys '1', '2' and '3', an extract of which is shown above.     The ` --level` option uses the entity list that is found in the relevant matching section.  Level keys do not need to be numeric.  You can add as many levels as you want.

To define a custom level you can add a custom configuraton file with its own level entry as shown below:

```
level:
    'my_custom_level':
        - _IGNORE_
        - _SPACY_
        - CCARD
        - MONEY
        - SSN
        - PIN
        - CUSTOM_ENITY1
        - CUSTOM_ENITY2
```

### redaction-order

```
redaction-order:
    - _IGNORE_
    - PERSON
    - ADDRESS
    - SSN
    -  ...
```

**Example redaction-order (YAML)**

The `redaction-order` section lists the order in which the redactor functions for the entities are computed (See the entities section).  This section can be re-ordered if you want certain redactors to run before others.

If a label is not in the `redaction-order` then it cannot be anonymized or redacted even if it is specified in the `level `section.

You will notice the label **\_SPACY\_**.  This defines where the NL ML Spacy model is run in the order of execution. By default it is run after the other rules have been run but it could be moved to any position in the list.

The other special label ***\_IGNORE\_*** is uses to run a redactor that labels areas of text to be protected so that it can be restored at a later date.

The redaction order is defined by default in the [config.yml](../rules/config.yml) file.   To change this order, edit the default file or define a custom config file with its own redaction-order entry in it.  Custom configuration files are loaded after the default configuraton files so the custom entry will override the definition in the default files.

### always-anonymize

```
always-anonymize:
    - _IGNORE_
```

**Default always-anonymize (YAML) rule**

The `always-anonymize` section lists entities that are anonymized even if the `--anonymize` flag is not set. This allows entities that catch text to be ignored to restore them afterwards even if anonymization is not performed.

This section is optional and if it is omitted then the rule shown above is implemented by default. This is to provide backwards compatibility. It is recommended that this section is included for clarity. If this section is defined then it overrides the default. This means that you should explicitly include the *\_IGNORE\_* entity if you with to use this entity to protect and restore text.

The always-anonymize section can be used to anonymize entities with any kind of anonymizer defined. This feature can be used for things other than restoring ignored text. You can also have multiple entities in this section if desired.

The default `always-anonymize` rule is defined in the `../rules/config.ym`l file.  This rule can be overriden using a custom configuration file.

### anonymization-order (optional)

```
anonymization-order:
    - _IGNORE_
    - PERSON
    - ADDRESS
    - SSN
    -  ...
```

**Example anonymization-order (YAML)**

The `anonymization-order` section of the rules file is optional.  If it is not defined then the order of the entities in the `redaction-order` section is used to determine the order of anonymization.  In the current implementation of redactomatic the order of anonymization is not important so this section is usually omitted.  It is included to future-proof the tool should the order of anonymization ever be important.

The default `anonymization-order ` rule is defined in the `../rules/config.ym`l file. This rule can be overriden using a custom configuration file.

### anon-map

```
anon-map:
    ADDRESS: [ streetAddress ]
    CARDINAL: [ DIGITS, digits ]
    CCARD: [ creditCardNumber, ccNum ]
    CREDENTIALS: [ credentials ]
    DATE: [ expDate ]
    ...
```

**Example anon-map (YAML)**

The `anon-map` section defines which redaction labels are aliases for redaction entities.   Consider the following text that has already been redacted.  The address has been converted into the label **[streetAddress]** which is not a native entity that is defined in the ```entities``` section of the configuration.  It is also not referenced in the ```level``` or ```redacton-order```.

```
My mother lives at [streetAddress].
```

The entry in the anon-map shown above means that redaction labels in the text of the form **[streetAddress]** or **[streetAddress-nnn]** will be anonymized using the rules defined for the entity **ADDRESS**.

You may be wondering why this is neccessary and how the redacted text can contain labels that are not defined in the configuration files.  There are two main reasons this can occur.

* The input file was redacted by another process and we are using Redactomatic to anonymize the resulting text.  For example a company may have their own redaction algorithm but want to use Redactomatic to put plausible text back into the transcripts.

* The label was generated by special redactor processes such as `_SPACY_` that add multiple label types and you want to share anonymizer rules for these labels.

If redactomatic is expecting to anonymize an entity and does not find an entry for it in the anon-map then it will assume that the entity maps to itself.  However if an entity is defined in the key of the anon-map then only the entities found in the map will use the anonymizer defined for that entity.

```
anon-map:
        ENTITY1: [ "ENTITY1" ]               # Not needed to map ENTITY1 to itself
        ENTITY2: [ ENTITY2", "ENTITY3" ]    # Not needed to map ENTITY2 to ENTITY2
```

It is is possible to supress the use of a particular anonymizer for an entity by mapping it to an empty set of entities.  It is also possible to use a different anonymizer to anonymize that entity instead.

```
anon-map:
    ENTITY1: []           #Suppress use of the anonymizer for ENTITY1
    ENTITY2: [ENTITY1]    #Use anonymizer for ENTITY2 for ENTITY1
```

Redactomatic does not prevent you from mapping an entity to more than one anonymizer but it is not a useful thing to attempt.  If this does happen then Redactomatic will map the entity with the first mapping that it finds when it follows the` anonymization-order `(or `redaction-order` if `anonymization-order` is not specified).  It will then try to map it using later anonymizers but will not find the entity because it will already have been anonymized.

The default `anon-map` rule is defined in the `../rules/config.ym`l file but it is empty. This rule can be overriden using a custom configuration file.

### token-map

```
token-map:
    ZIP: [ "<ZIP\/>" ]
    PIN: [ "<PIN\/>", "<CVV\/>" ]
    CCARD: [ "<ccNum\/>" ]
    DATE: [ "<expDate\/>" ]
```

**Example token-map (YAML)**
Token maps are very like anon-maps but are used to map entity labels that are not in the correct Redactomatic format for anonymization.  They are typically used to anonymize data that has come from programs other than redactomatic. In the example input text below a different redaction algorithm has labelled ZIP codes using XML labels.

```
My mother's ZIP code is <ZIP\/>
```

The token-map above will ensure that this label is anonymized using the entity rules for "ZIP" in the rest of the rules.

The default `token-map` rule is defined in the `../rules/config.ym`l file but it is empty. This rule can be overriden using a custom configuration file.

### regex

```
regex
  ordinal:
    # voice-yes, chat-yes
    - >
    (?x)
    (?(DEFINE)

    (?<one_to_9>
    (fir|seco|thi|four|fif|six|seven|eigh|nin|[1-9])(?:st|nd|rd|th)
    ) # end one_to_9 definition

    (?<ten_to_19>     (?:(?:(ten|eleven|twelf)|((?:thir|four|fif|six|seven|eigh|nine)teen))th|((10|11|12|13|14|15|16|17|18|19)th))
    ) # end ten_to_19 definition

    ... etc. etc. ...

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

    ## Regex rule is defined here.
    (?&bignumber)

    ordinal-text-gen:
    - '1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th'

    ordinal-voice-gen:
    - 'first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth'

    etc.
```

**Example regex ruleset for ORDINAL redaction and anonymization (YAML)**

Regular expressions can be defined in one place in the rule set and referenced by redaction or anonymization rules elsewhere in the rules.

The example above shows extracts from the regex section of the core-def.yml file included in the release. Three rules can be seen, attached to three keys `ordinal`, `ordinal-text-gen`, and`ordinal-voice -gen`.

As can be seen in the next section, the `ordinal `regular expression will be used to define a shared text and voice redactor for an **ORDINAL** entity. Redactomatic currenly support Perl Compatible Regular Expressions (PCRE) for redaction via the `redactor.RedactorRegex` class.  This means that the extremely useful (DEFINE) syntax can be used - amongst other features of PCRE.

The two rules `ordinal-text-gen`, and `ordinal-voice -gen` are used as generative grammars for the anonymizers for the **ORDINAL ** entity for text and voice modalities. The `anonymizer.AnonRegex` class used for this does not currently support PCRE.

The definitions in the `regex `section are just that - they are definitions.  By themselves they do not make anything happen.  In order to be useful they need to be referenced in `regex-id` parameters in the redaction and anonymization sections of the `entities `definitions.

The values of the named id keys in the `regex `section can be a **single pattern** or a **list of patterns**.  The interpretation of what to do with a list of regular expressions is left up to the redactor or anonymizer that uses the regex definition.

#### ?INCLUDE< rule-id >

```
regex
  zero_to_nine-voice:
      - >
        (?<zero_to_nine>
        (?:(one|two|three|four|five|six|seven|eight|nine|zero|oh|0z))
        )

  ccard-voice:
    # chat-yes, voice-no
    (?xi)
      (?(DEFINE)?INCLUDE<zero_to_nine-voice>)
      (^|\s)
      (?<ccard>( ((?&zero_to_nine)\s+){12,15}) (?&zero_to_nine) )
      (?!\s*)?
```

**Example of an ?INCLUDE macro.**

Redactomatic has its own special macro to include a regular expression defined in one rule as a macro in another rule.

In the example given above the regular expression zero_to_nine-voice is just a standard regular expression definition.

In the ccard-voice rule this is then inserted via the macro **?INCLUDE< rule-id >** macro.   This macro is a direct text substitution of the rule in place of the invocation.  Macros can insert other macros but take care not to create infinite recursion.

A default set  `regex`  rules are defined in the `../rules/core-defs.yml`file.  Additional regex rules can be added in custom configuration files.    A defintion of a regex rule in the custom rules file with the same name as a core definition will overwrite the original definition.    You can use this to change individual core regular expressions if you wish to.

### regex-test

```
regex-test:
  ordinal:
    - engine: regex
      flags: [IGNORECASE,DOTALL]
      match-type: ONE_OR_MORE_MATCH
      phrases:
      - 'first and foremost'
      - 'the 10th person to see him'
    - engine: regex
      match-type: NO_MATCHES
      phrases:
      - 'the person who was seconded to the team.'
```

**Example regex-test ruleset for the rule with regex-id 'ordinal' (YAML)**

An optional `regex-test` section can be included which will test individual regular expressions with groups of test phrases.  you can test for exact phrase matches, partial matches, of parts of the phrase, or test that phrases do NOT match.  This is controlled by the `match-type` parameter which can have one of the following values:

- ONE_OR_MORE_MATCH  (Default)
- ONE_OR_MORE_EXACT_MATCH
- ONE_OR_MORE_PARTIAL_MATCH
- ALL_EXACT_MATCH
- ALL_PARTIAL_MATCH
- NO_MATCHES
- NO_EXACT_MATCHES
- NO_PARTIAL_MATCHES

By default the ONE_OR_MORE_MATCH options is used.   This will pass the test if the regular expression finds one or match within the phrase.  Recall that regular expression rules can comprise multiple patterns.

The `flags` parameter behaves as described for `redact.RedactorRegex`.

The `engine` paramter defines whether the match is performed using the 're' or 'regex' module.  The 'regex' module supports PCRE matching and is the default engine if none is specified.

A particularly useful feature of the regex-test is that it stores detailed information about the test results in the file specified by the `--testoutputfile`command line option.

A default set `regextest` rules are defined in the `../rules/core-regex-test.yml`file. Additional regex test rules can be added in custom configuration files.  

### entities

```
entities:
  ORDINAL:
    redactor:
      model-class: redact.RedactorRegex
      text:
        regex-id: ordinal
      voice:
        regex-id: ordinal
    anonymizer:
      model-class: anonymize.AnonRegex
      text:
        regex-id: ordinal-text-gen
      voice:
        regex-id: ordinal-voice-gen
```

**Example defintion for redaction and anonymization of the ORDINAL entity (YAML)**

The entities section of the rules defines algorithms and configuration used to perform redaction and anonymization.

In the example above the rules for redaction and anonymization of the **ORDINAL ** entity can be seen.  `redactor `and `anonymizer `rules must have a `model-class` key defined.  This defines the python module and class name to be used for the transformation.  For example redaction of **ORDINAL ** entities is performed using the class `RedactorRegex `defined in the module `redact.py` included in the release.

Each redactor or anonymizer takes its configuration from the parameters found in the rules. In general a redactor or anonymizer will expect to have a 'voice' or 'text' key containing the definitions for how to process those two modalities.  The expected parameters for a given class however are entirely up to the class itself.

A default set `entities` are defined in the `../rules/core-defs.yml`file.  Additional `entities `can be added in custom configuration files.  Default `entities `can also have their definition overriden in the custom configuration files.

## Built-In Redactor Classes

Redactomatic has three built-in Redactor classes.  New redactors can be added by implementing a new sub-class of the class `redact.RedactorBase`.

### redact.RedactorRegex

```
...
  MYDOMAIN:
    redactor:
      model-class: redact.RedactorRegex
      text:
        regex: ['\d{1-3}\.com']
        regex-id: my-rule-id
        group: my-named-group
        flags: [ ASCII, IGNORECASE, ... ]
      voice:
        ...
```

The `redact.RedactorRegex` class uses a regular expression to match the entity.  The regular expression can be specified via a set of  `regex ` inline patterns, or be a shared rule  with the `regex-id` key in the `regex `section.    The whole regex pattern must match part or all of the phrase.  Then the matching part of the phrase will be redacted with the redaction label (e.g. [MYDOMAIN-23] ).  It is possible to redact only part of the matching area of the phrase but specifying the `group ` parameter.  This can be an integer group number or a named group (using PCRE naming).

Flags for the regular expression match can be specified via the `flags`value.  This is a list of items as given below . By default  [ IGNORECASE ] is used.

- ASCII, A,

- IGNORECASE, I,

- MULTILINE, M,

- DOTALL, S,

- VERBOSE, X,

- LOCALE, L

Redactomatic expects to be given a list of regular expression for the redactor.   If a list of regular expressions is specified then the redactor will attempt to match the given text against each of the patterns in turn.  The matching is done in the order that the list is defined and any matching text is redacted once it is found.  Matching text does not stop any subsequent patterns from also being matched on the text.  For example if a pair of patterns is specified then a given text may match one of the patters in one part of the text and the other pattern in another part of the same text.  The two matching sections cannot overlap.

### redact.RedactorPhraseList

```
...
  EMPLOYEENAMES:
    redactor:
      model-class: redact.RedactorPhraseList
      text:
        #phrase-list: [fred, joe, stacy, kylie]
        phrase-filename: $REDACT_HOME/data/employeenames.csv
        phrase-field: name
        phrase-column: 1
        phrase-header: True
        flags: [ ASCII, IGNORECASE, ... ]

      voice:
        ...
```

**Example RedactorPhraseList definition.** (alternative phrase-list shown as comment)

The `redact.RedactorPhraseList` class is very similar to redact.RedactorRegex but instead of matching regular expressions it matches lists of phrases.

The phrase list can be specified directly inline:

- phrase-list - a list of phrases to select from randomly.

Alterntively if no phrase list is specified then the class will attempt to read the phrase list from a CSV file using the following parameters:

- phrase-filename - The name of a CSV file containing the phrases
- phrase-header - True/False The CSV file has a header row (default=True)
- phrase-field - The name of the column to select (phrase-header=True only)
- phrase-column - Alternative to phrase-field. An integer column number (Default=0)

The `phrase-filename` can be an absolute path, or a relative path.  If it is a relative path then redactomatic will look for it relative to the current working directory.  If the path is prefixed with `$REDACT_HOME` then the path will be interpreted relative to the path in the enviornment variable `REDACT_HOME`.  If that environment variable is not set then it will search relative to installation directory of redactomatic.py.

This class uses regular expressions to implement that phrase match. It optionally allows the definition of  regular expressions to be added to the front and back of each phrase using the ```prematch``` and ```postmatch``` options.  By default, ```prematch.regex='\b'``` and ```postmatch.regex='\b'``` to ensure that whole words are matched.  This can be suppressed using ```add-wordbreak: False``` option or by overriding one or both of them using your own ```prematch``` or ```postmatch``` regular expression.

The following parameters affect the regular expression matching.

- flags - behaves as described for `redact.RedactorRegex`.  
- combine-sets - If True, combine all phrases into a single regex for efficiency (Default=True)
- add-wordbreak - If True, sets the prematch.regex and postmatch.regex t- be '\b'. (Default=True)
- prematch - A section defining the pattern to match *before* the phrase (optional). One of:
  - regex - an inline regular expression or list ore regular expressions
  - regex-filename - a filename contaning the regular expression (not supported yet) 
  - regex-id - an ID to a regex definition in the regex section
- postmatch - A section defining the pattern to match *after* the phrase (optional). One of:
  - regex - an inline regular expression or list ore regular expressions
  - regex-filename - a filename contaning the regular expression (not supported yet)
  - regex-id - an ID to a regex definition in the regex section 

This class is used by in the definition of the `_IGNORE_` entity redactor that can be found in the release file [data/ignore.yml](data/ignore.yml).   Note that the special anonymizer class `anonymize.AnonRestoreEntityText` is used to restore this text again after redaction is completed.

```
entities:
  _IGNORE_:
    redactor:
      model-class: redact.RedactorPhraseList
      text:
        phrase-list:
          - first name
          - first and
          - today
          - yesterday
          - CV
          - tomorrow
      voice:
        phrase-list:
          - first name
          - first and
          - today
          - yesterday
          - CV
          - tomorrow
    anonymizer:
      model-class: anonymize.AnonRestoreEntityText
```
### redact.RedactorPhraseDict

```
entity:  
  Common_Cardinal_Phrases:
    redactor:
      model-class: redact.RedactorPhraseDict
      text:
        phrase-filename: keywords.json
        phrase-field: keywords
        prematch:
          regex: '[1-9]+[ ]'
        flags: [ ASCII, IGNORECASE, ... ]

      voice:
        ...
```

**Example RedactorPhraseDict definition.** (alternative phrase-list shown as comment)

The `redact.RedactorPhraseDict` class is very similar to `redact.RedactorPhraseList` but it reads its phrase list data from a JSON or YML file rather than a CSV.

The following parameters are used to define where the phrase list can be found.

- phrase-filename - The name of a JSON or YML file containing the phrases
- phrase-path - A JSON style path to the elements where the phrases are defined (e.g. toplist.words)

The `phrase-filename` can be an absolute path, or a relative path.  If it is a relative path then redactomatic will look for it relative to the current working directory.  If the path is prefixed with `$REDACT_HOME` then the path will be interpreted relative to the path in the enviornment variable `REDACT_HOME`.  If that environment variable is not set then it will search relative to installation directory of redactomatic.py.

The `phrase-path` defines the path into the JSON or YML file to find the phrase list.  It is intended that this will eventually follow JPATH but currenlty class only supports one sub-level.

This redactor using regular expressions to match the phrases in an identical manner to `redact.RedactorPhraseList`.  It supports the same parameters to affect the regular expression matching.

- flags - behaves as described for `redact.RedactorRegex`.  
- combine-sets - If True, combine all phrases into a single regex for efficiency (Default=True)
- add-wordbreak - If True, sets the prematch.regex and postmatch.regex t- be '\b'. (Default=True)
- prematch - A section defining the pattern to match *before* the phrase (optional). One of:
  - regex - an inline regular expression or list ore regular expressions
  - regex-filename - a filename contaning the regular expression (not supported yet) 
  - regex-id - an ID to a regex definition in the regex section
- postmatch - A section defining the pattern to match *after* the phrase (optional). One of:
  - regex - an inline regular expression or list ore regular expressions
  - regex-filename - a filename contaning the regular expression (not supported yet)
  - regex-id - an ID to a regex definition in the regex section 

The `prematch` section allows you to define a regular expression that must be true prior to the phrase.     Considering the definition of the `Common_Cardinal_Phrases` entity shown above.  The keywords are drawn from the 'keywords' section of 'keywords.json' file and then the regular expression `/[1-9]+[ ]/` is prepended to these keywords.  This means it will only match these keywords if they are preceded by one or more digits followed by a space and then followed by the keyword.  for example '1 week' will match but 'a bad year' will not.

```
{
    "keywords": [
      "adjustment",		
      "activated",
      ...
      "weeks",
      "year",
      "years"
    ]
}
```

**An example JSON file with keywords in a single dictionary item. (e.g. keywords.json)**

In the above example file `phrase-path="keywords"` will take the keywords from the array in the 'keywords' dictionary item.

```
{
	"terms": [
		{
			"label": ":) t359",
			"speech": [
				"smiley t three five nine",
				"smiley t three hundred fifty nine",
				"smiley t three fifty nine"
			],
      "text": [
				"t359"
			]
    },
		{
			"label": "A30",
			"speech": [
				"A thirty"
			],
 			"text": [
				"a30"
			]
		},

        ....
	]
}
```

**An example JSON file with keywords in sub-strcutures.**

In the above example file `phrase-path="terms.speech"` will take the keywords from all of the arrays in each of the terms.speech dictionary items.


### redact.RedactorSpacy

```
entities:
  _SPACY_:
    redactor:
      model-class: redact.RedactorSpacy
```

The `redact.RedactorSpacy` class implements the redaction of text using the Spacy NL ML models.  It takes no parameters but its configuration is affected by the command line  `--large` option.

## Built-In Anonymizer Classes

Redactomatic currently has several built-in anonymizer classes.  There are four generic anonymizers and a number of custom anonymizers for specific entities.

### Turning off persistence

The *persist* rule is universal to all anonymizer classes.  This rule will also be inherited by any custom anonymizers that you add.

```
...
    anonymizer:
        model-class:  ..all-model-classes..
        persist: False
```

By default the *persist*  rule have the value *True* and does not need to be defined.  With this default value then replacements of entites with the same index number will be anonymized with the same value.  For example if the redaction label [Name-99] will always be anonymized with the first randome value assigned to it any given conversation regardless of how many times it occurs.

If the persist value is set to False then this entity will always be given a new random value even if the same index is repeated through the conversation.  This can be helpful where redacting things that are too generic to reliably be the same entity.  For example imagine a redaction rule that redacts all isolated digits. It may not be desirable to anonymize all redacted digits with the same anonymized digit.

### anonomizer.AnonRegex

```
...
    anonymizer:
      model-class: anonymize.AnonRegex
      text:
        regex: ['[a-z]{0-16}\.com']
        regex-id: my-rule-id
        limit: 10
        flags: [ IGNORECASE ]
      voice:
        ...
```

The `anonomizer.AnonRegex` class is used to generate random text strings using a regular expression as a generative grammar.  The regular expressions can be expressed inline via the `regex` parameter or by reference rules in the `regex `section using the `regex-id` parameter.   Both are shown in the xample above but only define one of these in each anonymizer. The `limit `parameter defines the maximum number of repeats that a  repeating pattern will be permitted to follow before terminating.  This prevents infinite loops and can be used to limit computationally costly patterns.   This is set to 10 by default.  For more details see [xeger PyPI](https://pypi.org/project/xeger/).  The `flags `parameter behaves as described for `redact.RedactorRegex`.   This class does not support PCRE.

```
entities:
  ORDINAL:
    anonymizer:
      model-class: anonymize.AnonRegex
      text:
        regex:
          - '1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th'
      voice:
        regex:
          - 'first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth'
```

An example implementation using inline regular expressions is shown above for the ORDINAL entity.

### anonymize.AnonRestoreEntityText

```
...
entities:
  _IGNORE_:
    anonymizer:
      model-class: anonymize.AnonRestoreEntityText
```

The `anonomizer.AnonRestoreEntityText` class is used to restore any text that was redacted by a redactor rule for the same named entity.  This class will restore the text for an entity regardless of which class was used to anonymize it. It takes no parameters.

In the default configuration file [data/ignore.yml](data/ignore.yml) , the \_IGNORE\_ entity tag is redacted using the `redactor.RedactPhraseList` class and then restored at the end using the `anonymize.AnonRestoreEntityText` class.   This is one example of how the ignore/restore pattern can be used but you can use this class to restore text redacted by other classes and have as many restorable entities as you want.

As this class restores the original text take care not to accidentially restore PII that needs to remain redacted.

### anonymize.AnonNullString

```
entities:
  LAUGHTER:
    anonymizer:
      model-class: anonymize.AnonNullString
```

The `anonomizer.AnonNullString` class is used to remove redaction labels and replace them with a null string.  In the example shown above the LAUGHTER entity (received from a speech recognizer for example) is removed and no text is put in its place.

### anonymize.AnonPhraseList

```
entities:
  PERSON:
    anonymizer:
      model-class: anonymize.AnonPhraseList
      text:
        #phrase-list: [fred, joe, stacy, kylie]
        phrase-filename: $REDACT_HOME/data/baby-names.csv
        phrase-field: name
        phrase-column: 1
        phrase-header: True
      voice:
        ...
```

**Example AnonPhraseList definition.** (alternative phrase-list shown as comment)

The `anonomizer.AnonPhraseList` class enables anonymization of fields based on the random selection of a phrase from a phrase list.

This class has very similar parameters to `redactor.RedactPhraseList` class.

The phrase list can be specified directly inline:

- phrase-list - a list of phrases to select from randomly.

Alterntively if no phrase list is specified then the class will attempt to read the phrase list from a CSV file using the following parameters:

- phrase-filename - The name of a CSV file containing the phrases
- phrase-header - True/False The CSV file has a header row (default=True)
- phrase-field - The name of the column to select (phrase-header=True only)
- phrase-column - Alternative to phrase-field. An integer column number (Default=0)

The `phrase-filename` can be an absolute path, or a relative path.  If it is a relative path then redactomatic will look for it relative to the current working directory.  If the path is prefixed with `$REDACT_HOME` then the path will be interpreted relative to the path in the enviornment variable `REDACT_HOME`.  If that environment variable is not set then it will search relative to installation directory of redactomatic.py.

### Other Built-In Anonymizers

A number of entities are anonymized using custom classes written specifically for that entity.

The following classes generate number entities (text or voice) using random number generation within a pattern.

- `anonymize.AnonSSN`
- `anonymize.AnonPhone`

The following are specializations of `anonymize.AnonPhraseList`.  They accept the same parameters but then add specific formatting to phrase once a random item has been selected.

- `anonymize.AnonAddress`
- `anonymize.AnonZipC`
- `anonymize.AnonEmail`

## License

Please see the [LICENSE](LICENSE) 

## Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the MIT license, shall
be licensed as above, without any additional terms or conditions.

Please see the [Contribution Guidelines](CONTRIBUTING.md).

## Known Issues

There are no known issues.

## Authors

Jonathan Eisenzopf, David Attwater

## Copyright

Copyright 2021, Jonathan Eisenzopf, All rights reserved.

## Contributors

Thanks to [@kavdev](https://github.com/kavdev) for reviewing the code and submitting bug fixes.
Thanks to [@wmjg-alt](https://github.com/wmjg-alt) for adding context to anonymization functions.
Thanks to [@davidattwater](https://github.com/davidattwater) for refactoring the code to use a generic rules base.

## Version History

| Version  | Description                                                                                    | Date |
| -------- | ---------------------------------------------------------------------------------------------- | ---------- |
| 1.0       | Redactomatic redacts and anonymizes personally identifiable information (PII) in transcribed calls and chat logs with context. It uses a multi-pass approach utilizing both machine learning named entity recognition and regular expressions. |Aug 9 2021 |
| 1.1      |Added redaction levels 1-3, 1 being the least strict and 3 being the most strict. The default is 2. |Aug 13 2021|
| 1.2      | Adds the ability to add abbreviations to entity token names. This makes it possible to do some tokenization of entities prior to using redactomatic. For example, if you pre-processed zip codes and tagged them as [zipcode], you could map this tag to [ZIP] in config.json, run redactomatic with the --anonymization flag turned on, and it would replace all instances of [ZIP] and [zipcode] with randomized zip codes. | |
| 1.3      | Minor release that prints the Redactomatic version. |Sept 28 2021|
| 1.4      |Fixed anonymization so that a previously redacted file can be anonymized with the --noredaction switch. | Sept 29 2021|
| 1.5      |- Added support for new entity type PIN. Added voice support for zip and phone. </br>- Also added the ability to map existing tags to entity types, which can be configured in config.json. |Oct 1 2021 |
| 1.6      | Addressed anonymization bug. Updated sample CSV files for additional test cases.|Oct 2 2021 |
| 1.7      | Refactored anonymization functions to fix a number of bugs. | Jan 27 2022|
| 1.8      |Added the ability to define regular expressions and redaction and anonymization rules using YML or JSON rules files.| Feb 9 2022|
| 1.9      |-All hard-coded paths have been removed from the core anonymizers by adding Anonymize.AnonPhraseList class.</br>-  Configuration is now entirely done via rules files.</br>-  Some custom anonymization classes remain for core entities such as ADDRESS and ZIP code but these are now simple specializations of of the PhraseList class. </br>- As part of this release we have also further refactored the Anonymization so that only the callback() functions need to be defined to create your own anonymizer class. |Feb 9 2022 |
| 1.10      |Anonymize.AnonPhraseList has been extended to allow multiple phrase lists to be randomly concatenated. This allows the construction of things like email addresses. | Feb 9 2022|
| 1.11      |- Bug fix for multi-rule regular expressions. Previous version only ran one of the defined regular expressions.</br>- Added ?DEFINE macro support in regular expressions with a couple of core rules changed to showcase the feature.</br>- Added regextest example file and test which can be built upon in later releases.</br>- Added voice support for credit card number.</br>- Refactored config.json into config.yml to make all configuration files yml rather than json. |Feb 21 2022 |
| 1.12      | Added voice support for US SSN and credit cards.|Mar 5 2022 |
| 1.13      |-Added batching to prevent the need to load the whole file in before processing it.</br>- Added optional support for named headers with defaults. Files with headers are now correctly concatenated into an output file with a single header line and there is no need to specify the column numbers if your file has headers.</br>- Relative file paths to redaction and anonymization file resources are now resolved relative to the program directory not the current working directory. This means that you do not have to run redactomatic in its home directory any more. Also added support for $REDATC_HOME environment variable to overload this if neccessary.</br>- Tidied up and checked all the test files so that they return True. |Mar 31 2022 |
| 1.14      |This release should be backwards compatible with v1.13 apart from the renaming of the -noredaction flag.</br>- Added --chunklimit to allow benchmarking of different chunk sizes without having to run the whole file.</br>- Tided up the command-line switches for --anonymize and --redact.</br>- Deprecated --noredaction and made it --no-redact instead in line with above.</br>- Removed self-mappings from anon_map and changed the self-mapping to be define in entity_rules.py properties instead of anonymize.py</br>- Added the always-anonymize section to remove all special meaning from the IGNORE entity. You can now have multiple ignore sets if you want to. If this section is missing however it adds 'IGNORE' as a default to keep backwards compatibility. | Apr 12 2022 |
| 1.15      | Added the ability to add Perist: False to anonymizers to support random anonymization of things like isolated digits without persisting specific values across the whole dialog.| May 6 2022|
| 1.16      | Updated the Spacy models to 3.3.0| Jun 1 2022|
| 1.17      |  Brought in line with the Talkmap internal version of corpustools as of 20/10/2022.</br>- added --default rules to allow separation of custom rules and default rule set</br>- Made redactomatic a processor like any other.</br>- Moved the clean() routines from redactomatic to processorbase so they can be shared.</br>- Moved reading of config files from redactomatic to entity_rules so they can be used by other programs.</br>- Tidied up the imports in redactomatic to stop it importing things it did not need.</br>- Added substitution and recursive substitution rules to regex_utils</br>- Added fixes to cardinal digit anonymization to stop digits being concatenated without spaces</br>- Updated ignore.yml to use regular expressions rather than phrase lists and added protection for common cardinal phrases and contexts.</br>- Created a test-script area and moved redactomatic tests into there.</br>- Moved documentation for redactomatic into docs and put in a more general top level README.</br>- Added a more comprehensive fix for the bug where cardinal rules redacted other redaction labels. |Oct 20 2022 |
| 1.18      | Add and abort message when trying to restore ignored text with --no-redact set.</br>- Bugfix for wrong left/right ordering </br>- Add RedactorPhraseDict class to support JSON and YML phrase lists.</br>- Add RedactorPhraseDict documentation</br>- Upgrade the protection for stopping regular expressions overwriting other redaction labels.</br>- Fixed a bug where multi-line regex definition could result in corrupted text.</br>- Add --traceback option for debugging</br>- And warning for missing entity definitions</br>- Clean up the default config.yml</br>- Separate cardinal text and voice rules</br>- Remove 'oh' from cardinal rules</br>- Add sample custom 'redactanon' YML file</br>- Move aboslute_path to processor base.</br>- Add explicit support for $REDACT_HOME and local paths in the current working directory</br>- Add --version option. |  Nov 2022  |
| 1.19      | - Added default option to compile a single regex for a whole phrase list to make it more efficient to RedactorPhraseDict and RedactorPhraseList</br>- Added combine-sets parameter to support turning this off if required</br>- Added complete prematch and postmatch support for RedactorPhraseDict and RedactorPhraseList</br>- Added add-wordbreak parameter to RedactorPhraseDict and RedactorPhraseList</br>- Documented all of the above changes in README  | Nov 2022  |
| 1.20 | - Added --verbose and --no-verbose command line options</br>- Changed entity restoration error from an exeption to at stops execution to a warning that restoration failed.  |16 Dec 2022 |
