# Database a 


# We map phoneme representations defined in dataset a to the ones outlined by Sejnowski and Rosenberg 
# in their 1987 paper "Parallel Networks that Learn to Pronounce English Text."
phoneme_map = \
{
				# FROM		TO 
				# (Example words given in dataset a and S&R's NETTalk paper respectively)
	# VOWELS
	'aa': 'a', 	# _o_dd, 	f_a_ther
	'ay': 'A',	# h_i_de,	b_i_te    *I take HUGE issue with this, but Webster's Dictionary 
	'ao': 'c', 	# _ou_ght,	b_ou_ght   and Google both corroborate that no symbolic distinction 
	'ae': '@',	# _a_t,		b_a_t      exists between "hide" and "bite," even though the 
	'ah': '^',	# h_u_t,	b_u_t      difference in sound is obvious.
	'aw': 'W',	# c_ow_,	b_ou_t
	'iy': 'i',	# _ea_t,	p_e_te
	'ih': 'I',	# _i_t,		b_i_t
	'ow': 'o',	# _oa_t,	b_oa_t
	'oy': 'O',	# t_oy_,	b_oy_
	'eh': 'E',	# _e_d, 	b_e_t
	'er': 'R',	# h_ur_t,	b_ir_d
	'ey': 'e',	# _a_te,	b_a_ke	
	'uh': 'U',	# h_oo_d,	b_oo_k
	'uw': 'u',	# t_wo_,	l_u_te
	# CONSONANTS
	'b': 'b', 	# _b_e, 	_b_et
	'ch': 'C',	# _ch_eese,	_ch_in	
	'd': 'd',	# _d_ee,	_d_ebt
	'dh': 'D',	# _th_ee,	_th_is
	'f': 'f',	# _f_ee,	_f_in
	'g': 'g',	# _g_reen,	_g_uess
	'hh': 'h',	# _h_e,		_h_ead
	'jh': 'J',	# _g_ee,	_g_in
	'k': 'k',	# _k_ey,	_k_en
	'l': 'l',	# _l_ee,	_l_et
	'm': 'm',	# _m_e,		_m_et
	'n': 'n',	# _kn_ee,	_n_et
	'ng': 'G',	# pi_ng_, 	si_ng_
	'p': 'p',	# _p_ee,	_p_et
	'r': 'r',	# _r_ead,	_r_ed
	's': 's',	# _s_ea,	_s_it
	'sh': 'S',	# _sh_e,	_sh_in
	't': 't',	# _t_ea,	_t_est
	'th': 'T',	# _th_eta,	_th_in
	'v': 'v',	# _v_ee,	_v_est
	'w': 'w',	# _w_e,		_w_et
	'y': 'y',	# _y_ield,	_y_et
	'z': 'z',	# _z_ee,	_z_oo
	'zh': 'Z',	# sei_z_ure, lei_s_ure
}

# Dataset a defines 39 phonetic symbols, whereas S&R describe 51. Of the remaining 12, 
# only one cannot be extracted from dataset a. It is /:/, e.g. lo_g_ic, which dataset a treats as identical to jh.
# The other 11 belong to two categories:
# - unmapped, which represent two combined phonemes from the 39.
# - context_dependent, which are unmapped phonemes that can be salvaged from dataset a
#   using (ending) position and (lack of) stress.

unmapped = \
{						# S&R examples:
	# diphthongs		
	'yu': 'Y',	# c_u_te
	# clusters
	'kS': 'K',	# se_x_ual
	'ks': 'X',	# e_xc_ess
	'gz': '#', 	# e_x_amine
	'w^': '*', 	# _o_ne
	'ts': '!',	# na_z_i
	'kw': 'Q'	# _qu_est
}

'''
# These features described in S&R can be teased out of dataset a given additional context.
context_dependent = \
{
	# TODO: Replace 'END' with the actual character.
	# TODO: Replace the dataset a representations with S&R
									# S&R examples:
	['ah0']: 'x',					# _a_bout
	['ah0', 'l', 'END']: 'L',		# bott_le_
	['m', 'END']: 'M',				# absy_m_
	['n', 'END']: 'N'				# butto_n_
}
'''

class Word:
	def __init__(self, letters, phonemes, stresses):
		self.letters = letters
		self.phonemes = phonemes
		self.stresses = stresses
		self.syllable_count = len(stresses)

def preprocess():
	# To be filled with references to word objects.
	corpus = []

	alphabet = 'abcdefghijklmnopqrstuvwxyz'
	numeral = (0, 1, 2)

	# Database a
	with open('Raw/a.txt', 'r') as a:
		for line in a:
			# Ignore comments
			if line.startswith(';;;'): 
				continue

			line = line.lower().strip()
			word, pronunciation = line.split('  ')
			pronunciation = pronunciation.lstrip() # Sometimes, the separator was three spaces instead of two.
			if '(' in word: 
				continue	# Skip homonyms.
			letters = ''
			phonemes = ''
			stresses = []
			# Load letters.
			for ch in word:
				letters += ch if ch in alphabet else ''
			# Load pronunciations.
			current = ''
			for ch in pronunciation:
				if ch == ' ':		# The current phoneme just ended.
					# Map to S&R representation and add to phonemes.
					phonemes += phoneme_map[current]
					current = ''
				elif ch in ('0', '1', '2'):	# The current phoneme is about to end. Add the stress.
					stresses += ch
				else:
					current += ch	# Phoneme currently being built.
			# Add last phoneme.
			phonemes += phoneme_map[current]

			# Handle unmapped phonemes.
			for key in unmapped.keys():
				if key in phonemes:
					old = phonemes
					phonemes = phonemes.replace(key, unmapped[key])
					print('Simplifying {} to {}'.format(old, phonemes))
			corpus.append(Word(letters, phonemes, stresses))
			print('Added {}, {}, and {}'.format(letters, phonemes, stresses))
	# Database b

preprocess()





















