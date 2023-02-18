from docuscope._imports import streamlit as st
from docuscope._imports import spacy
from docuscope._imports import ds
from docuscope._imports import string
from docuscope._imports import unidecode

import re
import pathlib
from collections import Counter
import random
import math

from docuscope._streamlit import categories
from docuscope._streamlit import states as _states

HERE = pathlib.Path(__file__).parents[1].resolve()
MODEL_LARGE = str(HERE.joinpath("models/en_docusco_spacy"))
MODEL_SMALL = str(HERE.joinpath("models/en_docusco_spacy_fc"))

CATEGORY = categories.CORPUS_LOAD
TITLE = "Mangage Corpus Data"
KEY_SORT = 1

warning_1 = """
	<div style="background-color: #fddfd7; padding-left: 5px;">
	&#128555; The files you selected could not be processed.
	Be sure that they are <b>plain text</b> files, that they are encoded as <b>UTF-8</b>, and that most of text is in English.
	For file preparation, we recommend that you use a plain text editor (and not an application like Word).
	</div>
	"""

def warning_2(duplicates):
    dups = ', '.join(duplicates)
    html_code = f'''
	<div style="background-color: #fddfd7; padding-left: 5px;">
	<p>&#128555; The files you selected could not be processed.
	Your corpus contains these <b>duplicate file names</b>:</p>
	<p><b>{dups}</b></p>
	Plese remove duplicates before processing.
	</div>
    '''
    return html_code

@st.cache(show_spinner=False, allow_output_mutation=True, suppress_st_warning=True)
def load_models():
    large_model = spacy.load(MODEL_LARGE)
    small_model = spacy.load(MODEL_SMALL)
    models = {"Large Dictionary": large_model, "Common Dictionary": small_model}
    return models

def pre_process(txt):
	txt = re.sub(r'\bits\b', 'it s', txt)
	txt = re.sub(r'\bIts\b', 'It s', txt)
	txt = " ".join(txt.split())
	return(txt)

def process_corpus(corp, detect_model, nlp_model):
	doc_ids = [doc.name for doc in corp]
	doc_ids = [doc.replace(" ", "") for doc in doc_ids]
	if len(doc_ids) > len(set(doc_ids)):
		dup_ids = [x for x in doc_ids if doc_ids.count(x) >= 2]
		tp = {}
		exceptions = []
		return tp, exceptions, dup_ids
	else:
		is_punct = re.compile("[{}]+\s*$".format(re.escape(string.punctuation)))
		is_digit = re.compile("\d[\d{}]*\s*$".format(re.escape(string.punctuation)))
		tp = {}
		exceptions = []
		dup_ids = []
		conf_eng = []
		for doc in corp:
			try:
				doc_txt = doc.getvalue().decode('utf-8')
			except:
				exceptions.append(doc.name)
			else:
				doc_txt = unidecode.unidecode(doc_txt)
				doc_id = doc.name.replace(" ", "")
				doc_txt = pre_process(doc_txt)
				doc_len = len(doc_txt)
				if doc_len > 1000000:
					n_chunks = math.ceil(doc_len/750000)
					chunk_idx = [math.ceil(i/n_chunks*doc_len) for i in range(1, n_chunks)]
					try:
						split_idx = [re.search('[\.\?!] [A-Z]', doc_txt[idx:]).span()[1] + (idx-1) for idx in chunk_idx]
					except:
						try:
							split_idx = [re.search(' ', doc_txt[idx:]).span()[0] + idx for idx in chunk_idx]
						except :
							exceptions.append(doc.name)
					else:
						split_idx.insert(0, 0)
						doc_chunks = [doc_txt[i:j] for i, j in zip(split_idx, split_idx[1:]+[None])]
						token_list = []
						tag_list = []
						iob_ent = []
						for chunk in doc_chunks:
							chunk_taged = nlp_model(chunk)
							token_chunk = [token.text for token in chunk_taged]
							ws_chunk = [token.whitespace_ for token in chunk_taged]
							token_chunk = list(map(''.join, zip(token_chunk, ws_chunk)))
							iob_chunk = [token.ent_iob_ for token in chunk_taged]
							ent_chunk = [token.ent_type_ for token in chunk_taged]
							iob_ent_chunk = list(map('-'.join, zip(iob_chunk, ent_chunk)))
							tag_chunk = [token.tag_ for token in chunk_taged]
							tag_chunk = ['Y' if bool(is_punct.match(token_chunk[i])) else v for i, v in enumerate(tag_chunk)]
							tag_chunk = ['MC' if bool(is_digit.match(token_chunk[i])) and tag_chunk[i] != 'Y' else v for i, v in enumerate(tag_chunk)]
							token_list.append(token_chunk)
							tag_list.append(tag_chunk)
							iob_ent.append(iob_ent_chunk)
						token_list = [item for sublist in token_list for item in sublist]
						tag_list = [item for sublist in tag_list for item in sublist]
						iob_ent = [item for sublist in iob_ent for item in sublist]
						tp.update({doc_id: (list(zip(token_list, tag_list, iob_ent)))})
				else:
					doc_taged = nlp_model(doc_txt)
					token_list = [token.text for token in doc_taged]
					ws_list = [token.whitespace_ for token in doc_taged]
					token_list = list(map(''.join, zip(token_list, ws_list)))
					iob_list = [token.ent_iob_ for token in doc_taged]
					ent_list = [token.ent_type_ for token in doc_taged]
					iob_ent = list(map('-'.join, zip(iob_list, ent_list)))
					tag_list = [token.tag_ for token in doc_taged]
					tag_list = ['Y' if bool(is_punct.match(token_list[i])) else v for i, v in enumerate(tag_list)]
					tag_list = ['MC' if bool(is_digit.match(token_list[i])) and tag_list[i] != 'Y' else v for i, v in enumerate(tag_list)]
					tp.update({doc_id: (list(zip(token_list, tag_list, iob_ent)))})
		return tp, exceptions, dup_ids
		
