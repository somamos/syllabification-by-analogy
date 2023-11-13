# Pronunciation By Analogy
# Implements the method described by Dedina and Nusbaum (1991)’s Pronounce
# as summarized by Marchand & Damper's "Can syllabification improve
# pronunciation by analogy of English?
from lattice import Lattice, ERRORS

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
				self.simple_print(code)
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
					self.cross_validation_wordlist.append('#{}#'.format(line[0]))

		self.pl = None
		print('Loading lexical database...')
		# Assign Lexical Database.
		self.lexical_database = {}
		self.substring_database = {}
		with open(dataset_path, 'r', encoding='latin-1') as f:
			for line in f:
				# Add # and $.
				line = line.split()
				if not line[0].startswith('#') and not line[0].endswith('#'):
					line[0] = '#{}#'.format(line[0])
				if not line[1].startswith('$') and not line[1].endswith('$'):
					line[1] = '${}$'.format(line[1])
				self.lexical_database[line[0]] = line[1]
				self.substring_database[line[0]] = [[line[0][i:j] for j in range(i, len(line[0]) + 1) \
					if j - i > 1] for i in range(0, len(line[0]) - 1)]

				if verbose:
					print('{}\n{}\n{}\n\n'.format(line[0], line[1], self.substring_database[line[0]]))

	# Removes input word from the dataset before pronouncing if present.
	# Returns 
	def cross_validate_pronounce(self, input_word, verbose=False):
		if not input_word.startswith('#'):
			input_word = '#' + input_word
		if not input_word.endswith('#'):
			input_word = input_word + '#'

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
				if verbose:
					print('Removed {} ({}) from dataset.'.format(input_word, answer))
		if not found:
			print('The dataset did not have {}.'.format(input_word))
		results = self.pronounce(input_word, (trimmed_lexical_database, trimmed_substring_database), verbose=False)
		if verbose:
			self.simple_print(results, answer)

		return results

	def pronounce(self, input_word, trimmed_databases=None, verbose=False):
		print('Building lattice...')
		if not input_word.startswith('#'):
			input_word = '#' + input_word
		if not input_word.endswith('#'):
			input_word = input_word + '#'		
		# Default to the database loaded in the constructor.
		lexical_database = self.lexical_database
		substring_database = self.substring_database

		# Refer to pruned versions when called by cross_validate_pronounce.
		if trimmed_databases != None:
			lexical_database = trimmed_databases[0]
			substring_database = trimmed_databases[1]
		if verbose:
			print('Building pronunciation lattice for "{}"...'.format(input_word))
		# Construct lattice.
		self.pl = Lattice(input_word)

		# Bigrams unrepresented in the dataset will cause gaps in lattice paths.
		self.pl.flag_unrepresented_bigrams(input_word, lexical_database)

		# Second fastest.
		# The original method of Dedina and Nusbaum. Words begin left-aligned and end right-aligned.
		def populate_legacy():
			nonlocal input_word
			nonlocal entry_word
			nonlocal phonemes
			length_difference = len(input_word) - len(entry_word)
			# a is always the longer word.
			a, b = (input_word, entry_word) if length_difference >= 0 else (entry_word, input_word)
			for offset in range(abs(length_difference) + 1):
				index = -1
				length = 0
				match = ''
				char_buffer = [False, False]
				for k in range(0, len(b) + 1):
					# Iterate buffer.
					char_buffer[0] = char_buffer[1] # Begin False (default).
					char_buffer[1] = (b[k] == a[offset + k]) if k != len(b) else False # End False.
					# Currently in the middle of a match.
					if all(char_buffer):
						length += 1
						match += b[k] # Append to match.
					# Match just started.
					elif char_buffer == [False, True]:
						index = k
						length = 1
						match = b[k] # Flush match.
					# Match just ended.
					elif char_buffer == [True, False]:
						# Insufficient length.
						if length == 1:
							continue
						if length_difference < 0:
							# When the entry word is bigger, phoneme indices "shift right" to remain accurate.
							self.pl.add(match, phonemes[index + offset : index + offset + length], index)
						else:
							# When the entry word is smaller, matched indices "shift right" to remain accurate.
							self.pl.add(match, phonemes[index : index + length], index + offset)
		# Maps every possible substring greater than length 2 to their first index of occurrence
		# in order, conveniently, from smallest to largest (per starting index).
		input_precalculated_substrings = [[input_word[i:j] for j in range(i, len(input_word) + 1) if j - i > 1] for i in range(0, len(input_word) + 1)]
		# Every word has their substrings precalculated. Search for the smaller word
		# in the larger word. This is the equivalent to Marchand & Damper's improvement
		# of beginning with the end of the shorter word aligned with the start of the longer word,
		# ending with the start of the shorter word aligned with the end of the longer word, E.G.:
		#        FROM       ->           TO
		# alignment         ->         alignment
		#        malignant  ->  malignant
		def populate_precalculated():
			def add_entry(substr_index_tuple, bigger_w, length_diff):
				nonlocal entry_word # Pass this in for debug. 
				import re
				substr, i = substr_index_tuple
				indices_in_bigger = [m.start() for m in re.finditer('(?={})'.format(substr), bigger_w)]
				# Add to the lattice.
				for bigger_index in indices_in_bigger:
					# Entry word is the bigger word.
					if length_diff <= 0:
						# The smaller word's starting index, then, is i, because of how input_precalculated_substrings are organized.
						# Locate the indices in the entry word out of which to slice the phonemes.
						self.pl.add(substr, phonemes[bigger_index : bigger_index + len(substr)], i, entry_word)
					# Input word is the bigger word.
					else:
						self.pl.add(substr, phonemes[i : i + len(substr)], bigger_index, entry_word)
			# TODO: Only match upon a break. That way,
			# to,
			# tor,
			# tori,
			# these substrings won't get double counted.
			nonlocal input_precalculated_substrings
			nonlocal input_word
			nonlocal entry_word
			nonlocal phonemes

			length_difference = len(input_word) - len(entry_word)
			# Input word is shorter.
			if length_difference <= 0:
				smaller_words_substrings = input_precalculated_substrings
				bigger_word = entry_word
			else:
				smaller_words_substrings = substring_database[entry_word]
				bigger_word = input_word
			preserved_prev_substring_match = ''
			NO_MATCH = ('', -1)
		# PART 1: Prevent LEFT-ALIGNED substrings of matches, themselves, from matching.
			# A tuple saving the previous match and its index.
			# Due to the sorted order of (both input's and entries') precalculated substrings,
			# A first NON-match often implies the previous substring DID match.
			# To avoid double counting smaller sections of the same substring e.g.:
			# to,
			# tor,
			# tori,
			# we must only add items after the first nonmatch.
		# PART 2: Prevent RIGHT-ALIGNED substrings of matches, themselves, from matching.
			# The above fix does not prevent
			# tori,
			#  ori,
			#   ri
			# from matching.
			# ['#l', '#la', '#lam', '#lamp', '#lamp#']
			# ['la', 'lam', {lamp}, 'lamp#']
			# [<am>, <amp>, 'amp#']
			# [<mp>, 'mp#']
			# ['p#']
			# If the curly braced entry above matches,
			# we must log the index of the match, k, say, and disregard  
			prev_match_i_and_j = (0, 0)
			# the next n rows' first k - n indices.
			prev_matching_substring = NO_MATCH
			for i, row in enumerate(smaller_words_substrings):
				rows_since_last_match = i - prev_match_i_and_j[0]
				for j, substring in enumerate(row):
					if substring not in bigger_word:
						# Ignore when NEVER had a match.
						if prev_matching_substring == NO_MATCH:
							break
						# See PART 1 above for reasoning.
						add_entry(prev_matching_substring, bigger_word, length_difference)
						prev_match_i_and_j = i, j # see PART 2 above for reasoning.

						# Flush the buffer so we know, upon loop end, whether the last remaining prev_match
						# has been accounted for. (Imagine a scenario where the very last checked substring
						# happens to perfectly match. In such cases, the "substring not in bigger_word" branch
						# would never run. Therefore, we must check for prev_match after the loop as well.)
						preserved_prev_substring_match = prev_matching_substring[0] # Preserve this for debug.
						prev_matching_substring = NO_MATCH
						# The above case also guarantees no more matches in this row.
						break
					# Substring is in bigger word. As per PART 2 above,
					# we must ascertain this current column "does not lie in a previous mask's shadow."
					elif j >= (prev_match_i_and_j[1] - rows_since_last_match):
						# Store this in the buffer to be added upon first lack of match.
						prev_matching_substring = (substring, i)
						#print('{} will be added later...'.format(prev_matching_substring))
					else:
						print('{}: Skipping substring "{}" as a right-aligned substring of the previous match, "{}"'.format( \
							entry_word, substring, preserved_prev_substring_match))

				if prev_matching_substring != NO_MATCH:
					add_entry(prev_matching_substring, bigger_word, length_difference)
		for entry_word in lexical_database:
			phonemes = lexical_database[entry_word]
			populate_precalculated()
			#populate_legacy()
		candidates = self.pl.find_all_paths()
		results = self.pl.decide(candidates)
		# Print with no regard for ground truth.
		if verbose:
			self.simple_print(results)
		return results

	# Given a dict of string labels (describing a strategy) mapped to candidates
	# arrived at via that strategy, print.
	def simple_print(self, results, ground_truth=''):
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


pba = PronouncerByAnalogy("Preprocessing/Out/output_c_2023-11-11-09-08-47.txt")
#pba.cross_validate_pronounce('merit', verbose=True)
#results = pba.cross_validate_pronounce('mandatory', verbose=True)
#pba.pronounce('uqauqauqauqauqauqa', verbose=True)
pba.cross_validate_pronounce('personification', verbose=True)
#pba.cross_validate()


