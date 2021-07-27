pip install -r requirements.txt
python -m spacy download en_core_web_lg
python -m spacy download en_core_web_sm
python redactomatic.py --column 4 --idcolumn 1 --modality voice --inputfile ./data/sample_data_voice.csv --outputfile voice_output.csv --log voice_log.csv
python redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile text_output.csv --log text_log.csv
python redactomatic.py --column 4 --idcolumn 1 --modality voice --inputfile ./data/sample_data_voice.csv --outputfile voice_output_anonymized.csv --anonymize
python redactomatic.py --column 4 --idcolumn 1 --modality text --inputfile ./data/sample_data.csv --outputfile text_output_anonymized.csv --anonymize
python test.py -v
rm text_log.csv
rm voice_log.csv
rm voice_output.csv
rm text_output.csv
rm voice_output_anonymized.csv
rm text_output_anonymized.csv
