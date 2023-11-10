# syllabification-by-analogy

## PbA Success! (11/9/2023)
The first "leave-one-out" test for this repository's __pronunciation by analogy__ implementation is complete. Results seem to indicate improvement across the board over M&D's implementation, probably due to a greater number of words in the lexical database (65,915 versus 19,594).

![image](https://github.com/somamos/syllabification-by-analogy/assets/141623014/2695ae3f-da1f-4fe8-8ad2-e47d128f5cb2)

The repository currently consists of 

1. Preprocessing to merge common words between a pronunciation wordlist and a syllabified wordlist,
2. Marchand & Damper's text-phoneme alignment algorithm,
3. Dedina & Nusbaum's pronunciation by analogy method (with tweaks by M&D), and
4. a preliminary implementation of Marchand & Damper's syllabification by analogy (SbA).

Read more about their algorithm [here](https://github.com/somamos/syllabification-by-analogy/files/13186641/Damper.Marchand.s.Can.syllabification.improve.pronunciation.by.analogy.of.English.pdf).

## todo:
1. preprocess.py
    - [ ] Allow for outputs that do not mix datasets A and B.
    - [ ] Allow for outputs from different sources.
    - [ ] Test the premise that inferring nucleus locations pre-alignment improves results. Is it smart to anchor nuclei so naively based on such simple rules? Or should we instead let alignment do its thing and determine the nucleus per syllable post-alignment (ditching mappings of multiple aligned nuclei per dataset-b-encoded syllable?)
2. align.py
    - [X] Prioritize encodings' nucleus locations during alignment (list of index tuples?).
    - [X] Rewrite description of "suppression above the diagonal."
    - [ ] Improve alignment of pba's worst performers (see "Track the worst-performing..." below)
3. pba.py
    - [X] Implement the 5 scoring systems described by Marchand & Damper.
    - [X] Fix the scoring systems to match those described by [this version(!)](https://github.com/somamos/syllabification-by-analogy/files/13280320/089120100561674.pdf) of the paper.
    - [X] Fix "silence problem" (flag bigrams unrepresented in the dataset).
    - [X] Call off search at a certain number of candidate paths reached during bfs.
    - [X] Refactor to prepare for syllabification (generalize Lattice).
    - [ ] Write a convenient way to compare two datasets' results.
    - [ ] Track the worst-performing input letters, output phonemes, and most challenging ground truth phonemes. 
4. sba.py
    - [X] Add sba (split encodings by syllable).
    - [ ] Evaluate sba results.

# Overview
 
## preprocess.py

Given dataset a (containing phoneme information and stress pattern information) and dataset b (containing syllable division information), `preprocess.py` merges them into the following form (described on page 10 of the paper):

![image](https://github.com/somamos/syllabification-by-analogy/assets/141623014/20972aa6-35d1-42e3-a0da-2a387fb5df2f)

See Appendix A of Sejnowski and Rosenberg's _Parallel Networks that Learn to Pronounce English Text_ for more details. (Contact somamosinteractive@protonmail.com for access to the datasets `a` and `b`.) 

## align.py

Data-driven "by analogy" techniques require an aligned dataset. In this case, every word's letter must map to one and only one phoneme. We implement Marchand & Damper's _Aligning Text and Phonemes for Speech Technology Applications Using an EM-Like Algorithm_ with a few tweaks and improvements. 

## pba.py

Given an input word, pronunciation by analogy searches for matching substrings in a so-called "lexical database" (a list of words mapped to their phonemes), patching the substrings together into a "lattice" to form a list of candidate pronunciations. The candidate pronunciations are then scored.

