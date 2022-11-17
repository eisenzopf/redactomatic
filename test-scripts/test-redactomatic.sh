BINDIR='..'
INPUTDIR='../sample-data'
TESTEXPECTED='../test-expected'
CUSTOMRULES=$INPUTDIR'/custom-anon-rules.yml'

#Inputfile names
sample_voice='sample_data_voice.csv'
sample_text='sample_data.csv'

#Output file names
regex_test='regextest.csv'
voice_redacted_l2='voice_output_l2.csv'
voice_log_l2='voice_log_l2.csv'
text_redacted_l2='text_output_l2.csv'
text_log_l2='text_log_l2.csv'
voice_redact_anonymized_l2='voice_output_anonymized_l2.csv'
text_redact_anonymized_l2='text_output_anonymized_l2.csv'
voice_redacted_l3='voice_output_l3.csv'
voice_log_l3='voice_log_l3.csv'
text_redacted_l3='text_output_l3.csv'
text_log_l3='text_log_l3.csv'
text_anonymized_only='text_output_anonymized_only.csv'
voice_anonymized_only='voice_output_anonymized_only.csv'

#This should throw an error due to no rules being loaded
python3 $BINDIR/redactomatic.py --no-defaultrules --regextest --no-redact --testoutputfile $regex_test
echo "NOTE TO TESTER: Check that redactomatic terminated with the error message 'No rulefiles loaded'. "

#Test the automatic regular expression testing.
python3 $BINDIR/redactomatic.py --regextest --no-redact --testoutputfile $regex_test

#Test redaction and then anonymization at level 2
python3 $BINDIR/redactomatic.py --column 4 --idcolumn 1 --modality voice --rulefile $CUSTOMRULES --chunksize 20 --inputfile $INPUTDIR/$sample_voice --outputfile $voice_redacted_l2 --log $voice_log_l2 --level 2 
python3 $BINDIR/redactomatic.py --column 4 --idcolumn 1 --modality text  --rulefile $CUSTOMRULES --inputfile $INPUTDIR/$sample_text --outputfile $text_redacted_l2 --log $text_log_l2 --level 2
python3 $BINDIR/redactomatic.py --column 4 --idcolumn 1 --modality voice --rulefile $CUSTOMRULES --inputfile $INPUTDIR/$sample_voice --outputfile $voice_redact_anonymized_l2 --anonymize --seed 1 --level 2
python3 $BINDIR/redactomatic.py --column 4 --idcolumn 1 --modality text  --rulefile $CUSTOMRULES --inputfile $INPUTDIR/$sample_text --outputfile $text_redact_anonymized_l2 --anonymize --seed 1 --level 2

#Test redaction at level 3
python3 $BINDIR/redactomatic.py --column 4 --idcolumn 1 --modality voice --rulefile $CUSTOMRULES --inputfile $INPUTDIR/$sample_voice --outputfile $voice_redacted_l3 --log $voice_log_l3 --level 3
python3 $BINDIR/redactomatic.py --column 4 --idcolumn 1 --modality text  --rulefile $CUSTOMRULES --inputfile $INPUTDIR/$sample_text --outputfile $text_redacted_l3 --log $text_log_l3 --level 3

#Test anonymization for each of the anonymizer tokens
python3 $BINDIR/redactomatic.py --column 4 --idcolumn 1 --modality text --rulefile $CUSTOMRULES --inputfile $INPUTDIR/anonymized_sample_data.csv --outputfile $text_anonymized_only --anonymize --no-redact --level 3 --seed 2
python3 $BINDIR/redactomatic.py --column 4 --idcolumn 1 --modality voice --rulefile $CUSTOMRULES --inputfile $INPUTDIR/anonymized_sample_data.csv --outputfile $voice_anonymized_only --anonymize --no-redact --level 3 --seed 2

# Now compare the results.
python3 compare-files.py $regex_test $TESTEXPECTED/$regex_test 'Is the regex test output file correct?'
python3 compare-files.py $text_log_l2 $TESTEXPECTED/$text_log_l2 'Is the L2 text redaction log correct?'
python3 compare-files.py $text_redacted_l2 $TESTEXPECTED/$text_redacted_l2 'Is the L2 redacted text output file correct?'
python3 compare-files.py $text_redact_anonymized_l2 $TESTEXPECTED/$text_redact_anonymized_l2 'Is the L2 redacted and anonymized text output file correct?'
python3 compare-files.py $voice_log_l2 $TESTEXPECTED/$voice_log_l2 'Is the L2 voice redaction log correct?'
python3 compare-files.py $voice_redacted_l2 $TESTEXPECTED/$voice_redacted_l2 'Is the L2 redacted voice output file correct'
python3 compare-files.py $voice_redact_anonymized_l2 $TESTEXPECTED/$voice_redact_anonymized_l2 'Is the L2 redacted and anonymized voice output file correct?'
python3 compare-files.py $text_log_l3 $TESTEXPECTED/$text_log_l3 'Is the L3 text redaction log correct?'
python3 compare-files.py $text_redacted_l3 $TESTEXPECTED/$text_redacted_l3 'Is the L3 redacted text output file correct'
python3 compare-files.py $voice_log_l3 $TESTEXPECTED/$voice_log_l3 'Is the L3 voice redaction log correct?'
python3 compare-files.py $voice_redacted_l3 $TESTEXPECTED/$voice_redacted_l3 'Is the L3 redacted voice output file correct'
python3 compare-files.py $text_anonymized_only $TESTEXPECTED/$text_anonymized_only 'Is the pure text anonymization file correct?'
python3 compare-files.py $voice_anonymized_only $TESTEXPECTED/$voice_anonymized_only 'Is the pure voice anonymization file correct?'

#Now delete the test output files.
rm -f $regex_test
rm -f $voice_redacted_l2 
rm -f $voice_log_l2 
rm -f $text_redacted_l2    
rm -f $text_log_l2 
rm -f $voice_redact_anonymized_l2 
rm -f $text_redact_anonymized_l2 
rm -f $voice_redacted_l3 
rm -f $voice_log_l3 
rm -f $text_redacted_l3 
rm -f $text_log_l3 
rm -f $text_anonymized_only 
rm -f $voice_anonymized_only 