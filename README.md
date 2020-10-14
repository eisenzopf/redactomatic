# RedactoMatic

RedactoMatic removes personally identifiable information (PII) from conversation data. It works with transcribed calls AND chat logs. Please report bugs and feel free to make features requests.

## Installation

To install RedactoMatic, run:

```sh
sh setup.sh
```

This will install required Python libraries and download the small and large Spacy models.

## Usage

The current iteration of the code expects you to provide a CSV file from the commandline.

```sh
usage: redactomatic.py [-h] --column COLUMN --inputfile INPUTFILE [INPUTFILE ...] --outputfile OUTPUTFILE
```

You can specify one or more input files but only one output file. You must also specify which column in the input CSV(s) to redact. For example, if the CSV input file(s) contain text in the 2nd column that you would like to redact, you would set the  --column flag to 2.

```sh
Ex.: python redactomatic.py --column 2 --inputfile input.csv --outputfile output.csv
```

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

Copyright 2020, [Discourse.ai](https://www.discourse.ai), All rights reserved.
