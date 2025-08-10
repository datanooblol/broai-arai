# Note

- first_evaluations: terms=5
- second_evaluations: terms=10
- third_evaluations: terms=10, is_terms=['both'] | both False False with marverick won while both True True degrading
- forth_evaluations: terms=10 with filtering mechanism # fail
- fifth_evaluations: terms=10 with filtering mechanism # success, term_extractor=marverick
- sixth_evaluations: terms=10 with filtering mechanism # success, term_extractor=llama3.2:70B
- seventh_evaluations: terms=10 with filtering mechaism, term_extractor=marverick