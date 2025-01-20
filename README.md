# TLDR:

This repository implements the 'by analogy' methods described [here](https://github.com/somamos/syllabification-by-analogy/files/13186641/Damper.Marchand.s.Can.syllabification.improve.pronunciation.by.analogy.of.English.pdf) and [here](https://github.com/somamos/syllabification-by-analogy/files/13280320/089120100561674.pdf).

The pre-processor implements the 'expectation-maximization-like' algorithm described [here](https://eprints.soton.ac.uk/260616/1/06-DAMPER.pdf).

Continue reading if you dare.

# syllabification-by-analogy

Syllabification by Analogy (SbA) is a way to infer syllable divisions of an unknown word. 

In summary, SbA involves:

1. comparing the unknown word's substrings against a large set of words mapped to their known syllabified counterparts,
2. stringing together matches into a lattice structure (a graph of arcs linking nodes), and
3. evaluating the "best" complete path through that structure given some heuristics.

Pronunciation by Analogy (PbA) does the same thing but maps words' spellings to the pronunciation domain. 

Although titled syllabification-by-analogy, this repository's pronunciation-by-analogy method is currently far superior. See immediately below:

## PbA. Now 300x faster. (11/17/2023)

Lattice construction gets a **HUGE performance boost**! Thanks to precalculating a ~16 MB dict. 

New `patternmatcher.py` converts a lexical database of the form `{'word': 'phonemes'}` into an optimized dict of the form `{'substring': {'phonemes_1': count_1, 'phonemes_2': count_2, ...}}` -- that is, a dict of every letter substring mapped to an _inner_ dict of all its alternate domain representations, each one mapped to the number of times that representation aligns with that substring, i.e. `{sauce: {'sc--s': 6, 's-Wse': 2, 'sc-sx': 1}}`.

## Surpassing the original paper's results! (11/11/2023)
The "leave-one-out" cross validation tests for __pronunciation by analogy__ AND __syllabification by analogy__ are complete. Compared to the results of M&D's original publication, this repository demonstrates considerable pronunciation improvement (below, left) and modest syllabification improvement (below, right), probably due to a greater number of words in the lexical database (ours has 58,989. M&D's had 19,594).

![results_](https://github.com/somamos/syllabification-by-analogy/assets/141623014/f39516db-cd8d-4e1a-a0e5-8e99fd0dc45a)

## Quick Start

Written on MacOS with Python 3.8.2 and Windows with Python 3.11.0.

As of 11/17/2023, all preprocessed datasets are tracked with the repository -- no preprocessing needed! Just run `python pba.py` from the repository location after cloning. The top-level code has a few sample functions to get you started.

The repository currently consists of 

1. `preprocessing.py`: to merge common words between a pronunciation wordlist `a.txt` and a syllabified wordlist `b.txt` (as well as to prep a third dataset `c.txt` that has both in one),
2. `align.py`, an implementation of Marchand & Damper's text-phoneme alignment algorithm,
3. `pba.py`, an implementation of Dedina & Nusbaum's pronunciation by analogy method (with tweaks by M&D) **now with 150-300x performance boost!** via `patternmatching.py`, and
4. `sba.py`, A not-yet-optimized implementation of Marchand & Damper's syllabification by analogy (SbA).

Read more about their algorithm [here](https://github.com/somamos/syllabification-by-analogy/files/13186641/Damper.Marchand.s.Can.syllabification.improve.pronunciation.by.analogy.of.English.pdf).

## Pronunciation Key

By the way, the pronunciation representations will seem like gibberish until you get used to the following mapping (designed by Sejnowski & Rosenberg to train NETtalk):
<details>
<summary> Click to expand table </summary>

| phoneme | example1 | example2 |
|---------|----------|----------|
| a       | odd      | father   |
| A       | hide     | bite     |
| c       | ought    | bought   |
| @       | at       | bat      |
| ^       | hut      | but      |
| W       | cow      | bout     |
| i       | eat      | pete     |
| I       | it       | bit      |
| o       | oat      | boat     |
| O       | toy      | boy      |
| E       | ed       | bet      |
| R       | hurt     | bird     |
| e       | ate      | bake     |
| U       | hood     | book     |
| u       | two      | lute     |
| b       | be       | bet      |
| C       | cheese   | chin     |
| d       | dee      | debt     |
| D       | thee     | this     |
| f       | fee      | fin      |
| g       | green    | guess    |
| h       | he       | head     |
| J       | gee      | gin      |
| k       | key      | ken      |
| l       | lee      | let      |
| m       | me       | met      |
| n       | knee     | net      |
| G       | ping     | sing     |
| p       | pee      | pet      |
| r       | read     | red      |
| s       | sea      | sit      |
| S       | she      | shin     |
| t       | tea      | test     |
| T       | theta    | thin     |
| v       | vee      | vest     |
| w       | we       | wet      |
| y       | yield    | yet      |
| z       | zee      | zoo      |
| Z       | seizure  | leisure  |
| Y       | cute     | curate   |
| L       | yentl    | ample    |
| IzM     | escapism |          |
| K       | sexual   |          |
| X       | excess   |          |
| #       | examine  |          |
| *       | one      |          |
| !       | nazi     |          |
| Q       | quest    |          |
</details>

## todo:

1. preprocess.py
    - [ ] Build and cross-validate version of dataset c that only contains words from dataset a∩b.
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
    - [X] Multiprocessing at "pattern matching" level.
    - [X] Rewrite a "complete matching" method that benefits from multiprocessing (populate_precalculated doesn't).
    - [ ] Multiprocessing at word level for cross validation.
    - [ ] Write a convenient way to compare two datasets' results.
    - [ ] Track the worst-performing input letters, output phonemes, and most challenging ground truth phonemes. 
4. sba.py
    - [X] Add sba (split encodings by syllable).
    - [X] Evaluate sba results.
5. patternmatcher.py
    - [x] Test new and improved pattern matcher.
    - [X] Port previous methods to oldpatternmatcher.py
    - [ ] Determine why lattices differ slightly between populate_optimized and populate_precalculated_legacy.   
6. lattice.py
    - [ ] Faster BFS. (Multiprocessing?)
    - [ ] Point arcs to index-agnostic versions of themselves to speed up repeat occurrences within the same word?

# Overview 

(this section needs updating).

## preprocess.py

Given dataset a (containing phoneme information and stress pattern information) and dataset b (containing syllable division information), `preprocess.py` merges them into the following form (described on page 10 of the paper):

![image](https://github.com/somamos/syllabification-by-analogy/assets/141623014/20972aa6-35d1-42e3-a0da-2a387fb5df2f)

See Appendix A of Sejnowski and Rosenberg's _Parallel Networks that Learn to Pronounce English Text_ for more details. (Contact somamosinteractive@protonmail.com for access to the datasets `a` and `b`.) 

## align.py

Data-driven "by analogy" techniques require an aligned dataset. In this case, every word's letter must map to one and only one phoneme. We implement Marchand & Damper's _Aligning Text and Phonemes for Speech Technology Applications Using an EM-Like Algorithm_ with a few tweaks and improvements. 

## pba.py

Given an input word, pronunciation by analogy searches for matching substrings in a so-called "lexical database" (a list of words mapped to their phonemes), patching the substrings together into a "lattice" to form a list of candidate pronunciations. The candidate pronunciations are then scored.

