# Pronunciation By Analogy
# Implements the method described by Dedina and Nusbaum (1991)’s Pronounce
# as summarized by Marchand & Damper's "Can syllabification improve
# pronunciation by analogy of English?
from lattice import Lattice, ERRORS
from patternmatcher import PatternMatcher
from oldpatternmatcher import OldPatternMatcher

USE_EXPERIMENTAL_PATTERNMATCHER = True
MULTIPROCESS_LEGACY = False

class PronouncerByAnalogy:
	def cross_validate(self, start=0):
		from datetime import datetime
		from collections.abc import Iterable
		now = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
		total = 0
		trial = start
		# Cross validate either against itself OR against some specific wordlist (whose path was passed into the constructor.)
		wordlist = list(self.lexical_database.keys()) if self.cross_validation_wordlist is None else self.cross_validation_wordlist

		trial_count = len(wordlist) - 1
		trial_word = ''
		ground_truth = ''
		# Map the strategy name to the titular stat.
		words_correct = {}
		words_total = {}
		phonemes_correct = {}
		phonemes_total = {}
		with open('Data/Results_{}.txt'.format(now), 'w', encoding='latin-1') as f:
			def end_trial(output):
				nonlocal trial
				f.write(output)
				trial += 1
			# Iterate the occurrences of this error. Return the line to append to the file.
			def count_error(code):
				description = ERRORS[code]
				PronouncerByAnalogy.simple_print(code)
				# Log instance of error code.
				words_total[description] = words_total.get(description, 0) + 1
				# Print results.
				return '{}, {}\n\n'.format(description, words_total.get(description, 0))

			while trial < trial_count:
				output = ''
				i = 0
				skipped = False
				
				trial_word = wordlist[trial]
				output += 'TRIAL {}, {}\n'.format(trial, trial_word)
				ground_truth = self.lexical_database.get(trial_word, '')
				if ground_truth == '':
					# The wordlist has a word that is not in this dict.
					trial += 1
					#print(trial, trial_count, trial_word)
					continue
				print('Loading trial #{}: {} ({})...'.format(trial, trial_word, ground_truth))

				results = self.cross_validate_pronounce(trial_word)
				if not isinstance(results, Iterable):
					# Print the error.
					error_code = results
					output += count_error(error_code)
					end_trial(output)
					continue

				for key in results:
					method = key
					phoneme_correct = 0
					total_phonemes = 0
					# Iterate words for which this trial had a result.
					words_total[key] = words_total.get(key, 0) + 1
					# Evaluate that result.
					if results[key].pronunciation == ground_truth:
						words_correct[key] = words_correct.get(key, 0) + 1
					# Iterate phonemes for which this trial had a result.
					for index, ch in enumerate(results[key].pronunciation):
						# Total always iterates.
						phonemes_total[key] = phonemes_total.get(key, 0) + 1
						if index < len(ground_truth) and ch == ground_truth[index]:
							# Correct only when correct.
							phonemes_correct[key] = phonemes_correct.get(key, 0) + 1
				for key in results:
					output += '{}, {}, {}, {}, {}\n'.format(key, words_correct.get(key, 0), words_total.get(key, 0), \
						phonemes_correct.get(key, 0), phonemes_total.get(key, 0))
					print('{}: {}, {}. {}/{} words correct ({:.2f}%), {}/{} phonemes correct ({:.2f}%)'.format(key, results[key].pronunciation, results[key].pronunciation == ground_truth, words_correct.get(key, 0), words_total.get(key, 0), \
						100*words_correct.get(key, 0)/words_total.get(key, 1), phonemes_correct.get(key, 0), phonemes_total.get(key, 0), 100*phonemes_correct.get(key, 0)/phonemes_total.get(key, 0)))
				output += '\n'
				end_trial(output)
				# Total only increments after a nonskipped trial.
				total += 1
				#print('{} / {} ({}%) Correct'.format(correct_count, total, 100*correct_count/total))

				#print('Guess: {}\nGround truth: {}'.format(best, ground_truth))
				#print('{} vs. {}'.format(ground_truth, best[0]))
				print()

	def __init__(self, dataset_path, wordlist_path=None, verbose=False):
		self.cross_validation_wordlist = None
		if wordlist_path is not None:
			self.cross_validation_wordlist = []
			with open(wordlist_path, 'r', encoding='latin-1') as e:
				for line in e:
					# For cross validating with a previous version's wordlist.
					line = line.split()

		self.pl = None
		print('Loading lexical database...')
		# Assign Lexical Database.
		self.lexical_database = {}
		self.substring_database = {}
		with open(dataset_path, 'r', encoding='latin-1') as f:
			for line in f:
				line = line.split()
				self.lexical_database[line[0]] = line[1]
				self.substring_database[line[0]] = [[line[0][i:j] for j in range(i, len(line[0]) + 1) \
					if j - i > 1] for i in range(0, len(line[0]) - 1)]

				if verbose:
					print('{}\n{}\n{}\n\n'.format(line[0], line[1], self.substring_database[line[0]]))
		self.pm = PatternMatcher(self.lexical_database)
		self.opm = OldPatternMatcher()

	# Removes input word from the dataset before pronouncing if present.
	# Returns 
	def cross_validate_pronounce(self, input_word, verbose=False):

		trimmed_lexical_database = {}
		trimmed_substring_database = {}
		answer = ''
		found = False
		for word in self.lexical_database.keys():
			if word != input_word:
				trimmed_lexical_database[word] = self.lexical_database[word]
				trimmed_substring_database[word] = self.substring_database[word]
			else:
				found = True
				answer = self.lexical_database[word]
				if verbose and not USE_EXPERIMENTAL_PATTERNMATCHER:
					print('Removed {} ({}) from dataset.'.format(input_word, answer))
		if not found:
			print('The dataset did not have {}.'.format(input_word))

		pm = None
		if USE_EXPERIMENTAL_PATTERNMATCHER:
			pm = self.pm
			pm.remove(input_word, answer)

		results, duration = PronouncerByAnalogy.pronounce(input_word, trimmed_lexical_database, trimmed_substring_database, verbose=False, pm=pm)
		if verbose:
			PronouncerByAnalogy.simple_print(results, answer)

		if USE_EXPERIMENTAL_PATTERNMATCHER:
			# Add back the word.
			pm.replace(input_word, answer)

		return results

	def pronounce_sentence(self, input_sentence, multiprocess_words=True):
		import time
		time_before = time.perf_counter()
		processed_sentence = input_sentence.lower()
		processed_sentence = ''.join([ch for ch in processed_sentence if ch in ' abcdefghijklmnopqrstuvwxyz'])
		input_words = processed_sentence.split()
		output_sentence = []
		# Results will be a list of dicts. Each dict represents a set of evaluation methods mapped to their top candidate
		# for that word.
		results_list = []
		pm = None
		if USE_EXPERIMENTAL_PATTERNMATCHER:
			pm = self.pm

		if not multiprocess_words:
			for word in input_words:
				results_list.append(PronouncerByAnalogy.pronounce(word, self.lexical_database, self.substring_database, pm=pm))
		else:
			import multiprocessing as mp
			num_processes = mp.cpu_count()
			pool = mp.Pool(processes=num_processes)
			results_list = pool.starmap(PronouncerByAnalogy.pronounce, \
				([word, self.lexical_database, self.substring_database, pm] \
				for word in input_words))
		# pronounce returns a dict of entries AND a float value.
		for tup in results_list:
			candidates_dict = tup[0]
			for key in candidates_dict:
				if len(candidates_dict) == 1 or key == '10100':
					# Convert from Candidate back to string.
					result = candidates_dict[key].pronunciation \
					if type(candidates_dict[key]) == Lattice.Candidate else candidates_dict[key]
					output_sentence.append(result)
					continue

		time_after = time.perf_counter()
		print('Sentence pronounced in {} seconds'.format(time_after - time_before))
		print('{}:'.format(input_sentence))
		print(' '.join(output_sentence))
		return

	def timed_pronounce(self, input_word, lexical_database, substring_database, verbose=False, attempt_bypass=False, pm=None):
		results, duration = PronouncerByAnalogy.pronounce(input_word, lexical_database, substring_database, verbose=verbose, attempt_bypass=attempt_bypass, pm=pm)
		return results, duration

	@staticmethod
	def pronounce(input_word, lexical_database, substring_database, pm, verbose=False, attempt_bypass=False):
		import time

		if attempt_bypass and input_word in lexical_database:
			return {'bypass': lexical_database[input_word]}

		if verbose:
			print('Building pronunciation lattice for "{}"...'.format(input_word))
		# Construct lattice.
		pl = Lattice(input_word)

		# Bigrams unrepresented in the dataset will cause gaps in lattice paths.
		pl.flag_unrepresented_bigrams(input_word, lexical_database)

		# Populate lattice.
		match_count = 0
		time_before = time.perf_counter()
		# New, optimized method with current PatternMatcher.
		if pm is not None:
			matches = pm.populate_optimized(input_word)
			for match in matches:
				key, alt_domain_representation, row_index, count = match
				match_count += count
				pl.add_forced(*match)
		# OldPatternMatcher with multiprocessing.
		elif MULTIPROCESS_LEGACY:
			pl, matches = OldPatternMatcher.manage_batch_populate(pl, \
				input_word, lexical_database, substring_database, verbose=False)
		# OldPatternMatcher without multiprocessing.
		else:
			for entry_word in lexical_database:
				phonemes = lexical_database[entry_word] 
				substrings = substring_database[entry_word]
				matches = OldPatternMatcher.populate(input_word, entry_word, phonemes, None)
				for match in matches:
					pl.add(*match)
					match_count += 1
		if verbose:
			print('{} matches found.'.format(match_count))
		time_after = time.perf_counter()
		duration = time_after - time_before
		print('Lattice populated in {} seconds'.format(duration))


		candidates = pl.find_all_paths()
		results = pl.decide(candidates)
		# Print with no regard for ground truth.
		if verbose:
			PronouncerByAnalogy.simple_print(results)
		return results, duration

	# Given a dict of string labels (describing a strategy) mapped to candidates
	# arrived at via that strategy, print.
	@staticmethod
	def simple_print(results, ground_truth=''):
		from collections.abc import Iterable		
		if not isinstance(results, Iterable) and results in ERRORS:
			print('{}: {}'.format(results, ERRORS[results]))
			return
		if ground_truth == '':
			for result in results:
				print('{}: {}'.format(result, results[result]))
			return
		for result in results:
			evaluation = 'CORRECT' if results[result].pronunciation == ground_truth else 'incorrect'
			print('{}: {}, {}'.format(result, results[result], evaluation))
		print('Ground truth: {}'.format(ground_truth))

	def compare_experimental(self, input_word, verbose=False, pm=None):
		pm = None
		# Old method.
		results1, dur1 = pba.timed_pronounce(input_word, self.lexical_database, self.substring_database, verbose=verbose, pm=pm)
		pm = self.pm
		# New, experimental method.
		results2, dur2 = pba.timed_pronounce(input_word, self.lexical_database, self.substring_database, verbose=verbose, pm=pm)
		print('Without experimental: ', end='')
		print(['{}: {}'.format(key, str(results1[key])) for key in results1])
		print('With experimental: ', end='')
		print(['{}: {}'.format(key, str(results2[key])) for key in results2])
		print('Same answers? {}. Speedup: {}x faster.'.format(results1==results2, dur1/dur2))

if __name__ == "__main__":
	USE_EXPERIMENTAL_PATTERNMATCHER = True
	MULTIPROCESS_LEGACY = False

	pba = PronouncerByAnalogy("Preprocessing/Out/output_c_2023-11-11-09-08-47.txt")

	print('\nAscertain removing and adding back each word does not change the optimized dict:')
	pba.pm.simulate_leaveoneout(pba.lexical_database, check_every=10000)

	print('\nCompare old method to new method\n(Bypasses USE_EXPERIMENTAL_PATTERNMATCHER flag):\n')
	pba.compare_experimental('deliberation')

	print('\nPronounce a sentence with the new method:\n')
	pba.pronounce_sentence('The QUICK brown FOX jumps OVER the LAZY dog.', multiprocess_words=False)

	print('\nTesting a word that is clearly not in the dataset\n(Bypasses USE_EXPERIMENTAL_PATTERNMATCHER flag):\n')
	pba.pronounce('hyperliminationatory', pba.lexical_database, pba.substring_database, pba.pm, verbose=True)

	print('\nRemove the test word from the dataset before attempt:\n')
	pba.cross_validate_pronounce('testing', verbose=True)

	print('\nCross validate with the new method.\n')