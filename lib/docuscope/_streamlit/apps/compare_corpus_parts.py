from docuscope._imports import streamlit as st
from docuscope._imports import ds
from docuscope._imports import pandas as pd
from docuscope._imports import altair as alt
from docuscope._imports import st_aggrid

import base64
from io import BytesIO

from docuscope._streamlit import categories
from docuscope._streamlit import states as _states

# a method for preserving button selection on page interactions
# with quick clicking it can lag
def increment_counter_8():
	st.session_state.count_8 += 1

def increment_counter_9():
	st.session_state.count_9 += 1

def increment_counter_10():
	st.session_state.count_10 += 1

#prevent categories from being chosen in both multiselect
def update_tar():
	if len(list(set(st.session_state.tar) & set(st.session_state.ref))) > 0:
		item = list(set(st.session_state.tar) & set(st.session_state.ref))
		st.session_state.tar = list(set(list(st.session_state.tar))^set(item))

def update_ref():
	if len(list(set(st.session_state.tar) & set(st.session_state.ref))) > 0:
		item = list(set(st.session_state.tar) & set(st.session_state.ref))
		st.session_state.ref = list(set(list(st.session_state.ref))^set(item))

CATEGORY = categories.KEYNESS
TITLE = "Compare Corpus Parts"
KEY_SORT = 6

