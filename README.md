# RedactoMatic

RedactoMatic is a new project that aims to safely remove and tokenize personally identifiable information (PII) from conversation data. The project is in its early stages and the output of this project should be considered unsafe; meaning that the code is not at the stage where it will reliably remove PII data from a conversation file.

## Installation

To install RedactoMatic, run:

```sh
sh setup.sh
```

This will install required Python libraries and download the large Spacy model.

## Usage

The current iteration of the code expects you to provide a CSV file from the commandline. Redacted output will be printed to STDOUT.

```sh
python redactomatic.py input.csv > output.csv
```

## License

Please see the [LICENSE](LICENSE)

## Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall
be dual licensed as above, without any additional terms or conditions.

Please see the [Contribution Guidelines](CONTRIBUTING.md).

## Authors

Jonathan Eisenzopf

## Copyright

This application is provided by [Discourse.ai](https://www.discourse.ai) as Open Source software.
