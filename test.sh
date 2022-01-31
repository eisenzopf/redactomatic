python3 redactomatic.py --column 4 --idcolumn 1 --modality voice --inputfile ./data/sample_data_voice.csv --outputfile voice_output_l2.csv --log voice_log_l2.csv --level 2 
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile text_output_l2.csv --log text_log_l2.csv --level 2
python3 redactomatic.py --column 4 --idcolumn 1 --modality voice --inputfile ./data/sample_data_voice.csv --outputfile voice_output_anonymized_l2.csv --anonymize --seed 1 --level 2
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile text_output_anonymized_l2.csv --anonymize --seed 1 --level 2

python3 redactomatic.py --column 4 --idcolumn 1 --modality voice --inputfile ./data/sample_data_voice.csv --outputfile voice_output_l3.csv --log voice_log_l3.csv --level 3
python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile text_output_l3.csv --log text_log_l3.csv --level 3

python3 redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/anonymized_sample_data.csv --outputfile text_output_anonymized_only.csv --anonymize --noredaction --level 3 --seed 1
python3 redactomatic.py --column 4 --idcolumn 1 --modality voice --inputfile ./data/anonymized_sample_data.csv --outputfile voice_output_anonymized_only.csv --anonymize --noredaction --level 3 --seed 2

python3 test.py -v

rm text_log_l2.csv
rm voice_log_l2.csv
rm voice_output_l2.csv
rm text_output_l2.csv
rm voice_output_anonymized_l2.csv
rm text_output_anonymized_l2.csv
rm text_log_l3.csv
rm voice_log_l3.csv
rm voice_output_l3.csv
rm text_output_l3.csv
rm text_output_anonymized_only.csv
rm voice_output_anonymized_only.csv
