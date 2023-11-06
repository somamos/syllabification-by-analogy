# syllabification-by-analogy
The repository currently consists of 

1. Preprocessing to merge common words between a pronunciation wordlist and a syllabified wordlist,
2. Marchand & Damper's text-phoneme alignment algorithm, and
3. Dedina & Nusbaum's pronunciation by analogy method (with tweaks by M&D) that here achieves ~85-90% success rate.

This work is leading up to a Python implementation of the Syllabification by Analogy (SbA) algorithm described by Marchand & Damper in _Can syllabification improve pronunciation by analogy of English?_ which you can read [here](https://github.com/somamos/syllabification-by-analogy/files/13186641/Damper.Marchand.s.Can.syllabification.improve.pronunciation.by.analogy.of.English.pdf).

## todo:
1. readme.md
    - [X] Update readme
2. preprocess.py
    - [ ] Account for remaining consonant clusters & diphthongs.
    - [ ] Gauge encodings without nuclei post-alignment.
    - [ ] Scrutinize outliers during syllable encoding.
    - [ ] Guarantee 1 nucleus per syllable.
3. align.py
    - [ ] Refactor to remove side effects.
    - [ ] Prioritize encodings' nucleus locations during alignment (list of index tuples?).
    - [ ] Rewrite description of "suppression above the diagonal."
    - [ ] Retry normalization with power transformation.
4. pba.py
    - [ ] Refactor to prepare for syllabification (generalize Lattice).
    - [ ] Implement the 5 scoring systems described by Marchand & Damper.
    - [ ] Implement "silence problem" fix (flag bigrams unrepresented in the dataset).
    - [ ] Add sba (split encodings by syllable).

# Overview
 
## preprocess.py

Given dataset a (containing phoneme information and stress pattern information) and dataset b (containing syllable division information), `preprocess.py` merges them into the following form (described on page 10 of the paper):

![image](https://github.com/somamos/syllabification-by-analogy/assets/141623014/20972aa6-35d1-42e3-a0da-2a387fb5df2f)

See Appendix A of Sejnowski and Rosenberg's _Parallel Networks that Learn to Pronounce English Text_ for more details. (Contact somamosinteractive@protonmail.com for access to the datasets `a` and `b`.) 

## align.py

Data-driven "by analogy" techniques require an aligned dataset. In this case, every word's letter must map to one and only one phoneme. We implement Marchand & Damper's _Aligning Text and Phonemes for Speech Technology Applications Using an EM-Like Algorithm_ with a few tweaks and improvements. 

## pba.py

Given an input word, pronunciation by analogy searches for matching substrings in a so-called "lexical database" (a list of words mapped to their phonemes), patching the substrings together into a "lattice" to form a list of candidate pronunciations. The candidate pronunciations are then scored. Even this early version is achieving an ~85-90% success rate (out of a mere couple hundred words of informal cross validation).