def main():
	# check states to prevent unlikely error
	for key, value in _states.STATES.items():
		if key not in st.session_state:
			setattr(st.session_state, key, value)

	if st.session_state.count_8 % 2 == 0:
	    idx_8 = 0
	else:
	    idx_8 = 1
	if st.session_state.count_9 % 2 == 0:
	    idx_9 = 0
	else:
	    idx_9 = 1
	if st.session_state.count_10 % 2 == 0:
	    idx_10 = 0
	else:
	    idx_10 = 1

	if bool(isinstance(st.session_state.kw_pos_cp, pd.DataFrame)) == True:
		st.sidebar.markdown("### Comparison")	
		table_radio = st.sidebar.radio("Select the keyness table to display:", ("Tokens", "Tags Only"), index=idx_8, on_change=increment_counter_8, horizontal=True)
		if table_radio == 'Tokens':
			st.sidebar.markdown("---")
			st.sidebar.markdown("### Tagset")
			tag_radio_tokens = st.sidebar.radio("Select tags to display:", ("Parts-of-Speech", "DocuScope"), index=idx_9, on_change=increment_counter_9, horizontal=True)
	
			if tag_radio_tokens == 'Parts-of-Speech':
				df = st.session_state.kw_pos_cp
			else:
				df = st.session_state.kw_ds_cp
	
			col1, col2 = st.columns([1,1])			
			with col1:
				t_cats = ', '.join(st.session_state.tar_cats)
				st.markdown(f"""##### Target corpus information:
				
				Document categories: {t_cats}\n    Number of tokens: {st.session_state.tar_tokens}\n    Number of word tokens: {st.session_state.tar_words}
				""")
			with col2:
				r_cats = ', '.join(st.session_state.ref_cats)
				st.markdown(f"""##### Reference corpus information:
				
				Document categories: {r_cats}\n    Number of tokens: {st.session_state.ref_tokens}\n    Number of word tokens: {st.session_state.ref_words}
				""")
	
			gb = st_aggrid.GridOptionsBuilder.from_dataframe(df)
			gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=100) #Add pagination
			gb.configure_column("Token", filter="agTextColumnFilter", headerCheckboxSelection = True, headerCheckboxSelectionFilteredOnly = True)
			gb.configure_column("Tag", filter="agTextColumnFilter")
			gb.configure_column("LL", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2)
			gb.configure_column("LR", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=3)
			gb.configure_column("PV", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=4)
			gb.configure_column("RF", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2)
			gb.configure_column("Range", type=["numericColumn","numberColumnFilter"], valueFormatter="(data.Range).toFixed(1)+'%'")
			gb.configure_column("RF Ref", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2)
			gb.configure_column("Range Ref", type=["numericColumn","numberColumnFilter"], valueFormatter="(data.Range).toFixed(1)+'%'")
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
							The 'LL' column refers to [log-likelihood](https://ucrel.lancs.ac.uk/llwizard.html),
							a hypothesis test measuring observed vs. expected frequencies.
							Note that a negative value means that the token is more frequent in the reference corpus than the target.\n
							The 'AF' column refers to the absolute token frequency.
							The 'RF'column refers to the relative token frequency (normalized per million tokens).
							Note that for part-of-speech tags, tokens are normalized against word tokens,
							while DocuScope tags are normalized against counts of all tokens including punctuation.
							The 'Range' column refers to the percentage of documents in which the token appears in your corpus.
							""")
				
			selected = grid_response['selected_rows'] 
			if selected:
				st.write('Selected rows')
				df = pd.DataFrame(selected).drop('_selectedRowNodeInfo', axis=1)
				st.dataframe(df)
	
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
						linko= f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="tag_frequencies.xlsx">Download Excel file</a>'
						st.markdown(linko, unsafe_allow_html=True)

			st.sidebar.markdown("---")
			st.sidebar.markdown("### Generate new table")
			st.sidebar.markdown("""
							Click the button to reset the keyness table.
							""")			
			if st.sidebar.button("Compare New Categories"):
				st.session_state.kw_pos_cp = ''
				st.session_state.kw_ds_cp = ''
				st.session_state.kt_pos_cp = ''
				st.session_state.kt_ds_cp = ''
				st.session_state.tar_tokens = 0
				st.session_state.tar_words = 0
				st.session_state.ref_tokens = 0
				st.session_state.tar_words = 0
				st.session_state.tar_cats = []
				st.session_state.ref_cats = []
				st.experimental_rerun()
			st.sidebar.markdown("---")
			
		else:
			st.sidebar.markdown("### Tagset")
			tag_radio_tags = st.sidebar.radio("Select tags to display:", ("Parts-of-Speech", "DocuScope"), index=idx_10, on_change=increment_counter_10, horizontal=True)
	
			if tag_radio_tags == 'Parts-of-Speech':
				df = st.session_state.kt_pos_cp
			else:
				df = st.session_state.kt_ds_cp
	
			col1, col2 = st.columns([1,1])
			with col1:
				t_cats = ', '.join(st.session_state.tar_cats)
				st.markdown(f"""##### Target corpus information:
				
				Document categories: {t_cats}\n    Number of tokens: {st.session_state.tar_tokens}\n    Number of word tokens: {st.session_state.tar_words}
				""")
			with col2:
				r_cats = ', '.join(st.session_state.ref_cats)
				st.markdown(f"""##### Reference corpus information:
				
				Document categories: {r_cats}\n    Number of tokens: {st.session_state.ref_tokens}\n    Number of word tokens: {st.session_state.ref_words}
				""")
		
			gb = st_aggrid.GridOptionsBuilder.from_dataframe(df)
			gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=100) #Add pagination
			gb.configure_column("Tag", filter="agTextColumnFilter", headerCheckboxSelection = True, headerCheckboxSelectionFilteredOnly = True)
			gb.configure_column("LL", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2)
			gb.configure_column("LR", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=3)
			gb.configure_column("PV", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=4)
			gb.configure_column("RF", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2)
			gb.configure_column("Range", type=["numericColumn","numberColumnFilter"], valueFormatter="(data.Range).toFixed(1)+'%'")
			gb.configure_column("RF Ref", type=["numericColumn","numberColumnFilter","customNumericFormat"], precision=2)
			gb.configure_column("Range Ref", type=["numericColumn","numberColumnFilter"], valueFormatter="(data.Range).toFixed(1)+'%'")
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
							The 'LL' column refers to [log-likelihood](https://ucrel.lancs.ac.uk/llwizard.html),
							a hypothesis test measuring observed vs. expected frequencies.
							Note that a negative value means that the token is more frequent in the reference corpus than the target.\n
							The 'AF' column refers to the absolute token frequency.
							The 'RF'column refers to the relative token frequency (normalized per 100 tokens).
							Note that for part-of-speech tags, tokens are normalized against word tokens,
							while DocuScope tags are normalized against counts of all tokens including punctuation.
							The 'Range' column refers to the percentage of documents in which the token appears in your corpus.
							""")
					
			selected = grid_response['selected_rows'] 
			if selected:
				st.write('Selected rows')
				df = pd.DataFrame(selected).drop('_selectedRowNodeInfo', axis=1)
				st.dataframe(df)
							
			st.sidebar.markdown("---")
			st.sidebar.markdown("### Plot comparisons")
			st.sidebar.markdown("""
								Click the button to genenerate a plot of comparative frequencies.
								You can use the checkboxes to plot selected rows.
								With no rows selected, all variables will be plotted.
								""")
			if st.sidebar.button("Plot resutls"):
				df_plot = df[["Tag", "RF", "RF Ref"]]
				df_plot["Mean"] = df_plot.mean(numeric_only=True, axis=1)
				df_plot.rename(columns={"Tag": "Tag", "Mean": "Mean", "RF": "Target", "RF Ref": "Reference"}, inplace = True)
				df_plot = pd.melt(df_plot, id_vars=['Tag', 'Mean'],var_name='Corpus', value_name='RF')
				df_plot.sort_values(by=["Mean", "Corpus"], ascending=[True, True], inplace=True)
					
				order = ['Target', 'Reference']
				base = alt.Chart(df_plot, height={"step": 12}).mark_bar(size=10).encode(
								x=alt.X('RF', title='Frequency (per 100 tokens)'),
								y=alt.Y('Corpus:N', title=None, sort=order, axis=alt.Axis(labels=False, ticks=False)),
								color=alt.Color('Corpus:N', sort=order),
								row=alt.Row('Tag', title=None, header=alt.Header(orient='left', labelAngle=0, labelAlign='left'), sort=alt.SortField(field='Mean', order='descending')),
								tooltip=[
								alt.Tooltip('RF:Q', title="Per 100 Tokens", format='.2')
								]).configure_facet(spacing=0.5).configure_legend(orient='top')
	
				st.altair_chart(base, use_container_width=True)
	
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
						linko= f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="tag_frequencies.xlsx">Download Excel file</a>'
						st.markdown(linko, unsafe_allow_html=True)
			
			st.sidebar.markdown("---")
			st.sidebar.markdown("### Generate new table")
			st.sidebar.markdown("""
							Click the button to reset the keyness table.
							""")			
			if st.sidebar.button("Compare New Categories"):
				st.session_state.kw_pos_cp = ''
				st.session_state.kw_ds_cp = ''
				st.session_state.kt_pos_cp = ''
				st.session_state.kt_ds_cp = ''
				st.session_state.tar_tokens = 0
				st.session_state.tar_words = 0
				st.session_state.ref_tokens = 0
				st.session_state.tar_words = 0
				st.session_state.tar_cats = []
				st.session_state.ref_cats = []
				st.experimental_rerun()
			st.sidebar.markdown("---")
	
	else:		
		st.sidebar.markdown("### Select categories to compare")
		st.sidebar.markdown("Using this tool requires processing metadata from corpus file names.")
		st.sidebar.markdown("After **target** and **reference** categories have been selected, click the button to generate a keyness table.")
		st.sidebar.markdown(":lock: Selecting of the same category as target and reference is prevented.")
		
		st.sidebar.markdown('#### Target corpus categories:')
		st.sidebar.multiselect("Select target categories:", (sorted(set(st.session_state.doccats))), on_change = update_tar, key='tar')
		
		st.sidebar.markdown('#### Reference corpus categories:')
		st.sidebar.multiselect("Select reference categories:", (sorted(set(st.session_state.doccats))), on_change = update_ref, key='ref')
		st.sidebar.markdown("---")
		
		st.sidebar.markdown("###  Generate keywords")
		st.sidebar.markdown("Use the button to generate a keywords table from your corpus.")
		if st.sidebar.button("Keyness Table of Corpus Parts"):
			if len(list(st.session_state.tar)) == 0 or len(list(st.session_state.ref)) == 0:
				st.markdown(":warning: You must select at least one category for your target and one for your reference.")
			else:
				with st.spinner('Generating keywords...'):
					tp = st.session_state.corpus
					tar_list = [item + "_" for item in list(st.session_state.tar)]
					ref_list = [item + "_" for item in list(st.session_state.ref)]
					tar_docs = {key: value for key, value in tp.items() if key.startswith(tuple(tar_list))}
					ref_docs = {key: value for key, value in tp.items() if key.startswith(tuple(ref_list))}
					#get target counts
					tar_tok = list(tar_docs.values())
					tar_tags = []
					for i in range(0,len(tar_tok)):
						tags = [x[1] for x in tar_tok[i]]
						tar_tags.append(tags)
					tar_tags = [x for xs in tar_tags for x in xs]
					tar_tokens = len(tar_tags)
					tar_words = len([x for x in tar_tags if not x.startswith('Y')])
					#get reference counts
					ref_tok = list(ref_docs.values())
					ref_tags = []
					for i in range(0,len(ref_tok)):
						tags = [x[1] for x in ref_tok[i]]
						ref_tags.append(tags)
					ref_tags = [x for xs in ref_tags for x in xs]
					ref_tokens = len(ref_tags)
					ref_words = len([x for x in ref_tags if not x.startswith('Y')])
				
					wc_tar_pos = ds.frequency_table(tar_docs, tar_words)
					wc_tar_ds = ds.frequency_table(tar_docs, tar_tokens, count_by='ds')
					tc_tar_pos = ds.tags_table(tar_docs, tar_words)
					tc_tar_ds = ds.tags_table(tar_docs, tar_tokens, count_by='ds')
	
					wc_ref_pos = ds.frequency_table(ref_docs, ref_words)
					wc_ref_ds = ds.frequency_table(ref_docs, ref_tokens, count_by='ds')
					tc_ref_pos = ds.tags_table(ref_docs, ref_words)
					tc_ref_ds = ds.tags_table(ref_docs, ref_tokens, count_by='ds')
				
					kw_pos_cp = ds.keyness_table(wc_tar_pos, wc_ref_pos)
					kw_ds_cp = ds.keyness_table(wc_tar_ds, wc_ref_ds)
					kt_pos_cp = ds.keyness_table(tc_tar_pos, tc_ref_pos, tags_only=True)
					kt_ds_cp = ds.keyness_table(tc_tar_ds, tc_ref_ds, tags_only=True)
					st.session_state.kw_pos_cp = kw_pos_cp
					st.session_state.kw_ds_cp = kw_ds_cp
					st.session_state.kt_pos_cp = kt_pos_cp
					st.session_state.kt_ds_cp = kt_ds_cp
					st.session_state.tar_tokens = tar_tokens
					st.session_state.tar_words = tar_words
					st.session_state.ref_tokens = ref_tokens
					st.session_state.ref_words = ref_words
					st.session_state.tar_cats = st.session_state.tar
					st.session_state.ref_cats = st.session_state.ref
					st.success('Keywords generated!')
					st.experimental_rerun()
		st.sidebar.markdown("---")
		
		st.markdown("""To use this tool, you must first process metadata from your file names.
		Categories of interest can be placed at the beginning of file names before an underscore:
		
		BIO_G0_02_1.txt, BIO_G0_03_1.txt, ENG_G0_16_1.txt, ENG_G0_21_1.txt, HIS_G0_02_1.txt, HIS_G0_03_1.txt
		""")
		
		st.markdown("""Processing these names would yield the categories:
		
		BIO, ENG, HIS
		""")
		
		st.markdown("""
		Those categories could then be compared in any combination.
		""")

if __name__ == "__main__":
    main()
	