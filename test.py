import filecmp
text_log_l2 = "text_log_l2.csv"
text_redacted_l2 = "text_output_l2.csv"
text_redact_anonymized_l2 = "text_output_anonymized_l2.csv"
voice_log_l2 = "voice_log_l2.csv"
voice_redacted_l2 = "voice_output_l2.csv"
voice_redact_anonymized_l2 = "voice_output_anonymized_l2.csv"

text_log_l3 = "text_log_l3.csv"
text_redacted_l3 = "text_output_l3.csv"
text_redact_anonymized_l3 = "text_output_anonymized_l3.csv"
voice_log_l3 = "voice_log_l3.csv"
voice_redacted_l3 = "voice_output_l3.csv"
voice_redact_anonymized_l3 = "voice_output_anonymized_l3.csv"

text_anonymized_only = "text_output_anonymized_only.csv"
voice_anonymized_only = "voice_output_anonymized_only.csv"

# Level 2 redaction and anonymization
print ("Is the L2 text redaction log correct?:", filecmp.cmp(text_log_l2, "test/" + text_log_l2))
print( "Is the L2 redacted text output file correct?:", filecmp.cmp(text_redacted_l2, "test/" + text_redacted_l2))
print( "Is the L2 redacted and anonymized text output file correct?:", filecmp.cmp(text_redact_anonymized_l2, "test/" + text_redact_anonymized_l2))
print ("Is the L2 voice redaction log correct?:", filecmp.cmp(voice_log_l2, "test/" + voice_log_l2))
print( "Is the L2 redacted voice output file correct?:", filecmp.cmp(voice_redacted_l2, "test/" + voice_redacted_l2))
print( "Is the L2 redacted and anonymized voice output file correct?:", filecmp.cmp(voice_redact_anonymized_l2, "test/" + voice_redact_anonymized_l2))

# Level 3 redaction and anonymization
print ("Is the L3 text redaction log correct?:", filecmp.cmp(text_log_l3, "test/" + text_log_l3))
print( "Is the L3 redacted text output file correct?:", filecmp.cmp(text_redacted_l3, "test/" + text_redacted_l3))
#print( "Is the L3 redacted and anonymized text output file correct?:", filecmp.cmp(text_redact_anonymized_l3, "test/" + text_redact_anonymized_l3))
print ("Is the L3 voice redaction log correct?:", filecmp.cmp(voice_log_l3, "test/" + voice_log_l3))
print( "Is the L3 redacted voice output file correct?:", filecmp.cmp(voice_redacted_l3, "test/" + voice_redacted_l3))
#print( "Is the L3 redacted and anonymized voice output file correct?:", filecmp.cmp(voice_redact_anonymized_l3, "test/" + voice_redact_anonymized_l3))

# Check anonumization only
#print( "Is the anonymized text output file correct?:", filecmp.cmp(text_anonymized_only, "test/" + text_anonymized_only))
#print( "Is the anonymized voice output file correct?:", filecmp.cmp(voice_anonymized_only, "test/" + voice_anonymized_only))
