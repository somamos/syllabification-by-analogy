# Pronunciation By Analogy
# Implements the method described by Dedina and Nusbaum (1991)’s Pronounce
# as summarized by Marchand & Damper's "Can syllabification improve
# pronunciation by analogy of English?
from lattice import Lattice, ERRORS
from patternmatcher import PatternMatcher
from oldpatternmatcher import OldPatternMatcher

USE_EXPERIMENTAL_PATTERNMATCHER = True
# Takes longer, but potentially yields better results by linking certain phonemes to word borders.
# Attempting to pronounce "the" without padding yields "D-R", but with padding yields (correctly) "D-x".
MULTIPROCESS_LEGACY = False

class PronouncerByAnalogy:
	@staticmethod
	def pad_if(s, padding):
		# Assume we're not padding.
		s = s[1:-1] if s.startswith('#') and s.endswith('#') else s
		# Add it back if needed.
		if padding:
			s = '#{}#'.format(s)
		return s

	def cross_validate(self, start=0, pad=True):
		from datetime import datetime
		from collections.abc import Iterable
		now = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
		total = 0
		trial = start
		ldb = self.lexical_database_pad if pad else self.lexical_database
		wordlist = list(ldb.keys())

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
				ground_truth = ldb.get(trial_word, '')
				if ground_truth == '':
					# The wordlist has a word that is not in this dict.
					trial += 1
					#print(trial, trial_count, trial_word)
					continue
				print('Loading trial #{}: {} ({})...'.format(trial, trial_word, ground_truth))

				results = self.cross_validate_pronounce(trial_word, pad=pad)
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

	# skip_every is -1 (disabled) or >= 2. Generates smaller datasets for easier testing.
	def __init__(self, output_folder, dataset_filename, skip_every=-1, offset=0, verbose=False):
		import loader as l
		import os


		self.dataset_filename = dataset_filename
		self.skip_every = skip_every
		self.offset = offset

		self.pl = None
		print('Loading lexical database...')
		# Assign Lexical Database.
		lines = 0

		def format_name(prefix, f, use_padding):
			nonlocal skip_every
			nonlocal offset
			formatted_name = '{}_{}_padding-{}'.format(prefix, f, use_padding)
			# Append the skip factor if applicable.
			formatted_name = formatted_name + '_skipping-every-' + str(skip_every) if skip_every != -1 else formatted_name
			# Append offset if applicable.
			formatted_name = formatted_name + '_offset-' + str(offset) if offset != 0 else formatted_name
			return formatted_name

		ld_name = format_name("ld", dataset_filename, False)
		ldp_name = format_name("ld", dataset_filename, True)
		sd_name = format_name("sd", dataset_filename, False)
		sdp_name = format_name("sd", dataset_filename, True)

		if not os.path.exists(output_folder):
			os.makedirs(output_folder)

		self.lexical_database = l.load(output_folder, ld_name)
		self.lexical_database_pad = l.load(output_folder, ldp_name)
		self.substring_database = l.load(output_folder, sd_name)
		self.substring_database_pad = l.load(output_folder, sdp_name)

		if self.lexical_database is None or self.lexical_database_pad is None \
		or self.substring_database is None or self.substring_database_pad is None:
			self.lexical_database = {}
			self.substring_database = {}
			self.lexical_database_pad = {}
			self.substring_database_pad = {}
			print('Loading lexical databases from text...')
			# Load the input data.
			with open('Preprocessing/Out/{}.txt'.format(dataset_filename), 'r', encoding='latin-1') as f:
				def add_entry(lex, sub, a, b):
					lex[a] = b
					sub[a] = [[a[i:j] for j in range(i, len(a) + 1) \
						if j - i > 1] for i in range(0, len(a) - 1)]

				for i, line in enumerate(f):
					# Skip every skip_every words.
					if skip_every != -1 and (i + offset)%skip_every != 0:
						continue

					if lines%10000 == 0:
						print('{} lines loaded...'.format(lines))
					line = line.split()
					# Add padded and nonpadded versions.
					add_entry(self.lexical_database, self.substring_database, line[0], line[1])
					add_entry(self.lexical_database_pad, self.substring_database_pad, '#{}#'.format(line[0]), '${}$'.format(line[1]))
					lines += 1
			print('{} lines loaded.'.format(lines))
			# Save a copy of the dataset.
			l.write(output_folder, ld_name, self.lexical_database)
			l.write(output_folder, ldp_name, self.lexical_database_pad)
			l.write(output_folder, sd_name, self.substring_database)
			l.write(output_folder, sdp_name, self.substring_database_pad)

		pm_name = format_name("optimized", dataset_filename, False)
		pmp_name = format_name("optimized", dataset_filename, True)
		self.pm = PatternMatcher(self.lexical_database, output_folder, pm_name, False, skip_every, offset)
		self.pm_pad = PatternMatcher(self.lexical_database_pad, output_folder, pmp_name, True, skip_every, offset)


	# Removes input word from the dataset before pronouncing if present.
	def cross_validate_pronounce(self, input_word, verbose=False, pad=True):
		input_word = PronouncerByAnalogy.pad_if(input_word, pad)
		ldb = self.lexical_database_pad if pad else self.lexical_database
		sdb = self.substring_database_pad if pad else self.substring_database

		trimmed_lexical_database = {}
		trimmed_substring_database = {}
		answer = ''
		found = False
		for word in ldb.keys():
			if word != input_word:
				trimmed_lexical_database[word] = ldb[word]
				trimmed_substring_database[word] = sdb[word]
			else:
				found = True
				answer = ldb[word]
				if verbose and not USE_EXPERIMENTAL_PATTERNMATCHER:
					print('Removed {} ({}) from dataset.'.format(input_word, answer))
		if not found:
			print('The dataset did not have {}.'.format(input_word))

		pm = None
		if USE_EXPERIMENTAL_PATTERNMATCHER:
			pm = self.pm_pad if pad else self.pm
			# Can't remove a word unless we have its representation.
			if answer != '':
				pm.remove(input_word, answer)

		results = PronouncerByAnalogy.pronounce(input_word, trimmed_lexical_database, trimmed_substring_database, verbose=False, pm=pm)
		if verbose:
			PronouncerByAnalogy.simple_print(results, answer)

		if USE_EXPERIMENTAL_PATTERNMATCHER:
			# Add back the word, but only if we removed it in the first place.
			if answer != '':
				pm.replace(input_word, answer)

		return results

	def pronounce_sentence(self, input_sentence, multiprocess_words=False, pad=True):
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
			pm = self.pm_pad if pad else self.pm

		ldb = self.lexical_database_pad if pad else self.lexical_database
		sdb = self.substring_database_pad if pad else self.substring_database

		if not multiprocess_words:
			for word in input_words:
				word = PronouncerByAnalogy.pad_if(word, pad)
				results_list.append(PronouncerByAnalogy.pronounce(word, ldb, sdb, pm=pm))
		else:
			import multiprocessing as mp
			num_processes = mp.cpu_count()
			pool = mp.Pool(processes=num_processes)
			results_list = pool.starmap(PronouncerByAnalogy.pronounce, \
				([word, self.lexical_database, self.substring_database, pm] \
				for word in input_words))
		# pronounce returns a dict of entries AND a float value.
		for candidates_dict in results_list:
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

	def test_pronounce(self, input_word, lexical_database, substring_database, verbose=False, attempt_bypass=False, pm=None):
		results, duration, lattice = PronouncerByAnalogy.pronounce(input_word, lexical_database, substring_database, verbose=verbose, attempt_bypass=attempt_bypass, pm=pm, test_mode=True)
		if verbose:
			print('Completed in {} seconds.'.format(duration))
			PronouncerByAnalogy.simple_print(results)
		return results, duration, lattice

	# Setting test_mode to True returns lattice for testing.
	@staticmethod
	def pronounce(input_word, lexical_database, substring_database, pm, verbose=False, attempt_bypass=False, test_mode=False):
		# Check if we're using pad.
		uses_padding = list(lexical_database)[0].startswith('#')
		input_word = PronouncerByAnalogy.pad_if(input_word, uses_padding)
		import time

		if attempt_bypass and input_word in lexical_database:
			time_before = time.perf_counter()
			results = {'bypass': lexical_database[input_word]}
			time_after = time.perf_counter()
			if verbose:
				PronouncerByAnalogy.simple_print(results)
			if test_mode:
				results = (results, time_after - time_before, None)
			return results

		if verbose:
			print('Building pronunciation lattice for "{}"...'.format(input_word))
		# Construct lattice.
		pl = Lattice(input_word)

		# Bigrams unrepresented in the dataset will cause gaps in lattice paths.
		#pl.flag_unrepresented_bigrams(input_word, lexical_database)

		# Populate lattice.
		match_count = 0
		time_before = time.perf_counter()
		# New, optimized method with current PatternMatcher.
		if pm is not None:
			matches = pm.populate_optimized(input_word, verbose=False)
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
				matches = OldPatternMatcher.populate(input_word, entry_word, phonemes, substrings)
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
		if test_mode:
			return results, duration, pl
		return results

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
	def compare_experimental(self, input_word, verbose=False, pad=True):
		pm = None
		# Old method.
		print('Old method:')
		results1, dur1, lattice1 = pba.test_pronounce(input_word, self.lexical_database, self.substring_database, verbose=False, pm=pm)
		pm = self.pm_pad if pad else self.pm
		# New, experimental method.
		print('Experimental:')
		results2, dur2, lattice2 = pba.test_pronounce(input_word, self.lexical_database, self.substring_database, verbose=False, pm=pm)

		# Compare lattices.
		Lattice.print_lattice_comparison(lattice1, lattice2)

		print('Without experimental:\n', end='')
		PronouncerByAnalogy.simple_print(results1)
		print('With experimental:\n', end='')
		PronouncerByAnalogy.simple_print(results2)
		print('Same answers? {}. Speedup: {}x faster.'.format(results1==results2, dur1/dur2))

