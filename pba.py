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
		# Lists all paths via bfs.
		def print_all_paths(self):
			def util(u, d, path, path_strings):
				u.visited = True
				path.append(u)
				path_strings.append(u.phoneme)
				if u == d:
					print(''.join(path_strings))
					#print(''.join([str(path) for path in path]))
				else:
					for arc in u.to_arcs:
						v = arc.to_node
						has_intermediate = len(arc.intermediate_phonemes)
						path.append(arc)
						if has_intermediate:
							path_strings.append(arc.intermediate_phonemes) # Add to path buffer.
						if v.visited == False:
							util(v, d, path, path_strings) # Recur over successor node.
						path.pop() # Wipe path buffer.
						if has_intermediate:
							path_strings.pop() 
				path.pop()	# Wipe path buffer.
				path_strings.pop() 
				u.visited = False # Allow future revisiting.
			# Set visited to False for all.
			for node in self.nodes:
				node.visited = False
			path = []
			path_strings = []
			# Begin breadth-first search listing all paths.
			util(self.start, self.end, path, path_strings)			

		def print(self):
			self.print_all_paths()

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
		pl.print()
pba = PronouncerByAnalogy()
pba.pronounce('cot')
#pba.pronounce('am_____trous')