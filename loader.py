import pickle

def load(folder, name):	
	print('Attempting to load {}...'.format(name))
	try:
		f = open('{}{}'.format(folder, name), 'rb')
		data = pickle.load(f)
		f.close()
		print('Found and loaded previously saved file.')
		return data
	except:
		print('{} not found.'.format(name))
		return None

def write(folder, name, data):
	print('Writing data to {} in folder {}'.format(name, folder))
	f = open('{}{}'.format(folder, name), 'wb')
	pickle.dump(data, f)
	f.close()