def main():
	# check states to prevent unlikely error
	for key, value in _states.STATES.items():
		if key not in st.session_state:
			setattr(st.session_state, key, value)

	if st.session_state.ndocs > 0:
		st.markdown(f"""##### Target corpus information:
		
		Number of tokens in corpus: {st.session_state.tokens}\n    Number of word tokens in corpus: {st.session_state.words}\n    Number of documents in corpus: {st.session_state.ndocs}
		""")
				
		if st.session_state.warning == 3:
			st.markdown(f"""###### The following documents were excluded from the corpus either because they are improperly encoded or have substantial segments not recognized as English (and, therefore, cannot be tagged properly):
			
			{', '.join(st.session_state.exceptions)}
			""")
		
		with st.expander("Documents:"):
			st.write(sorted(st.session_state.docids))
		
		if st.session_state.doccats != '':
			st.markdown('##### Target corpus metadata:')
			with st.expander("Counts of document categories:"):
				st.write(Counter(st.session_state.doccats))
		else:
			st.sidebar.markdown('##### Target corpus metadata:')
			load_cats = st.sidebar.radio("Do you have categories in your file names to process?", ("No", "Yes"), horizontal=True)
			if load_cats == 'Yes':
				if st.sidebar.button("Process Document Metadata"):
					with st.spinner('Processing metadata...'):
						if all(['_' in item for item in st.session_state.docids]):
							doc_cats = [re.sub(r"_\S+$", "", item, flags=re.UNICODE) for item in st.session_state.docids]
							if min([len(item) for item in doc_cats]) == 0:
								st.markdown(":no_entry_sign: Your categories don't seem to be formatted correctly. You can either proceed without assigning categories, or reset the corpus, fix your file names, and try again.")
							elif len(set(doc_cats)) > 1 and len(set(doc_cats)) < 21:
								st.session_state.doccats = doc_cats
								st.success('Processing complete!')
								st.experimental_rerun()
							else:
								st.markdown(":grimacing: Your data should contain at least 2 and no more than 20 categories. You can either proceed without assigning categories, or reset the corpus, fix your file names, and try again.")
						else:
							st.markdown(":grimacing: Your categories don't seem to be formatted correctly. You can either proceed without assigning categories, or reset the corpus, fix your file names, and try again.")
			
			st.sidebar.markdown("""---""")
		
		if st.session_state.reference != '':
			st.markdown(f"""##### Reference corpus information:
			
			Number of tokens in corpus: {st.session_state.ref_tokens}\n    Number of word tokens in corpus: {st.session_state.ref_words}\n    Number of documents in corpus: {st.session_state.ref_ndocs}
			""")
			
			if st.session_state.warning == 4:
				st.markdown(f"""###### The following documents were excluded from the corpus either because they are improperly encoded or have substantial segments not recognized as English (and, therefore, cannot be tagged properly):
			
				{', '.join(st.session_state.ref_exceptions)}
				""")

			
			with st.expander("Documents in reference corpus:"):
				st.write(sorted(st.session_state.ref_docids))
				
		else:
			st.markdown('### Reference corpus:')
			load_ref = st.radio("Would you like to load a reference corpus?", ("No", "Yes"), horizontal=True)
			if load_ref == 'Yes':
			
				if st.session_state.warning == 1:
					st.markdown(warning_1, unsafe_allow_html=True)
		
				if st.session_state.warning == 2:
					st.markdown(warning_2(st.session_state.dup_ids), unsafe_allow_html=True)


				ref_files = st.file_uploader("Upload your corpus", type=["txt"], accept_multiple_files=True, key='reffiles')
				if len(ref_files) > 0:
					st.sidebar.markdown("### Process Reference")
					st.sidebar.markdown("Click the button to process your reference corpus files.")
					if st.sidebar.button("Process Reference Corpus"):
						with st.sidebar:
							with st.spinner('Processing corpus data...'):
								models = load_models()
								nlp = models[st.session_state.model]
								detector = load_detector()
								ref_corp, exceptions, dup_ids = process_corpus(ref_files, detector, nlp)
							if len(exceptions) > 0 and bool(ref_corp) == False:
								st.session_state.warning = 1
								st.error('There was a problem proccessing your reference corpus.')
								st.experimental_rerun()
							elif len(dup_ids) > 0 and bool(ref_corp) == False:
								st.session_state.warning = 2
								st.session_state.dup_ids = set(dup_ids)
								st.error('There was a problem proccessing your reference corpus.')
								st.experimental_rerun()
							elif len(exceptions) > 0 and bool(ref_corp) == True:
								st.warning('There was a problem proccessing your reference corpus.')
								st.session_state.warning = 4
								st.session_state.ref_exceptions = exceptions
								tok = list(ref_corp.values())
								#get pos tags
								tags_pos = []
								for i in range(0,len(tok)):
									tags = [x[1] for x in tok[i]]
									tags_pos.append(tags)
								tags_pos = [x for xs in tags_pos for x in xs]
								#get ds tags
								tags_ds = []
								for i in range(0,len(tok)):
									tags = [x[2] for x in tok[i]]
									tags_ds.append(tags)
								tags_ds = [x for xs in tags_ds for x in xs]
								tags_ds = [x for x in tags_ds if x.startswith('B-')]
								#assign session states
								st.session_state.ref_tokens = len(tags_pos)
								st.session_state.ref_words = len([x for x in tags_pos if not x.startswith('Y')])
								st.session_state.reference = ref_corp
								st.session_state.ref_docids = list(ref_corp.keys())
								st.session_state.ref_ndocs = len(list(ref_corp.keys()))
								st.experimental_rerun()
							else:
								st.success('Processing complete!')
								st.session_state.warning = 0
								tok = list(ref_corp.values())
								#get pos tags
								tags_pos = []
								for i in range(0,len(tok)):
									tags = [x[1] for x in tok[i]]
									tags_pos.append(tags)
								tags_pos = [x for xs in tags_pos for x in xs]
								#get ds tags
								tags_ds = []
								for i in range(0,len(tok)):
									tags = [x[2] for x in tok[i]]
									tags_ds.append(tags)
								tags_ds = [x for xs in tags_ds for x in xs]
								tags_ds = [x for x in tags_ds if x.startswith('B-')]
								#assign session states
								st.session_state.ref_tokens = len(tags_pos)
								st.session_state.ref_words = len([x for x in tags_pos if not x.startswith('Y')])
								st.session_state.reference = ref_corp
								st.session_state.ref_docids = list(ref_corp.keys())
								st.session_state.ref_ndocs = len(list(ref_corp.keys()))
								st.experimental_rerun()
								
					st.sidebar.markdown("---")
		
		st.sidebar.markdown('### Reset all tools and files:')
		st.sidebar.markdown(":warning: Using the **reset** button will cause all files, tables, and plots to be cleared.")
		if st.sidebar.button("Reset Corpus"):
			for key in st.session_state.keys():
				del st.session_state[key]
			for key, value in _states.STATES.items():
				if key not in st.session_state:
					setattr(st.session_state, key, value)
			st.experimental_rerun()
		st.sidebar.markdown("""---""")
	
	else:
	
		st.markdown("### Processing a target corpus :dart:")
		st.markdown(":warning: Be sure that all file names are unique.")
		
		if st.session_state.warning == 1:
			st.markdown(warning_1, unsafe_allow_html=True)
		
		if st.session_state.warning == 2:
			st.markdown(warning_2(st.session_state.dup_ids), unsafe_allow_html=True)
			
		corp_files = st.file_uploader("Upload your target corpus", type=["txt"], accept_multiple_files=True)

		st.markdown("""
					From this page you can load a corpus from a selection of text (**.txt**)
					files or reset a corpus once one has been processed.\n
					Once you have loaded a target corpus, you can add a reference corpus for comparison.
					Also note that you can encode metadata into your filenames, which can used for further analysis.
					(See naming tips.)\n
					Processing times may vary, but you can expect the initial corpus processing to take roughly 1 minute for every 1 million words.
					""")
		
		with st.expander("File preparation and file naming tips"):
			st.markdown("""
					Files must be in a \*.txt format. If you are preparing files for the first time,
					it is recommended that you use a plain text editor (rather than an application like Word).
					Avoid using spaces in file names.
					Also, you needn't worry about preserving paragraph breaks, as those will be stripped out during processing.\n
					Metadata can be encoded at the beginning of a file name, before an underscore. For example: acad_01.txt, acad_02.txt, 
					blog_01.txt, blog_02.txt. These would allow you to compare **acad** vs. **blog** as categories.
					You can designate up to 20 categories.
					""")
				
		st.sidebar.markdown("### Models")
		models = load_models()
		selected_dict = st.sidebar.selectbox("Select a DocuScope Model", options=["Large Dictionary", "Common Dictionary"])
		nlp = models[selected_dict]
		st.session_state.model = selected_dict
	
		with st.sidebar.expander("Which model do I choose?"):
			st.markdown("""
					For detailed descriptions, see the tags tables available from the Help menu.
					But in short, the full dictionary has more categories and coverage than the common dictionary.
					""")		
		st.sidebar.markdown("---")
				
		if len(corp_files) > 0:
			st.sidebar.markdown("### Process Target")
			st.sidebar.markdown("Once you have selected your files, use the button to process your corpus.")
			if st.sidebar.button("Process Corpus"):
				with st.sidebar:
					with st.spinner('Processing corpus data...'):
						detector = load_detector()
						corp, exceptions, dup_ids = process_corpus(corp_files, detector, nlp)
					if len(exceptions) > 0 and bool(corp) == False:
						st.session_state.warning = 1
						st.error('There was a problem proccessing your corpus.')
						st.experimental_rerun()
					elif len(dup_ids) > 0 and bool(corp) == False:
						st.session_state.warning = 2
						st.session_state.dup_ids = set(dup_ids)
						st.error('There was a problem proccessing your corpus.')
						st.experimental_rerun()
					elif len(exceptions) > 0 and bool(corp) == True:
						st.warning('There was a problem proccessing your corpus.')
						st.session_state.warning = 3
						st.session_state.exceptions = exceptions
						tok = list(corp.values())
						#get pos tags
						tags_pos = []
						for i in range(0,len(tok)):
							tags = [x[1] for x in tok[i]]
							tags_pos.append(tags)
						tags_pos = [x for xs in tags_pos for x in xs]
						#get ds tags
						tags_ds = []
						for i in range(0,len(tok)):
							tags = [x[2] for x in tok[i]]
							tags_ds.append(tags)
						tags_ds = [x for xs in tags_ds for x in xs]
						tags_ds = [x for x in tags_ds if x.startswith('B-')]
						#assign session states
						st.session_state.tokens = len(tags_pos)
						st.session_state.words = len([x for x in tags_pos if not x.startswith('Y')])
						st.session_state.corpus = corp
						st.session_state.docids = list(corp.keys())
						st.session_state.ndocs = len(list(corp.keys()))
						#tagsets
						tags_ds = set(tags_ds)
						tags_ds = sorted(set([re.sub(r'B-', '', i) for i in tags_ds]))
						tags_pos = set(tags_pos)
						tags_pos = sorted(set([re.sub(r'\d\d$', '', i) for i in tags_pos]))
						st.session_state.tags_ds = tags_ds
						st.session_state.tags_pos = tags_pos
						st.experimental_rerun()
					else:
						st.success('Processing complete!')
						st.session_state.warning = 0
						tok = list(corp.values())
						#get pos tags
						tags_pos = []
						for i in range(0,len(tok)):
							tags = [x[1] for x in tok[i]]
							tags_pos.append(tags)
						tags_pos = [x for xs in tags_pos for x in xs]
						#get ds tags
						tags_ds = []
						for i in range(0,len(tok)):
							tags = [x[2] for x in tok[i]]
							tags_ds.append(tags)
						tags_ds = [x for xs in tags_ds for x in xs]
						tags_ds = [x for x in tags_ds if x.startswith('B-')]
						#assign session states
						st.session_state.tokens = len(tags_pos)
						st.session_state.words = len([x for x in tags_pos if not x.startswith('Y')])
						st.session_state.corpus = corp
						st.session_state.docids = list(corp.keys())
						st.session_state.ndocs = len(list(corp.keys()))
						#tagsets
						tags_ds = set(tags_ds)
						tags_ds = sorted(set([re.sub(r'B-', '', i) for i in tags_ds]))
						tags_pos = set(tags_pos)
						tags_pos = sorted(set([re.sub(r'\d\d$', '', i) for i in tags_pos]))
						st.session_state.tags_ds = tags_ds
						st.session_state.tags_pos = tags_pos
						st.experimental_rerun()
			st.sidebar.markdown("---")

if __name__ == "__main__":
    main()
