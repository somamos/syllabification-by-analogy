# Pronunciation By Analogy
# Implements the method described by Dedina and Nusbaum (1991)’s Pronounce
# as summarized by Marchand & Damper's "Can syllabification improve
# pronunciation by analogy of English?
global DEBUG
DEBUG = False
class PronouncerByAnalogy:
	# A representation of possible pronunciations of a word.
	class PronunciationLattice:
		# Nodes are endpoints within the target word with a set location and candidate phoneme pronunciation.
		class Node:
			def __init__(self, matched_letter, phoneme, index):
				self.matched_letter = matched_letter
				self.phoneme = phoneme
				self.index = index
				self.from_arcs = [] 
				self.to_arcs = []
				self.visited = False
			def __hash__(self):
				return hash((self.matched_letter, self.phoneme, self.index))
			def __eq__(self, other):
				if not isinstance(other, type(self)):
					return NotImplemented
				return self.matched_letter == other.matched_letter \
				and self.phoneme == other.phoneme \
				and self.index == other.index
			def __ne__(self, other):
				return not self.__eq__(other)
			def __str__(self):
				return '{}'.format(self.phoneme)
		# Arcs span nodes with phonemes between them (or nothing, if the two nodes are bigrams.)
		class Arc:
			def __init__(self, intermediate_phonemes, from_node, to_node):
				self.from_node = from_node
				self.intermediate_phonemes = intermediate_phonemes
				self.to_node = to_node
				self.count = 1
			def __eq__(self, other):
				if not isinstance(other, type(self)):
					return NotImplemented
				return self.from_node == other.from_node \
				and self.intermediate_phonemes == other.intermediate_phonemes \
				and self.to_node == other.to_node
			def __ne__(self, other):
				return not self.__eq__(other)
			def __str__(self):
				return '[{}:{}]'.format(self.intermediate_phonemes, self.count)

		class Candidate:
			# Initialize candidate as empty or as shallow copy.
			def __init__(self, other=None):
				# Init as empty.
				if other == None:
					self.path = [] # Includes all nodes.
					self.arcs = [] # Arcs only.
					self.path_strings = [] # String representation of candidate pronunciation.
					self.score = 0
					self.length = 0
					return
				# Init as shallow copy.
				# Path and path string.
				self.path = other.path[:]
				self.arcs = other.arcs[:]
				self.path_strings = other.path_strings[:]
				# Heuristics.
				self.length = other.length
				self.score = other.score

			def __str__(self):
				return '{}: length {}, score {}'.format(''.join(self.path_strings), self.length, self.score)

			# Append arc to this candidate with its nodes and heuristics.
			def update(self, arc):
				# Update path and path string.
				self.path += [arc.from_node, arc]
				self.arcs += [arc]
				self.path_strings += [arc.from_node.phoneme, arc.intermediate_phonemes]
				# Update heuristics.
				self.score += arc.count
				self.length += 1
				# If it's the start, we don't need the first node, which merely represents the start node.
				if len(self.arcs) == 1:
					self.path = self.path[1:]
					self.path_strings = self.path_strings[1:]

			def pop(self):
				# Decrement from heuristics.
				self.score -= self.arcs[-1].count
				self.length -= 1
				# Pop from path and path string.
				self.arcs = self.arcs[:-1]
				self.path = self.path[:-2] # path and path_strings had [node, arc, node], three references to remove.
				self.path_strings = self.path_strings[:-2]



		# Initialize pronunciation lattice.
		def __init__(self, letters):
			self.letters = letters

			self.nodes = {}
			self.arcs = {}

			self.start = self.Node('#', '$', -1)
			self.end = self.Node('#', '$', len(letters))
			self.nodes[hash(('#', '$', -1))] = self.start
			self.nodes[hash(('#', '$', len(letters)))] = self.start
		# String interpretation of pronunciation lattice (unlinked. use print() for all linked pronunciations.)
		def __str__(self):
			s = ''
			for arc in self.arcs:
				inter_letters = ''
				if arc.from_node.index != None and arc.to_node.index != None:
					inter_letters = self.letters[arc.from_node.index + 1:arc.to_node.index]
					inter_letters = '<' + inter_letters + '>' if inter_letters != '' else ''

				key = '{}{}{}'.format(arc.from_node.matched_letter, inter_letters, arc.to_node.matched_letter)
				val = '{}{}{}'.format(arc.from_node.phoneme, arc.intermediate_phonemes, arc.to_node.phoneme)

				s += '{} [{}, {}] is pronounced {}: {} times\n'.format(key, arc.from_node.index, arc.to_node.index, val, arc.count)
			return s
		# For debugging.
		def print_nodes(self):
			for node in self.nodes:
				print('Node {} has {} arcs into it and {} arcs out of it.'.format(node.matched_letter + node.phoneme + str(node.index), len(node.from_arcs), len(node.to_arcs)))
		# Lists all paths via breadth-first search.
		def find_all_paths(self, print_progress = False):
			import sys
			min_length = sys.maxsize
			candidates = []
			def util(u, d, candidate_buffer):
				nonlocal min_length
				u.visited = True
				if u == d:
					if print_progress:
						print(candidate_buffer)
					candidates.append(self.Candidate(candidate_buffer)) # Append a shallow copy.
					min_length = candidate_buffer.length
				elif candidate_buffer.length < min_length:
					for arc in u.to_arcs:
						v = arc.to_node
						candidate_buffer.update(arc) # Append arc to buffer with its nodes and heuristics. 
						if v.visited == False:
							util(v, d, candidate_buffer) # Recur over successor node.
						candidate_buffer.pop() # Wipe candidate buffer.
				u.visited = False # Allow future revisiting.
			# Set visited to False for all.
			for node in self.nodes.values():
				node.visited = False
			candidate_buffer = self.Candidate()
			# Begin breadth-first search listing all paths.
			util(self.start, self.end, candidate_buffer)
			if len(candidates) == 0:
				print('Warning. No paths were found.')
			return candidates

		def decide(self, candidates):
			if len(candidates) == 0:
				print('Candidates list is empty.')
				return
			from operator import attrgetter
			# Find the minimum length among the candidates
			min_length = min(candidates, key=attrgetter('length')).length
			# Filter out the candidates by that length.
			min_lengths = list(filter(lambda x: x.length == min_length, candidates))
			if len(min_lengths) == 1:
				return min_lengths

			# Find the maximum score among the candidates with the minimum length
			max_score = max(min_lengths, key=attrgetter('score')).score
			# Filter out the candidates by that score.
			max_scores = list(filter(lambda x: x.score == max_score, min_lengths))
			if len(max_scores) > 1:
				print('There was a tie between {} scores.'.format(len(max_scores)))
			return max_scores

		def print(self):
			self.find_all_paths(True)

		def add(self, sub_letters, sub_phones, start_index):
			def create_or_iterate_arc(inter, a, b):
				new = self.Arc(inter, a, b)
				found = self.arcs.get(hash((inter, a, b)), None)
				if found is not None:
					found.count += 1
					return found
				self.arcs[hash((inter, a, b))] = new # Not found. Add new one.
				found2 = self.arcs.get(hash((inter, a, b)), None)
				a.to_arcs.append(new)
				b.from_arcs.append(new)
				return new				# Return.
				
			def create_or_find_node(l, p, i):
				new = self.Node(l, p, i)
				found = self.nodes.get(hash((l, p, i)), None)
				if found is not None:
					return found # Found. Return.

				self.nodes[hash((l, p, i))] = new # Not found. Add new one.
				return new 	# Return it.
			
			# Add start node.
			a = create_or_find_node(sub_letters[0], sub_phones[0], start_index)
			# Add end node.
			b = create_or_find_node(sub_letters[-1], sub_phones[-1], start_index + len(sub_letters) - 1)
			# Add arc between them.
			arc = create_or_iterate_arc(sub_phones[1:-1], a, b)
			# Handle beginning and ending nodes.
			if start_index == 0:
				start_arc = create_or_iterate_arc('', self.start, a)
			elif start_index + len(sub_letters) == len(self.letters):
				end_arc = create_or_iterate_arc('', b, self.end)

	def cross_validate(self, path="Preprocessing/Out/output.txt", start = 0):
		prev_time = time.time()
		correct = 0
		incorrect = 0
		no_paths_found = 0
		total = 0
		trial = start
		trial_count = len(self.lexical_database) - 1
		trial_word = ''
		ground_truth = ''
		while trial < trial_count:
			partial_database = {}
			i = 0
			print('Loading trial #{}...'.format(trial))
			skipped = False
			for i, line in enumerate(self.lexical_database.keys()):
				if trial == i:
					if len(line) <= 2:
						print('Skipping trial. Word "{}" not long enough.'.format(line))
						skipped = True
						break
					# Remove one word from entries.
					trial_word = line
					print('Word to pronounce: {}'.format(trial_word))
					ground_truth = self.lexical_database[line]
					#continue
				partial_database[line] = self.lexical_database[line]
			if skipped:
				trial += 1
				continue
			best = self.pronounce(trial_word)
			if best is not None:
				outputs = [''.join(candidate.path_strings) for candidate in best]
				print('Attempt(s): {}'.format(outputs))
				if ground_truth in outputs:
					correct += 1
				else:
					incorrect += 1
			else:
				print('Attempt: No paths found.')
				no_paths_found += 1
			print('Ground truth: {}'.format(ground_truth))

			print('Time to load: {}'.format(time.time() - prev_time))
			total = correct + incorrect + no_paths_found
			print('{} / {} ({}%) Correct'.format(correct, total, 100*correct/total))

			#print('{} vs. {}'.format(ground_truth, best[0]))
			trial += 1
			total += 1
			prev_time = time.time()
			print()

	def __init__(self, path="Preprocessing/Out/output.txt"):
		print('Loading lexical database...')
		# Assign Lexical Database.
		self.lexical_database = {}
		self.substring_database = {}
		with open(path, 'r', encoding='latin-1') as f:
			for line in f:
				line = line.split()
				self.lexical_database[line[0]] = line[1]
				self.substring_database[line[0]] = [[line[0][i:j] for j in range(i, len(line[0]) + 1) \
					if j - i > 1] for i in range(0, len(line[0]) + 1)]

	def pronounce(self, input_word):
		print('Building pronunciation lattice for "{}"...'.format(input_word))
		# Construct lattice.
		pl = self.PronunciationLattice(input_word)
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
							pl.add(match, phonemes[index + offset : index + offset + length], index)
						else:
							# When the entry word is smaller, matched indices "shift right" to remain accurate.
							pl.add(match, phonemes[index : index + length], index + offset)
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
				substr, i = substr_index_tuple
				indices_in_bigger = [m.start() for m in re.finditer('(?={})'.format(substr), bigger_w)]
				# Add to the lattice.
				for bigger_index in indices_in_bigger:
					# Entry word is the bigger word.
					if length_diff <= 0:
						# The smaller word's starting index, then, is i, because of how input_precalculated_substrings are organized.
						# Locate the indices in the entry word out of which to slice the phonemes.
						if DEBUG:
							print('Entry word bigger:')
							print('{}, {}, {}, {}, {}'.format(input_word, entry_word, substr, phonemes[bigger_index : bigger_index + len(substr)], i))
							print('{}[{} : {} + {}]'.format(phonemes, bigger_index, bigger_index, len(substr)))
						pl.add(substr, phonemes[bigger_index : bigger_index + len(substr)], i)
					# Input word is the bigger word.
					else:
						if DEBUG:
							print('Input word bigger:')
							print('{}, {}, {}, {}, {}'.format(input_word, entry_word, substr, phonemes[i : i + len(substr)], bigger_index))
							print('{}[{} : {} + {}]'.format(phonemes, i, i, len(substr)))
						pl.add(substr, phonemes[i : i + len(substr)], bigger_index)
			# TODO: Only match upon a break. That way,
			# to,
			# tor,
			# tori,
			# these substrings won't get double counted.
			import re
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
				smaller_words_substrings = self.substring_database[entry_word]
				bigger_word = input_word

			NO_MATCH = ('', -1)
			# A tuple saving the previous match and its index.
			# Due to the sorted order of (both input's and entries') precalculated substrings,
			# A first NON-match often implies the previous substring DID match.
			# To avoid double counting smaller sections of the same substring e.g.:
			# to,
			# tor,
			# tori,
			# we must only add items after the first nonmatch.
			prev_matching_substring = NO_MATCH
			for i, row in enumerate(smaller_words_substrings):
				for j, substring in enumerate(row):

					if substring not in bigger_word:
						# Ignore when NEVER had a match.
						if prev_matching_substring == NO_MATCH:
							break
						# See "to, tor, tori" above for reasoning.
						#print('{} is being added!'.format(prev_matching_substring))
						add_entry(prev_matching_substring, bigger_word, length_difference)
						# Flush the buffer so we know, upon loop end, whether the last remaining prev_match
						# has been accounted for or not. (Imagine a scenario where the very last checked substring
						# happens to perfectly match. In such cases, the "substring not in bigger_word" branch
						# would never run. Therefore, we must check for prev_match after the loop as well.)
						prev_matching_substring = NO_MATCH
						# The above case also guarantees no more matches in this row.
						break
					else:
						# Store this in the buffer to be added upon first lack of match.
						prev_matching_substring = (substring, i)
						#print('{} will be added later...'.format(prev_matching_substring))
				if prev_matching_substring != NO_MATCH:
					add_entry(prev_matching_substring, bigger_word, length_difference)
		for entry_word in self.lexical_database:
			phonemes = self.lexical_database[entry_word]
			populate_precalculated()
			#populate_legacy()

		print('Done.')
		print('{} nodes and {} arcs.'.format(len(pl.nodes), len(pl.arcs)))
		candidates = pl.find_all_paths()
		best = pl.decide(candidates)
		if best is not None:
			print('Best: {}'.format([str(item) for item in best]))
		return best

import time
pba = PronouncerByAnalogy()
#pba.pronounce('autoperambulatorification')
#pba.pronounce('iota')
pba.cross_validate(start=10000)
