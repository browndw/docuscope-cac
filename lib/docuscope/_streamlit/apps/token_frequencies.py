from docuscope._imports import streamlit as st
from docuscope._imports import ds
from docuscope._imports import pandas as pd
from docuscope._imports import st_aggrid

import base64
from io import BytesIO

from docuscope._streamlit import categories
from docuscope._streamlit import states as _states

# a method for preserving button selection on page interactions
# with quick clicking it can lag
def increment_counter():
	st.session_state.count_1 += 1

CATEGORY = categories.FREQUENCY
TITLE = "Token Frequencies"
KEY_SORT = 2

def main():
	# check states to prevent unlikely error
	for key, value in _states.STATES.items():
		if key not in st.session_state:
			setattr(st.session_state, key, value)

	if st.session_state.count_1 % 2 == 0:
		idx = 0
	else:
		idx = 1

	if bool(isinstance(st.session_state.ft_pos, pd.DataFrame)) == True:
		st.sidebar.markdown("### Tagset")
		tag_radio = st.sidebar.radio("Select tags to display:", ("Parts-of-Speech", "DocuScope"), index=idx, on_change=increment_counter, horizontal=True)
		
		if tag_radio == 'Parts-of-Speech':
			df = st.session_state.ft_pos
		else:
			df = st.session_state.ft_ds
	
		st.markdown(f"""##### Target corpus information:
		
		Number of tokens in corpus: {st.session_state.tokens}\n    Number of word tokens in corpus: {st.session_state.words}\n    Number of documents in corpus: {st.session_state.ndocs}
		""")
			
		gb = st_aggrid.GridOptionsBuilder.from_dataframe(df)
		gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=100) #Add pagination
		gb.configure_column("Token", filter="agTextColumnFilter", headerCheckboxSelection = True, headerCheckboxSelectionFilteredOnly = True)
		gb.configure_column("Tag", filter="agTextColumnFilter")
		gb.configure_column("RF", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2)
		gb.configure_column("Range", type=["numericColumn","numberColumnFilter"], valueFormatter="(data.Range).toFixed(1)+'%'")
		gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
		gb.configure_grid_options(sideBar = {"toolPanels": ['filters']})
		go = gb.build()
		
		grid_response = st_aggrid.AgGrid(
			df,
			gridOptions=go,
			enable_enterprise_modules = False,
			data_return_mode='FILTERED_AND_SORTED', 
			update_mode='MODEL_CHANGED', 
			columns_auto_size_mode='FIT_CONTENTS',
			theme='alpine',
			height=500, 
			width='100%',
			reload_data=False
			)
				
		with st.expander("Column explanation"):
			st.markdown("""
					The 'AF' column refers to the absolute token frequency.
					The 'RF'column refers to the relative token frequency (normalized per million tokens).
					Note that for part-of-speech tags, tokens are normalized against word tokens,
					while DocuScope tags are normalized against counts of all tokens including punctuation.
					The 'Range' column refers to the percentage of documents in which the token appears in your corpus.
					""")
		
		st.sidebar.markdown("---")
		with st.sidebar.expander("Filtering and saving"):
			st.markdown("""
					Filters can be accessed by clicking on the three lines that appear while hovering over a column header.
					For text columns, you can filter by 'Equals', 'Starts with', 'Ends with', and 'Contains'.\n
					Rows can be selected before or after filtering using the checkboxes.
					(The checkbox in the header will select/deselect all rows.)\n
					If rows are selected and appear in new table below the main one,
					those selected rows will be available for download in an Excel file.
					If no rows are selected, the full table will be processed for downloading after clicking the Download button.
					""")
			
		selected = grid_response['selected_rows'] 
		if selected:
			st.write('Selected rows')
			df = pd.DataFrame(selected).drop('_selectedRowNodeInfo', axis=1)
			st.dataframe(df)
	
		st.sidebar.markdown("### Download data")
		st.sidebar.markdown("""
							Click the button to genenerate a download link.
							You can use the checkboxes to download selected rows.
							With no rows selected, the entire table will be prepared for download.
							""")
		if st.sidebar.button("Download"):
			with st.sidebar:
				with st.spinner('Creating download link...'):
					towrite = BytesIO()
					downloaded_file = df.to_excel(towrite, encoding='utf-8', index=False, header=True)
					towrite.seek(0)  # reset pointer
					b64 = base64.b64encode(towrite.read()).decode()  # some strings
					st.success('Link generated!')
					linko= f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="token_frequencies.xlsx">Download Excel file</a>'
					st.markdown(linko, unsafe_allow_html=True)
		st.sidebar.markdown("---")
				
	else:
		st.sidebar.markdown("### Generate counts")
		st.sidebar.markdown("""
					Use the button to generate a table of token 
					frequencies that can be sorted and filtered (i.e., a word list).
					""")
	
		if st.sidebar.button("Frequency Table"):
			if st.session_state.corpus == "":
				st.markdown(":neutral_face: It doesn't look like you've loaded a corpus yet.")
			else:
				with st.spinner('Processing frequencies...'):
					tp = st.session_state.corpus
					wc_pos = ds.frequency_table(tp, st.session_state.words)
					wc_ds = ds.frequency_table(tp, st.session_state.tokens, count_by='ds')
				st.session_state.ft_pos = wc_pos
				st.session_state.ft_ds = wc_ds
				st.experimental_rerun()

if __name__ == "__main__":
    main()
    