# Pronunciation By Analogy
# Implements the method described by Dedina and Nusbaum (1991)’s Pronounce
# as summarized by Marchand & Damper's "Can syllabification improve
# pronunciation by analogy of English?
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

			self.nodes = []
			self.arcs = []

			self.start = self.Node('#', '$', -1)
			self.end = self.Node('#', '$', len(letters))
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
			for node in self.nodes:
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
				for arc in self.arcs:
					if arc == new:
						arc.count += 1
						return arc 	# Found. Iterate and return.
				self.arcs.append(new) # Not found. Add new one.
				a.to_arcs.append(new)
				b.from_arcs.append(new)
				return new				# Return.
				
			def create_or_find_node(l, p, i):
				new = self.Node(l, p, i)
				for node_ in self.nodes:
					if new == node_:
						return node_ # Found. Return.
				self.nodes.append(new) # Not found. Add new one.
				return new 				 # Return it.
			
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

	def __init__(self, path="Preprocessing/Out/output.txt"):
		print('Loading lexical database...')
		# Assign Lexical Database.
		self.lexical_database = {}
		with open(path, 'r', encoding='latin-1') as f:
			for line in f:
				line = line.split()
				self.lexical_database[line[0]] = line[1]
				#print('{}: {}'.format(line[0], line[1]))

	def pronounce(self, input_word):
		print('Building pronunciation lattice for "{}"...'.format(input_word))
		# Construct lattice.
		pl = self.PronunciationLattice(input_word)
		# Match Patterns. This is super janky but I wrote it when I was very sleepy.
		for entry_word in self.lexical_database:
			pronunciation = self.lexical_database[entry_word]
			length_difference = len(input_word) - len(entry_word)
			# a is always the longer word.
			a, b = (input_word, entry_word) if length_difference >= 0 else (entry_word, input_word)
			# i is the number of characters that will get lopped off the bigger word.
			for i in range(abs(length_difference) + 1):
				match_string = ''
				match_phone = ''
				match_indices = ''
				# Find common substring.
				# Iterate over letters in the shorter word.
				for j, char in enumerate(b):
					if char == a[j]:
						match_string += char
						# When the entry word is smaller, pronunciation needs to shift right to remain accurate.
						match_phone += pronunciation[j + i] if length_difference < 0 else pronunciation[j]
						# When the entry word is bigger, matched indices need to shift right to remain accurate.
						match_indices += str(j) + ',' if length_difference < 0 else str(j + i) + ',' # Add comma for 10+ letter words.
					else:
						match_string += ' '
						match_phone += ' '
						match_indices += ' '
				# Separate by the ' ' gaps.
				match_strings = match_string.split()
				match_phones = match_phone.split()
				match_indices = match_indices.split()
				# Ignore single-character matches.
				match_strings = [m for m in match_strings if len(m) > 1]
				match_phones = [m for m in match_phones if len(m) > 1]
				match_indices = [m for m in match_indices if len(m) > 2] # Account for comma.
				# Add each matched phoneme to lattice.
				for j, substring in enumerate(match_strings):
					# Add the substring, its phonemes, and the substring's starting index.
					# Add to lattice.
					index_start = int(match_indices[j].split(',')[0])
					pl.add(substring, match_phones[j], index_start)
				# Iterate reference point if input word is the bigger word.
				a = a[1:]
		print(pl)
		print('Done.')
		# TODO: Decision function.
		candidates = pl.find_all_paths(print_progress = True)
		best = pl.decide(candidates)
		print('Best: {}'.format([str(item) for item in best]))
pba = PronouncerByAnalogy()
#pba.pronounce('cot')
pba.pronounce('empexterumonium')