if __name__ == "__main__":
	USE_EXPERIMENTAL_PATTERNMATCHER = True
	MULTIPROCESS_LEGACY = False

	# Huge lexical dataset.
	pba = PronouncerByAnalogy("Data/", "output_c_2023-11-11-09-08-47")
	# A way to prune the dataset while keeping distribution relatively even across the alphabet.
	#pba = PronouncerByAnalogy("Data/", "output_c_2023-11-11-09-08-47", skip_every=2000, offset=1)

	# Run a test that guarantees optimized dict structure will remain the same throughout cross validation
	#print('\nAscertain removing and adding back each word does not change the optimized dict:')
	#pba.pm.simulate_leaveoneout(pba.lexical_database, check_every=10000)
	pba.pronounce_sentence('The QUICK qzqzxz FOX jumps OVER the LAZY dog.')
	#import cProfile
	#cProfile.runctx('g(x)', {'x': 'The QUICK brown FOX jumps OVER the LAZY dog.', 'g': pba.pronounce_sentence}, {})

	pba.cross_validate_pronounce('authentication', verbose=True)

	print('\nCompare old pattern matching method to new, optimized method\n(Bypasses USE_EXPERIMENTAL_PATTERNMATCHER flag):\n')
	pba.compare_experimental('placable', verbose=True)

	print('\nPronounce a word with the new method.\n')
	pba.pronounce('the', pba.lexical_database_pad, pba.substring_database_pad, pba.pm_pad, attempt_bypass=False, verbose=True)

	print('\nPronounce a sentence with the new method:\n')
	pba.pronounce_sentence('The QUICK brown FOX jumps OVER the LAZY dog.')

	print('\nTesting a word that is clearly not in the dataset\n(Bypasses USE_EXPERIMENTAL_PATTERNMATCHER flag):')
	print('Notice how pathfinding via breadth-first-search is the current performance bottleneck.')
	pba.pronounce('solsolsolsolsol', pba.lexical_database, pba.substring_database, pba.pm, verbose=True)

	print('\nRemove the test word from the dataset before attempt:\n')
	pba.cross_validate_pronounce('testing', verbose=True)
	
	#print('\nCross validate with the new method.\n')
	#pba.cross_validate(pad=True)

