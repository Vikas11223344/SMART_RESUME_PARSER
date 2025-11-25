from parser import parse_resume_from_text
from utils import to_json, parsed_to_dataframe

sample = '''John Doe
john.doe@example.com
+1 555-123-4567
https://linkedin.com/in/johndoe

Summary
Experienced software engineer with expertise in Python and NLP.

Skills
Python, pandas, spaCy, Docker, AWS

Education
Bachelor of Science in Computer Science, University X, 2019

Experience
Senior Software Engineer, Acme Corp (Jan 2020 - Present)
- Developed ML pipelines
- Led a team of 4 engineers
'''

parsed = parse_resume_from_text(sample)
print('\n--- PARSED JSON ---')
print(to_json(parsed))
print('\n--- DATAFRAME CSV ---')
df = parsed_to_dataframe(parsed)
print(df.to_csv(index=False))
