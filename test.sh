python3 redactomatic.py --column 4 --idcolumn 1 --modality voice --inputfile ./data/sample_data_voice.csv --outputfile voice_output.csv --log voice_log.csv
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile text_output.csv --log text_log.csv
python3 redactomatic.py --column 4 --idcolumn 1 --modality voice --inputfile ./data/sample_data_voice.csv --outputfile voice_output_anonymized.csv --anonymize --seed 1
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile text_output_anonymized.csv --anonymize --seed 1
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/anonymized_sample_data.csv --outputfile text_output_anonymized_only.csv --anonymize --noredaction --level 3 --seed 1
python3 redactomatic.py --column 4 --idcolumn 1 --modality voice --inputfile ./data/anonymized_sample_data.csv --outputfile voice_output_anonymized_only.csv --anonymize --noredaction --level 3 --seed 2
python3 test.py -v
rm text_log.csv
rm voice_log.csv
rm voice_output.csv
rm text_output.csv
rm voice_output_anonymized.csv
rm text_output_anonymized.csv
rm text_output_anonymized_only.csv
rm voice_output_anonymized_only.csv
