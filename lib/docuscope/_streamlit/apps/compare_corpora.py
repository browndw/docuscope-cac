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

import altair as alt
import pandas as pd
import pathlib
import polars as pl
import streamlit as st

from docuscope._streamlit import categories as _categories
from docuscope._streamlit.utilities import analysis_functions as _analysis
from docuscope._streamlit.utilities import handlers_database as _handlers
from docuscope._streamlit.utilities import messages as _messages
from docuscope._streamlit.utilities import warnings as _warnings

CATEGORY = _categories.KEYNESS
TITLE = "Compare Corpora"
KEY_SORT = 5

def main():
	
	user_session = st.runtime.scriptrunner.script_run_context.get_script_run_ctx()
	user_session_id = user_session.session_id

	if user_session_id not in st.session_state:
		st.session_state[user_session_id] = {}
	try:
		session = pl.DataFrame.to_dict(st.session_state[user_session_id]["session"], as_series=False)
	except:
		_handlers.init_session(user_session_id)
		session = pl.DataFrame.to_dict(st.session_state[user_session_id]["session"], as_series=False)

	if session.get('keyness_table')[0] == True:
	
		_handlers.load_widget_state(pathlib.Path(__file__).stem, user_session_id)
		metadata_target = _handlers.load_metadata('target', user_session_id)
		metadata_reference = _handlers.load_metadata('reference', user_session_id)


		col1, col2 = st.columns([1,1])
		with col1:
			st.markdown(_messages.message_target_info(metadata_target))
		with col2:
			st.markdown(_messages.message_reference_info(metadata_reference))
		
		st.markdown("Showing keywords that reach significance at *p* < 0.01")
		
		st.sidebar.markdown("### Comparison")	
		table_radio = st.sidebar.radio("Select the keyness table to display:", ("Tokens", "Tags Only"), key = _handlers.persist("kt_radio1", pathlib.Path(__file__).stem, user_session_id), horizontal=True)
		st.sidebar.markdown("---")
		if table_radio == 'Tokens':
			tag_radio = st.sidebar.radio("Select tags to display:", ("Parts-of-Speech", "DocuScope"), key = _handlers.persist("kt_radio2", pathlib.Path(__file__).stem, user_session_id), horizontal=True)
			if tag_radio == 'Parts-of-Speech':
				tag_type = st.sidebar.radio("Select from general or specific tags", ("General", "Specific"), horizontal=True)			
				if tag_type == 'General':
					df = st.session_state[user_session_id]["target"]["kw_pos"]
					df = _analysis.freq_simplify_pl(df)
				else:
					df = st.session_state[user_session_id]["target"]["kw_pos"]
			else:			
				df = st.session_state[user_session_id]["target"]["kw_ds"]
			
			if df.height == 0 or df is None:
				cats = []
			elif df.height > 0:
				cats = sorted(df.get_column("Tag").unique().to_list())

			filter_vals = st.multiselect("Select tags to filter:", (cats))
			if len(filter_vals) > 0:
				df = df.filter(pl.col("Tag").is_in(filter_vals))

			st.dataframe(df, hide_index=True, 
					column_config={
						"Range": st.column_config.NumberColumn(format="%.2f %%"),
						"Range_Ref": st.column_config.NumberColumn(format="%.2f %%"),
						"RF_Ref": st.column_config.NumberColumn(format="%.2f"),
						"RF": st.column_config.NumberColumn(format="%.2f")}
			)
			
			with st.expander("Column explanation"):
				st.markdown(_messages.message_columns_keyness)
							
			st.sidebar.markdown("---")

			download_table = st.sidebar.toggle("Download to Excel?")
			if download_table == True:
				with st.sidebar:
					st.markdown(_messages.message_download)
					download_file = _handlers.convert_to_excel(df.to_pandas())

					st.download_button(
						label="Download to Excel",
						data=download_file,
						file_name="keywords_tokens.xlsx",
							mime="application/vnd.ms-excel",
							)
			st.sidebar.markdown("---")
	
		else:
			st.sidebar.markdown("### Tagset")
			tag_radio_tags = st.sidebar.radio("Select tags to display:", ("Parts-of-Speech", "DocuScope"), key = _handlers.persist("kt_radio3", pathlib.Path(__file__).stem, user_session_id), horizontal=True)
	
			if tag_radio_tags == 'Parts-of-Speech':
				df = st.session_state[user_session_id]["target"]["kt_pos"].filter(pl.col("Tag") != "FU")
			else:
				df = st.session_state[user_session_id]["target"]["kt_ds"].filter(pl.col("Tag") != "Untagged")
			
			if df.height == 0 or df is None:
				cats = []
			elif df.height > 0:
				cats = sorted(df.get_column("Tag").unique().to_list())

			filter_vals = st.multiselect("Select tags to filter:", (cats))
			if len(filter_vals) > 0:
				df = df.filter(pl.col("Tag").is_in(filter_vals))

			st.dataframe(df, hide_index=True, 
					column_config={
						"Range": st.column_config.NumberColumn(format="%.2f %%"),
						"Range_Ref": st.column_config.NumberColumn(format="%.2f %%"),
						"RF": st.column_config.NumberColumn(format="%.2f"),
						"RF_Ref": st.column_config.NumberColumn(format="%.2f")}
			)
			
			with st.expander("Column explanation"):
				st.markdown(_messages.message_columns_keyness)
				
			st.sidebar.markdown("---")
			st.sidebar.markdown(_messages.message_generate_plot)
			
			if st.sidebar.button('Plot resutls'):
				df_plot = df.to_pandas()
				df_plot = df_plot[['Tag', 'RF', 'RF_Ref']]
				df_plot['Mean'] = df_plot.mean(numeric_only=True, axis=1)
				df_plot.rename(columns={'Tag': 'Tag', 'Mean': 'Mean', 'RF': 'Target', 'RF_Ref': 'Reference'}, inplace = True)
				df_plot = pd.melt(df_plot, id_vars=['Tag', 'Mean'],var_name='Corpus', value_name='RF')
				df_plot.sort_values(by=['Mean', 'Corpus'], ascending=[True, True], inplace=True)
					
				order = ['Target', 'Reference']
				base = alt.Chart(df_plot, height={"step": 12}).mark_bar(size=10).encode(
							x=alt.X('RF', title='Frequency (per 100 tokens)'),
							y=alt.Y('Corpus:N', title=None, sort=order, axis=alt.Axis(labels=False, ticks=False)),
							color=alt.Color('Corpus:N', sort=order, scale=alt.Scale(scheme='category10')),
							row=alt.Row('Tag', title=None, header=alt.Header(orient='left', labelAngle=0, labelAlign='left'), sort=alt.SortField(field='Mean', order='descending')),
							tooltip=[
								alt.Tooltip('Tag'),
								alt.Tooltip('RF:Q', title="RF", format='.2')
							]).configure_facet(spacing=2.5).configure_legend(orient='top')				
				
				st.markdown(_messages.message_disable_full, unsafe_allow_html=True)
				st.altair_chart(base, use_container_width=True)
					
			download_table = st.sidebar.toggle("Download to Excel?")
			if download_table == True:
				with st.sidebar:
					st.markdown(_messages.message_download)
					download_file = _handlers.convert_to_excel(df.to_pandas())

					st.download_button(
						label="Download to Excel",
						data=download_file,
						file_name="keywords_tags.xlsx",
							mime="application/vnd.ms-excel",
							)
			st.sidebar.markdown("---")
	
	else:
		
		st.markdown(_messages.message_keyness)
		
		st.sidebar.markdown(_messages.message_generate_table)
		
		if st.sidebar.button("Keyness Table"):
			if session.get('has_target')[0] == False:
				st.markdown(_warnings.warning_11, unsafe_allow_html=True)
			elif session.get('has_reference')[0] == False:
				st.markdown(_warnings.warning_17, unsafe_allow_html=True)
			else:
				with st.sidebar:
					with st.spinner('Generating keywords...'):
					
						wc_tar_pos = st.session_state[user_session_id]["target"]["ft_pos"]
						wc_tar_ds = st.session_state[user_session_id]["target"]["ft_ds"]
						tc_tar_pos = st.session_state[user_session_id]["target"]["tt_pos"]
						tc_tar_ds = st.session_state[user_session_id]["target"]["tt_ds"]

						wc_ref_pos = st.session_state[user_session_id]["reference"]["ft_pos"]
						wc_ref_ds = st.session_state[user_session_id]["reference"]["ft_ds"]
						tc_ref_pos = st.session_state[user_session_id]["reference"]["tt_pos"]
						tc_ref_ds = st.session_state[user_session_id]["reference"]["tt_ds"]
						
						kw_pos = _analysis.keyness_pl(wc_tar_pos, wc_ref_pos)
						kw_ds  = _analysis.keyness_pl(wc_tar_ds, wc_ref_ds)
						kt_pos = _analysis.keyness_pl(tc_tar_pos, tc_ref_pos, tags_only=True)
						kt_ds  = _analysis.keyness_pl(tc_tar_ds, tc_ref_ds, tags_only=True)

						if "kw_pos" not in st.session_state[user_session_id]["target"]:
							st.session_state[user_session_id]["target"]["kw_pos"] = {}
						st.session_state[user_session_id]["target"]["kw_pos"] = kw_pos
						if "kw_ds" not in st.session_state[user_session_id]["target"]:
							st.session_state[user_session_id]["target"]["kw_ds"] = {}
						st.session_state[user_session_id]["target"]["kw_ds"] = kw_ds
						if "kt_pos" not in st.session_state[user_session_id]["target"]:
							st.session_state[user_session_id]["target"]["kt_pos"] = {}
						st.session_state[user_session_id]["target"]["kt_pos"] = kt_pos
						if "kt_ds" not in st.session_state[user_session_id]["target"]:
							st.session_state[user_session_id]["target"]["kt_ds"] = {}
						st.session_state[user_session_id]["target"]["kt_ds"] = kt_ds
						_handlers.update_session('keyness_table', True, user_session_id)
						st.success('Keywords generated!')
						st.rerun()
		
		st.sidebar.markdown("---")		

if __name__ == "__main__":
    main()