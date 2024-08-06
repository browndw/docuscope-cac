# Copyright (C) 2024 David West Brown

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pandas as pd
import polars as pl
import st_aggrid
import streamlit as st

from docuscope._streamlit import categories as _categories
from docuscope._streamlit import states as _states
from docuscope._streamlit.utilities import analysis_functions as _analysis
from docuscope._streamlit.utilities import handlers_database as _handlers
from docuscope._streamlit.utilities import messages as _messages
from docuscope._streamlit.utilities import warnings as _warnings

CATEGORY = _categories.OTHER
TITLE = "KWIC Tables"
KEY_SORT = 8

def main():

	user_session = st.runtime.scriptrunner.script_run_context.get_script_run_ctx()
	user_session_id = user_session.session_id

	if user_session_id not in st.session_state:
		st.session_state[user_session_id] = {}
	try:
		con = st.session_state[user_session_id]["ibis_conn"]
	except:
		con = _handlers.get_db_connection(user_session_id)
		_handlers.generate_temp(_states.STATES.items(), user_session_id, con)
	
	try:
		session = pl.DataFrame.to_dict(con.table("session").to_polars(), as_series=False)
	except:
		_handlers.init_session(con)
		session = pl.DataFrame.to_dict(con.table("session").to_polars(), as_series=False)
	
	if session.get('kwic')[0] == True:
				
		df = con.table("kwic", database="target").to_pyarrow_batches(chunk_size=5000)
		df = pl.from_arrow(df).to_pandas()
		
		gb = st_aggrid.GridOptionsBuilder.from_dataframe(df)
		gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=100) #Add pagination
		gb.configure_default_column(filter="agTextColumnFilter")
		gb.configure_column("Doc ID", filter="agTextColumnFilter", headerCheckboxSelection = True, headerCheckboxSelectionFilteredOnly = True)
		gb.configure_column("Pre-Node", type="rightAligned")
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
		
		selected = grid_response['selected_rows'] 
		if selected is not None:
			df = pd.DataFrame(selected)
			n_selected = len(df.index)
			st.markdown(f"""##### Selected rows:
			   
			Number of selected tokens: {n_selected}
			""")
		
		with st.sidebar.expander("Filtering and saving"):
			st.markdown(_messages.message_filters)
		
		with st.sidebar:
			st.markdown(_messages.message_download)
			download_file = _handlers.convert_to_excel(df)

			st.download_button(
    			label="Download to Excel",
    			data=download_file,
    			file_name="kwic.xlsx",
   					 mime="application/vnd.ms-excel",
					)
		st.sidebar.markdown("---")
		
		st.sidebar.markdown(_messages.message_reset_table)
													
		if st.sidebar.button("Create New KWIC Table"):
			try:
				con.drop_table("kwic", database="target")
			except:
				pass
			_handlers.update_session('kwic', False, con)
			st.rerun()
		st.sidebar.markdown("---")
			
	else:
		
		try:
			metadata_target = _handlers.load_metadata('target')
		except:
			metadata_target = {}
		
		st.markdown(_messages.message_kwic)
		
		st.sidebar.markdown("### Node word")
		st.sidebar.markdown("""Enter a node word without spaces.
					""")				
		node_word = st.sidebar.text_input("Node word")
		
		st.sidebar.markdown("---")
		st.sidebar.markdown("### Search mode")
		search_mode = st.sidebar.radio("Select search type:", ("Fixed", "Starts with", "Ends with", "Contains"), horizontal=True)
		
		if search_mode == "Fixed":
			search_type = "fixed"
		elif search_mode == "Starts with":
			search_type = "starts_with"
		elif search_mode == "Ends with":
			search_type = "ends_with"
		else:
			search_type = "contains"
		
		st.sidebar.markdown("---")
		st.sidebar.markdown("### Case")
		case_sensitive = st.sidebar.checkbox("Make search case sensitive")
		
		if bool(case_sensitive) == True:
			ignore_case = False
		else:
			ignore_case = True
		
		st.sidebar.markdown("---")
		st.sidebar.markdown(_messages.message_generate_table)
		if st.sidebar.button("KWIC"):
			if session.get('has_target')[0] == False:
				st.write(_warnings.warning_11, unsafe_allow_html=True)
			elif node_word == "":
				st.write(_warnings.warning_14, unsafe_allow_html=True)
			elif node_word.count(" ") > 0:
				st.write(_warnings.warning_15, unsafe_allow_html=True)
			elif len(node_word) > 15:
				st.write(_warnings.warning_16, unsafe_allow_html=True)
			else:
				tok_pl = con.table("ds_tokens", database="target").to_pyarrow_batches(chunk_size=5000)
				tok_pl = pl.from_arrow(tok_pl)
				
				with st.sidebar:
					with st.spinner('Processing KWIC...'):
						kwic_df = _analysis.kwic_pl(tok_pl, node_word=node_word, search_type=search_type, ignore_case=ignore_case)
				if kwic_df.is_empty() == False:
					con.create_table("kwic", obj=kwic_df, database="target", overwrite=True)
					_handlers.update_session('kwic', True, con)
					st.rerun()
				else:
					st.markdown(_warnings.warning_12, unsafe_allow_html=True)
		st.sidebar.markdown("---")
		
if __name__ == "__main__":
    main()