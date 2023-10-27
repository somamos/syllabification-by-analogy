# syllabification-by-analogy
A Python implementation of the Syllabification by Analogy (SbA) algorithm described by Marchand and Damper in _Can syllabification improve pronunciation by analogy of English?_ View their original paper [here](https://github.com/somamos/syllabification-by-analogy/files/13186641/Damper.Marchand.s.Can.syllabification.improve.pronunciation.by.analogy.of.English.pdf).

# Use
## Preprocessing
Given two datasets 1) dataset `a`, a list of words and their phonetic pronunciations; and 2) dataset `b`, a list of words separated by syllable; `preprocess.py` merges them into the form described on page 10 of the paper:

![image](https://github.com/somamos/syllabification-by-analogy/assets/141623014/20972aa6-35d1-42e3-a0da-2a387fb5df2f)

See Appendix A of Sejnowski and Rosenberg's _Parallel Networks that Learn to Pronounce English Text_ for more details. (Contact somamosinteractive@protonmail.com for access to the datasets `a` and `b`.) 