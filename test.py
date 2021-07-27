import filecmp
text_log = "text_log.csv"
text_redacted = "text_output.csv"
text_anonymized = "text_output_anonymized.csv"
voice_log = "voice_log.csv"
voice_redacted = "voice_output.csv"
voice_anonymized = "voice_output_anonymized.csv"
  
# shallow comparison
print ("Is the text redaction log correct?:", filecmp.cmp(text_log, "test/" + text_log))
print( "Is the redacted text output file correct?:", filecmp.cmp(text_redacted, "test/" + text_redacted))
print ("Is the voice redaction log correct?:", filecmp.cmp(voice_log, "test/" + voice_log))
print( "Is the redacted voice output file correct?:", filecmp.cmp(voice_redacted, "test/" + voice_redacted))
