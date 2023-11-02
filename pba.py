# Pronunciation By Analogy
# Implements the method described by Dedina and Nusbaum (1991)’s Pronounce
# as summarized by Marchand & Damper's "Can syllabification improve
# pronunciation by analogy of English?

class PronouncerByAnalogy:
	def __init__(self, path="Preprocessing/Out/output.txt"):
		# Assign Lexical Database.
		self.lexical_database = {}
		with open(path, 'r', encoding='latin-1') as f:
			for line in f:
				line = line.split()
				self.lexical_database[line[0]] = line[1]
				print('{}: {}'.format(line[0], line[1]))
	def pronounce(self, input_word):
		# Match Patterns.
		wordlist = self.lexical_database.keys()
		for entry_word in self.lexical_database:
			length_difference = len(input_word) - len(entry_word)
			# a is always the longer word.
			a, b = (input_word, entry_word) if length_difference >= 0 else (entry_word, input_word)
			for i in range(abs(length_difference) + 1):
				matchstring = ''
				# Find common substring.
				# Iterate over letters in the shorter word.
				for i, char in enumerate(b):
					matchstring += char if char == a[i] else ' '
				matchstrings = matchstring.split()
				matchstrings = [m for m in matchstrings if len(m) > 1]
				if(len(matchstrings)):
					print(a)
					print(matchstrings)
					print(b)
				# Shorten longer word.
				a = a[1:]

pba = PronouncerByAnalogy()
pba.pronounce('enterprise')
