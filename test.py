import filecmp
text_log = "text_log.csv"
text_redacted = "text_output.csv"
text_redact_anonymized = "text_output_anonymized.csv"
text_anonymized_only = "text_output_anonymized_only.csv"
voice_log = "voice_log.csv"
voice_redacted = "voice_output.csv"
voice_redact_anonymized = "voice_output_anonymized.csv"
voice_anonymized_only = "voice_output_anonymized_only.csv"

# shallow comparison
print ("Is the text redaction log correct?:", filecmp.cmp(text_log, "test/" + text_log))
print( "Is the redacted text output file correct?:", filecmp.cmp(text_redacted, "test/" + text_redacted))
print( "Is the redacted and anonymized text output file correct?:", filecmp.cmp(text_redact_anonymized, "test/" + text_redact_anonymized))
print ("Is the voice redaction log correct?:", filecmp.cmp(voice_log, "test/" + voice_log))
print( "Is the redacted voice output file correct?:", filecmp.cmp(voice_redacted, "test/" + voice_redacted))
print( "Is the redacted and anonymized voice output file correct?:", filecmp.cmp(voice_redact_anonymized, "test/" + voice_redact_anonymized))
print( "Is the anonymized text output file correct?:", filecmp.cmp(text_anonymized_only, "test/" + text_anonymized_only))
print( "Is the anonymized voice output file correct?:", filecmp.cmp(voice_anonymized_only, "test/" + voice_anonymized_only))
