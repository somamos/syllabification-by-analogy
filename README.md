# syllabification-by-analogy

## PbA. Now 300x faster. (11/17/2023)

Lattice construction gets a **HUGE performance boost**! Thanks to precalculating two ~16 MB dicts that store:

1. every letter substring mapped to an inner dict of alternate domain representations, themselves mapped to the number of times those letter substrings align with those alternate domain representations in the database, i.e. `{sauce: {'sc--s': 6, 's-Wse': 2, 'sc-sx': 1}}`, and
2. its effective inverse, alternate domain representations' substrings mapped to the set of letter substrings that serve as keys to that representation in (1) i.e. `{'sc--s': {'sauci', 'sauce'}`.

## SbA and PbA Success! (11/11/2023)
The "leave-one-out" cross validation tests for __pronunciation by analogy__ AND __syllabification by analogy__ are complete. Compared to the results of M&D's original publication, this repository demonstrates considerable pronunciation improvement (below, left) and modest syllabification improvement (below, right), probably due to a greater number of words in the lexical database (58,989 versus 19,594).

![results_](https://github.com/somamos/syllabification-by-analogy/assets/141623014/f39516db-cd8d-4e1a-a0e5-8e99fd0dc45a)

## Quick Start

As of 11/17/2023, all preprocessed datasets are tracked with the repository -- no preprocessing needed! Just run `python pba.py` from the repository location after cloning. The top-level code has a few methods to get you started.

The repository currently consists of 

1. `preprocessing.py`: to merge common words between a pronunciation wordlist `a.txt` and a syllabified wordlist `b.txt` (as well as to prep a third dataset `c.txt` that has both in one),
2. `align.py`, an implementation of Marchand & Damper's text-phoneme alignment algorithm,
3. `pba.py`, an implementation of Dedina & Nusbaum's pronunciation by analogy method (with tweaks by M&D) **now with 150-300x performance boost!** via `patternmatching.py`, and
4. `sba.py`, A not-yet-optimized implementation of Marchand & Damper's syllabification by analogy (SbA).

Read more about their algorithm [here](https://github.com/somamos/syllabification-by-analogy/files/13186641/Damper.Marchand.s.Can.syllabification.improve.pronunciation.by.analogy.of.English.pdf).

## todo:
1. preprocess.py
    - [ ] Build version of dataset c that only contains words from dataset a∩b.
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
    - [X] Bug fix: right-aligned substrings of substrings still count as duplicate matches. (tori -> ori -> ri).
    - [ ] Multiprocessing at word level for cross validation.
    - [X] Multiprocessing at "pattern matching" level.
    - [X] Rewrite a "complete matching" method that benefits from multiprocessing (populate_precalculated doesn't).
    - [ ] Multiprocessing at BFS for long words (20+ characters).
    - [ ] Write a convenient way to compare two datasets' results.
    - [ ] Track the worst-performing input letters, output phonemes, and most challenging ground truth phonemes. 
4. sba.py
    - [X] Add sba (split encodings by syllable).
    - [X] Evaluate sba results.
5. patternmatcher.py
    - [x] Test new and improved pattern matcher.
    - [X] Port previous methods to oldpatternmatcher.py

# Overview
 
## preprocess.py

Given dataset a (containing phoneme information and stress pattern information) and dataset b (containing syllable division information), `preprocess.py` merges them into the following form (described on page 10 of the paper):

![image](https://github.com/somamos/syllabification-by-analogy/assets/141623014/20972aa6-35d1-42e3-a0da-2a387fb5df2f)

See Appendix A of Sejnowski and Rosenberg's _Parallel Networks that Learn to Pronounce English Text_ for more details. (Contact somamosinteractive@protonmail.com for access to the datasets `a` and `b`.) 

## align.py

Data-driven "by analogy" techniques require an aligned dataset. In this case, every word's letter must map to one and only one phoneme. We implement Marchand & Damper's _Aligning Text and Phonemes for Speech Technology Applications Using an EM-Like Algorithm_ with a few tweaks and improvements. 

## pba.py

Given an input word, pronunciation by analogy searches for matching substrings in a so-called "lexical database" (a list of words mapped to their phonemes), patching the substrings together into a "lattice" to form a list of candidate pronunciations. The candidate pronunciations are then scored.

