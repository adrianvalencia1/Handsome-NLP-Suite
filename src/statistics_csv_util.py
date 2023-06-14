#written by Roberto Franzosi October 2019

import sys
import GUI_util
import IO_libraries_util

if IO_libraries_util.install_all_Python_packages(GUI_util.window,"Statistics",['csv','tkinter','os','collections','pandas','numpy','scipy','itertools'])==False:
    sys.exit(0)

import os
import tkinter as tk
import tkinter.messagebox as mb
from collections import Counter
import csv
import pandas as pd
import numpy as np
from scipy import stats

import IO_files_util
import IO_csv_util
import charts_util
import GUI_IO_util
import charts_Excel_util
import IO_user_interface_util

#column_to_be_counted is the column number (starting 0 in data_list for which a count is required)
#column_name is the name that will appear as the chart name
#value is the value in a column that needs to be added up; for either POSTAG (e.g., NN) or DEPREL tags, the tag value is displayed with its description to make reading easier
#most_common([n])
#Return a list of n elements and their counts.
#When n is omitted or None, most_common() returns all elements in the counter.
def compute_statistics_CoreNLP_CoNLL_tag(data_list,column_to_be_counted,column_name,CoreNLP_tag):
    import Stanford_CoreNLP_tags_util
    column_list=[]
    column_stats=[]
    if len(data_list) != 0:
        #get all the values in the selected column
        column_list = [i[column_to_be_counted] for i in data_list]
        column_stats = Counter(column_list)
        counts = column_stats.most_common()
        column_stats = [[column_name, "Frequencies"]]
        for value, count in counts:
            if CoreNLP_tag=="POSTAG":
                if value in Stanford_CoreNLP_tags_util.dict_POSTAG:
                    description= Stanford_CoreNLP_tags_util.dict_POSTAG[value]
                    column_stats.append([value + " - " + description, count])
            elif CoreNLP_tag=="DEPREL":
                if value in Stanford_CoreNLP_tags_util.dict_DEPREL:
                    description= Stanford_CoreNLP_tags_util.dict_DEPREL[value]
                    column_stats.append([value + " - " + description, count])
            elif CoreNLP_tag=="CLAUSALTAG":
                #print("in stats_visuals value ",value)
                if value in Stanford_CoreNLP_tags_util.dict_CLAUSALTAG:
                    description= Stanford_CoreNLP_tags_util.dict_CLAUSALTAG[value]
                    column_stats.append([value + " - " + description, count])
    # print("in compute_statistics_CoreNLP_CoNLL_tag column_stats ",column_stats)
    return column_stats

# https://datatofish.com/use-pandas-to-calculate-stats-from-an-imported-csv-file/
# https://www.shanelynn.ie/summarising-aggregation-and-grouping-data-in-python-pandas/
# PANDAS - Given a csv file as input, the function will compute basic stats on a specific column
#   Mean, Median, Mode, Total sum, Maximum, Minimum, Count, Standard deviation, Variance
# The function can also perform grouping calculations (e.g., computing the Sum of salaries, grouped by the Country column or Count of salaries, grouped by the Country column)
# https://www.geeksforgeeks.org/python-math-operations-for-data-analysis/
# inputFilename must be a csv file
# inputFilename includes the file path

# fullText.sum()                     Returns sum of all values in the series
# fullText.mean()                    Returns mean of all values in series. Equals to s.sum()/s.count()
# fullText.std()                     Returns standard deviation of all values
# fullText.min() or s.max()          Return min and max values from series
# fullText.idxmin() or s.idxmax()    ns index of min or max value in series
# fullText.median()                  Returns median of all value
# fullText.mode()                    Returns mode of the series
# fullText.value_counts()            Returns series with frequency of each value
# stats=[fullText[fieldName].describe()]
# groupByField
# You can  group by more than one variable, allowing more complex queries.
#   For instance, how many calls, sms, and data entries are in each month?
#   data.groupby(['month', 'item'])['date'].count()
# .sum(), .mean(), .mode(), .median() and other such mathematical operations
#    are not applicable on string or any other data type than numeric value.
# .sum() on a string series would give an unexpected output and return a string
#   by concatenating every string.

# Using the pandas 'describe' function returns a series
#   with information like mean, mode etc depending on
#       every NUMERIC field in the input file
#       or on a specific field passed

def compute_csv_column_statistics_NoGroupBy(window,inputFilename, outputDir, openOutputFiles,
                                            createCharts, chartPackage,
                                            columnNumber=-1):
    if inputFilename[-4:]!='.csv':
        mb.showwarning(title='File type error', message="The input file\n\n" + inputFilename + "\n\nis not a csv file. The statistical function only works with input csv files.\n\nPlease, select a csv file in input and try again!")
        return None

    outputFilename=IO_files_util.generate_output_file_name(inputFilename, '', outputDir, '.csv', '', 'ungroup_stats')

    stats=[]
    if columnNumber > -1:
        loopValue=[columnNumber]
    else:
        nRecords, nColumns = IO_csv_util.GetNumberOf_Records_Columns_inCSVFile(inputFilename)
        loopValue=range(nColumns)
    # insert headers
    headers=['Column header','Number of documents',
             'Count','Mean','Mode','Median','Standard deviation','Minimum','Maximum',
                   'Skewness','Kurtosis','25% quantile','50% quantile','75% quantile']
    stats.append(headers)
    for currentColumn in loopValue:
        #reading csv file
        try:
            # squeeze 1 dimensional axis objects into scalars
            # This method is most useful when you don’t know if your object is a Series or DataFrame,
            #   but you do know it has just a single column.
            #   In that case you can safely call squeeze to ensure you have a Series.
            df = pd.read_csv(inputFilename, encoding="utf-8", on_bad_lines='skip', squeeze = True)
        except:
            mb.showwarning(title='Data encoding error', message="The input file\n\n" + inputFilename + "\n\nhas character encoding that breaks the code. The statistical function only works with utf-8 compliant files.\n\nPlease, check your input file encoding and try again!")
            return None
        if df.iloc[:, currentColumn].dtypes!='object': #alphabetic field; do NOT process
            currentName=df.iloc[:, currentColumn].name
            #currentStats=df.iloc[:, currentColumn].describe()
            inputFile_headers=IO_csv_util.get_csvfile_headers(inputFilename)
            # get maximum number of documents in Document ID iff there is a Document ID field
            if 'Document ID' in inputFile_headers:
                docIDColumn=IO_csv_util.get_columnNumber_from_headerValue(inputFile_headers,'Document ID', inputFilename)
                nDocs=df.iloc[:, docIDColumn].max()
            else:
                nDocs=1
            currentStats=nDocs,df.iloc[:, currentColumn].sum(), \
                         df.iloc[:, currentColumn].mean(), \
                         df.iloc[:, currentColumn].mode(), \
                         df.iloc[:, currentColumn].median(), \
                         df.iloc[:, currentColumn].std(), \
                         df.iloc[:, currentColumn].min(), \
                         df.iloc[:, currentColumn].max(), \
                         df.iloc[:, currentColumn].skew(),\
                         df.iloc[:, currentColumn].kurt(), \
                         df.iloc[:, currentColumn].quantile(0.25), \
                         df.iloc[:, currentColumn].quantile(0.50), \
                         df.iloc[:, currentColumn].quantile(0.75)
            currentLine=[]
            currentLine.append(currentName)
            for i in str(currentStats).replace('(', '').replace(')', '').split(','):
                if 'dtype' not in i:
                    currentLine.append(i)

            stats.append(currentLine)
        # stats.to_csv(outputFilename, encoding='utf-8')
    if len(stats)>0:
        df = pd.DataFrame(stats)
        IO_csv_util.df_to_csv(GUI_util.window, df, outputFilename, headers=None, index=False,
                              language_encoding='utf-8')
    return outputFilename

def percentile(n):
    def percentile_(x):
        return np.percentile(x, n)
    percentile_.__name__ = 'percentile_%s' % n
    return percentile_


#written by Yi Wang March 2020, edited Landau/Franzosi February 2021, November 2022

# lists are the columns to be used for grouping (e.g., Document ID, Document) as ['Document ID', 'Document']
# plotField are the columns to be used for plotting (e.g., Mean, Mode)) as ['Mean', 'Mode'] or ['Mean']
#   plotField columns MUST contain NUMERIC values
# chart_title_label is used as part of the chart_title
def compute_csv_column_statistics_groupBy(window,inputFilename, outputDir, outputFileNameLabel, groupByField: list, plotField: list, chart_title_label, createCharts, chartPackage):
    filesToOpen=[]
    outputFilename=IO_files_util.generate_output_file_name(inputFilename, '', outputDir, '.csv', '', outputFileNameLabel + '_group_stats')
    # filesToOpen.append(output_name)

    if not set(groupByField).issubset(set(IO_csv_util.get_csvfile_headers(inputFilename))):
        mb.showwarning(title='Groupby field error',
                       message="The selected groupby fields (" + ", ".join(groupByField) + ") are not in the headers (" + ", ".join(IO_csv_util.get_csvfile_headers(inputFilename)) + ") of the file " + inputFilename)

    if inputFilename[-4:] != '.csv':
        mb.showwarning(title='File type error',
                       message="The input file\n\n" + inputFilename + "\n\nis not a csv file. The statistical function only works with input csv files.\n\nPlease, select a csv file in input and try again!")
        return None
    # reading csv file
    try:
        df = pd.read_csv(inputFilename, encoding="utf-8", on_bad_lines='skip', squeeze=True)
    except:
        mb.showwarning(title='Data encoding error',
                       message="The input file\n\n" + inputFilename + "\n\nhas character encoding that breaks the code. The statistical function only works with utf-8 compliant files.\n\nPlease, check your input file encoding and try again!")
        return None

    # group the data frame by group columns
    if len(groupByField)>0:
        try:
            # np as numpy
            df_group = df.groupby(groupByField).agg([np.sum, np.mean, lambda x: stats.mode(x, keepdims=False)[0], np.median,
                                                     np.std, np.min, np.max,
                                                     stats.skew, stats.kurtosis,
                                                     percentile(25), percentile(50), percentile(75)])
        except ValueError as e:
            IO_user_interface_util.timed_alert(GUI_util.window, 5000, 'Input file error',
                    "There was an error reading the input file\n\n" + \
                    str(inputFilename) + "\n\nto group by " + str(groupByField) + "\n\nERROR RAISED: " + str(e) +
                    "\n\nIn terminal/command line and in the NLP environment, try pip install scipy --upgrade and pip install numpy --upgrade", \
                    False, '', True, silent=False)
            return None
    if len(plotField) > 0:
        column_name=plotField[0]
        try:
            df_group = df_group[[column_name]]
        except:
            return None
        df_list = [pd.concat([df_group[column_name]],keys=[column_name],names=['Column header'])]
    else:
        df_list = [pd.concat([df_group[index]],keys=[index],names=['Column header']) for index in df_group.columns.levels[0]]
    df_group = pd.concat(df_list,axis=0)
    # putting data into the original headers
    headers_stats=['Count','Mean','Mode','Median','Standard deviation','Minimum','Maximum',
                   'Skewness','Kurtosis','25% quantile','50% quantile','75% quantile']
    df_group.columns = headers_stats
    df_group.to_csv(outputFilename, encoding='utf-8')
    filesToOpen.append(outputFilename)

    if createCharts==True:
        column_name_to_be_plotted=headers_stats[1] # Mean
        column_name_to_be_plotted=column_name_to_be_plotted + ', ' + headers_stats[2] # Mode
        column_name_to_be_plotted=column_name_to_be_plotted + ', ' + headers_stats[7] # Skewness
        column_name_to_be_plotted=column_name_to_be_plotted + ', ' + headers_stats[8] # Kurtosis
        # Plot Mean, Mode, Skewness, Kurtosis
        # headers_stats = ['Count', 'Mean', 'Mode', 'Median', 'Standard deviation', 'Minimum', 'Maximum',
        #                  'Skewness', 'Kurtosis', '25% quantile', '50% quantile', '75% quantile']

        columns_to_be_plotted_xAxis=[]
        columns_to_be_plotted_yAxis=[[2,4], [2,5], [2,10], [2,11]] # document field comes first [2
        # columns_to_be_plotted_xAxis=[], columns_to_be_plotted_yAxis=['Mean', 'Mode', 'Skewness', 'Kurtosis'] # document field comes first [2
        # hover_label=['Document']
        hover_label=[]
        outputFiles = charts_util.run_all(columns_to_be_plotted_yAxis, outputFilename, outputDir,
                                                  outputFileLabel='',
                                                  chartPackage=chartPackage,
                                                  chart_type_list=["bar"],
                                                  #chart_title=column_name_to_be_plotted + '\n' + chart_title_label + ' by Document',
                                                  chart_title=column_name_to_be_plotted + '\n' + chart_title_label + ' by Document',
                                                  column_xAxis_label_var='', #Document
                                                  column_yAxis_label_var=column_name_to_be_plotted,
                                                  hover_info_column_list=hover_label,
                                                  remove_hyperlinks = True)
        if outputFiles!=None:
            if isinstance(outputFiles, str):
                filesToOpen.append(outputFiles)
            else:
                filesToOpen.extend(outputFiles)

    return filesToOpen


# The function will provide several statistical measure for a csv field values: 'Count', 'Mean', 'Mode', 'Median', 'Standard deviation', 'Minimum', 'Maximum',
#   csv field values MUST be NUMERIC!
#   'Skewness', 'Kurtosis', '25% quantile', '50% quantile', '75% quantile'
#   it will provide statistics both ungrouped and grouped by Document ID
def compute_csv_column_statistics(window,inputFilename,outputDir, outputFileNameLabel,
                groupByList, plotList, chart_title_label='', createCharts=False, chartPackage='Excel'):
    filesToOpen=[]
    if len(groupByList)==0:
        command = tk.messagebox.askyesno("Groupby fields", "Do you want to compute statistics grouping results by the values of one or more fields (e.g., the DocumentID of a CoNLL table)?")
        if command ==True:
            groupByList=GUI_IO_util.slider_widget(GUI_util.window,"Enter comma-separated csv headers for GroupBy option",1,10,'')
    # TODO TONY temporarily disconnected while waiting to fix problems in the compute_csv_column_statistics_NoGroupBy function
    # temp_outputfile = compute_csv_column_statistics_NoGroupBy(window,inputFilename,outputDir,createCharts,chartPackage)
    # if temp_outputfile!='':
    #     filesToOpen.append(temp_outputfile)
    if len(groupByList)>0:
        temp_outputfile=compute_csv_column_statistics_groupBy(window,inputFilename,outputDir,outputFileNameLabel,groupByList,plotList,chart_title_label,createCharts,chartPackage)
        if not (temp_outputfile is None):
            filesToOpen = temp_outputfile
    return filesToOpen


# written by Roberto June 2022
def get_columns_to_be_plotted(outputFilename,col):
    headers = IO_csv_util.get_csvfile_headers(outputFilename)
    col1_nunmber = IO_csv_util.get_columnNumber_from_headerValue(headers, col, outputFilename)
    col2_nunmber = IO_csv_util.get_columnNumber_from_headerValue(headers, 'Frequency', outputFilename)
    columns_to_be_plotted=[[col1_nunmber, col2_nunmber]]
    return columns_to_be_plotted

# TODO Tony, can you pass more than one value? Yngve and Frazier
# index is the string value for the column, e.g., 'Sentence ID'
def csv_data_pivot(inputFilename, index, values, no_hyperlinks=True):
    if no_hyperlinks:
        temp, no_hyperlinks_filename = IO_csv_util.remove_hyperlinks(inputFilename)
    else:
        no_hyperlinks_filename = inputFilename
    data = pd.read_csv(no_hyperlinks_filename, encoding='utf-8',on_bad_lines='skip')
    # data = data.pivot(index = 'Sentence ID', columns = 'Document', values = "Yngve score")
    data = data.pivot(index = index, columns = 'Document', values = values)
    data.to_csv(no_hyperlinks_filename, encoding='utf-8')
    # end of function and pass the document forward
    return no_hyperlinks_filename

# written by Tony Chen Gu, April 2022
# TODO TONY How does this differ from the several compute frequency options that I have extensively commented for clarity
    # the latter one seems doing the same staff  but the former one is only for stats results
# the three steps function computes
#   1. the frequencies of a given csv field (select_col) aggregating the results by (group_col and select_col).
#   2. the resulting frequencies are pivoted in order plot the data in a multi-line chart (one chart for every distinct value of select_col) by Sentence ID.
#   3. the result of pivoting is then plotted
# select_col should be one column name to be plotted eg: ['Verb Voice']
# group_col should be a list of column names eg ['Sentence ID']
# enable complete_sid to make sentence index continuous
# enable graph to make a multiline graph
# the input should be saved to a csv file first
# def compute_csv_column_frequencies(inputFilename, group_col, select_col, outputDir, chart_title,
#         graph = True, complete_sid = True, series_label = None, chartPackage = 'Excel'):
#     cols = group_col + select_col
#     if 'Excel' in chartPackage:
#        use_plotly = False
#     else:
#         use_plotly = True
#     try:
#         data,header = IO_csv_util.get_csv_data(inputFilename, True)
#         data = pd.DataFrame(data, columns=header)
#     except:
#         # an error message about unable to read the file
#         print("Error: cannot read the csv file " + inputFilename)
#         return
#     #data = CoNLL_verb_analysis_util.verb_voice_data_preparation(data)
#     #data,stats,pas,aux,act = CoNLL_verb_analysis_util.voice_output(data, group_col)
#     #data = pd.DataFrame(data,columns=header+["Verb Voice"])
#     try:
#         print(data[select_col])
#         print(data[group_col])
#     except:
#         # an error message about wrong csv file without the necessary columns
#         print("Please select the correct csv file, with correct columns")
#         return
#     name = outputDir + os.sep + os.path.splitext(os.path.basename(inputFilename))[0] + "_frequencies.csv"
#     data.to_csv(name, encoding='utf-8')
#     Excel_outputFilename=name
#     # group by both group col and select cols and get a row named count to count the number of frequencies
#     data = data.groupby(cols).size().to_frame("count")
#     data.to_csv(name, encoding='utf-8')
#     data = pd.read_csv(name, encoding='utf-8',on_bad_lines='skip')
#     # transform the data by the select columns
#     # Reshape data (produce a “pivot” table) based on column values. Uses unique values from specified index / columns to form axes of the resulting DataFrame.
#     data = data.pivot(index = group_col, columns = select_col, values = "count")
#     print(data)
#     data.to_csv(name, encoding='utf-8')
#     # complete sentence id if needed
#     if(complete_sid):
#         # TODO Samir
#         print("Completing sentence index...")
#         charts_util.add_missing_IDs(name, name)
#     print(name)
#     if(graph):
#         #TODO: need filename generation and chart_title generation
#         data = pd.read_csv(name,header=0, encoding='utf-8',on_bad_lines='skip')
#         cols_to_be_plotted = []
#         for i in range(1,len(data.columns)):
#             cols_to_be_plotted.append([0,i])
#         if series_label is None:
#             Excel_outputFilename = charts_util.run_all(cols_to_be_plotted, name, outputDir,
#                                                        "frequency_multi-line_chart", chart_type_list=["line"],
#                                                        chart_title=chart_title,
#                                                        column_xAxis_label_var="Sentence ID", chartPackage=chartPackage)
#         else:
#             Excel_outputFilename = charts_util.run_all(cols_to_be_plotted, name, outputDir,
#                                                        "frequency_multi-line_chart", chart_type_list=["line"],
#                                                        chart_title=chart_title,
#                                                        column_xAxis_label_var="Sentence ID", series_label_list=series_label,
#                                                        chartPackage=chartPackage)
#     return Excel_outputFilename


# written by Yi Wang
# edited by Roberto June 2022

# compute frequencies of a field for a specific field value and with hover-over effects (e.g., NER field, value Location)
# the function also aggregates the values by another field (e.g., NER field by Document ID)
# in INPUT the function can use either a csv file or a data frame
# in OUTPUT the function returns a csv file with frequencies for the selected field

# selected_col, hover_col, group_col are single lists with the column headers (alphabetic, rather than column number)
#   selected_col=['POS'], hover_col=[], group_col=[Sentence ID', 'Sentence', 'Document ID', 'Document']
def compute_csv_column_frequencies(window,inputFilename, inputDataFrame, outputDir,
            openOutputFiles,createCharts,chartPackage,
            selected_col, hover_col, group_col, complete_sid,
            chart_title, fileNameType='CSV',chartType='line',pivot=True):

    name = outputDir + os.sep + os.path.splitext(os.path.basename(inputFilename))[0] + "_frequencies.csv"

    filesToOpen = []
    container = []
    hover_over_header = []
    removed_hyperlinks = False
    group_col_SV = group_col.copy()

    if inputDataFrame is not None:
        if len(inputDataFrame)!=0:
            data = inputDataFrame
    else:
        with open(inputFilename,encoding='utf-8',errors='ignore') as infile:
            reader = csv.reader(x.replace('\0', '') for x in infile)
            headers = next(reader)
        header_indices = [i for i, item in enumerate(headers) if item]
        data = pd.read_csv(inputFilename, usecols=header_indices,encoding='utf-8',on_bad_lines='skip')

    # remove hyperlink before processing
    data.to_csv(inputFilename,encoding='utf-8', index=False)
    if 'Document' in headers:
        removed_hyperlinks, inputFilename = IO_csv_util.remove_hyperlinks(inputFilename)
    data = pd.read_csv(inputFilename,encoding='utf-8',on_bad_lines='skip')
    # TODO check if data is empty exit
    # fileNameType=fileNameType.replace('/','-')
    # outputFilename = IO_files_util.generate_output_file_name(inputFilename, '', outputDir,
    #                 '.csv', 'col-freq_'+fileNameType)
    file_label=''
    for col in selected_col:
        file_label = file_label + col + '_'
    if len(group_col)>0:
        if 'Document' in group_col:
            file_label = file_label + 'byDoc'
        else:
            file_label = file_label + group_col[0] # add only the first element
    outputFilename = IO_files_util.generate_output_file_name(inputFilename, '', outputDir,
                    '.csv', file_label + '_col-freq')

    if len(selected_col) == 0:
        mb.showwarning('Missing field', 'You have not selected the csv field for which to compute frequencies.\n\nPlease, select the field and try again.')
        return filesToOpen

# no aggregation by group_col --------------------------------------------------------
    elif len(selected_col) != 0 and len(group_col) == 0:
        for col in selected_col:
            data = data[col].value_counts().to_frame().reset_index()
            hdr = [col, col + ' Frequency']
            hover_over_header = []
            if len(hover_col) != 0:
                hover_header = ', '.join(hover_col)
                hover_over_header = ['Hover_over: ' + hover_header]
                hdr.append(hover_over_header)
                data.columns = hdr
                temp_str = '%s' + '\n%s' * (len(hover_col) - 1)
                data['Hover_over: ' + hover_header] = data.apply(lambda x: temp_str % tuple(x[h] for h in hover_col),
                                                                 axis=1)
                data.drop(hover_col, axis=1, inplace=True)
            else:
                data.columns = hdr
            if (complete_sid):
                # TODO Samir
                print("Completing sentence index...")
                charts_util.add_missing_IDs(outputFilename, outputFilename)
            data.to_csv(outputFilename,encoding='utf-8', index=False)
            filesToOpen.append(outputFilename)

# aggregation by group_col NO hover over ----------------------------------------
    elif len(selected_col) != 0 and len(group_col) != 0 and len(hover_col) == 0:
        columns_to_be_plotted = []
        group_list = group_col_SV.copy()
        for col in selected_col:
            # selected_col, hover_col, group_col are single lists with the column headers
            #   selected_col=['POS'], hover_col=[], group_col=[Sentence ID', 'Sentence', 'Document ID', 'Document']
            # the aggregation can deal with column items passed as integer (from visualization_chart) or
            #   alphabetic values (from statistics_NLP_main)
            # group_column_names=[]
            # create a single list
            # temp_group_column_names = group_col + selected_col
            # test for list of lists [[],[]]
            # if any(isinstance(el, list) for el in temp_group_column_names):
            #     # flatten the list of lists to a single list
            #     temp_group_column_names = [x for xs in temp_group_column_names for x in xs]
            # i = 0
            # while i<len(temp_group_column_names):
            #     t = temp_group_column_names[i]
            #     header = t
            #     # check that t is not already in the list group_column_names
            #     if isinstance(t, (int, float)):
            #         header = IO_csv_util.get_headerValue_from_columnNumber(headers, t)
            #         if group_column_names.count(header) == 0:
            #             group_column_names.append(header)
            #     else:
            #         if group_column_names.count(header) == 0:
            #             group_column_names.append(header)
            #     i = i+1
            # for col in selected_col:
            group_list.append(col)
            # counts = data.groupby(list(args)).size()
            # Convert the multi-level index to columns
            # counts = counts.reset_index(name='Counts')
            data = data.groupby(group_list).size().reset_index(name='Frequency_' + str(col))
            # SIMON should get the col of frequency in data_final
            if 'Document' in str(group_list):
                columns_to_be_plotted = [[0, 2, 3]]  # will give different bars for each value
                # columns_to_be_plotted = [[0, 3], [1, 3]]
            else:
                columns_to_be_plotted=[[0, 2],[1, 2]]
            group_list = group_col_SV.copy()

        # added TONY1
        # pivot=True
        if pivot==True:
            data = data.pivot(index = group_column_names[1:], columns = group_column_names[0], values = "Frequency")
            data.fillna(0, inplace=True)
            #data.reset_index("Document")
        if (complete_sid):
            # TODO Samir
            print("Completing sentence index...")
            charts_util.add_missing_IDs(outputFilename, outputFilename)
        data.to_csv(outputFilename,encoding='utf-8', index=False)
        filesToOpen.append(outputFilename)
        hover_over_header = []
        chartType='bar'
        # chart_title = 'Frequency Distribution of ' + col + ' Values by ' + str(group_col),
        # get_columnNumber_from_headerValue(headers, header_value, inputFilename)
        # columns_to_be_plotted = [[1, 2]]
        # columns_to_be_plotted = [[0,4],[1,7]]
        # columns_to_be_plotted_xAxis=[], columns_to_be_plotted_yAxis=get_columns_to_be_plotted(outputFilename,col)

# aggregation by group_col & hover over -----------------------------------------------
    else:
        for col_hover in hover_col:
            col = str(selected_col[0])
            temp = group_col.copy()
            temp.append(col_hover)
            c = data.groupby(group_col)[col_hover].apply(list).to_dict()

            container.append(c)

        temp = group_col.copy()
        temp.extend(selected_col) # plotting variable
        data = data.groupby(temp).size().reset_index(name='Frequency')
        for index, row in data.iterrows():
            if row[selected_col[0]] == '':
                data.at[index,'Frequency'] = 0

        hover_header = ', '.join(hover_col)
        hover_over_header=['Hover_over: ' + hover_header]
        for index, hover in enumerate(hover_col):
            df = pd.Series(container[index]).reset_index()
            temp = group_col.copy()
            temp.append(hover)
            df.columns = temp
            data = data.merge(df, how = 'left', left_on= group_col,right_on = group_col)
        temp_str = '%s'+'\n%s'* (len(hover_col)-1)
        data['Hover_over: ' + hover_header+'_y'] = data.apply(lambda x: temp_str % tuple(x[h] for h in hover_col),axis=1)
        data.drop(hover_col, axis=1, inplace=True)
        data.to_csv(outputFilename, encoding='utf-8', index=False)
        filesToOpen.extend(outputFilename)
        columns_to_be_plotted = [[1, 2]]
        hover_over_header = [hover_over_header + '_y']

# plot the data from compute_csv_column_frequencies

    if createCharts:
        outputFiles = charts_util.run_all(columns_to_be_plotted, outputFilename, outputDir,
                                              outputFileLabel=fileNameType,
                                              chartPackage=chartPackage,
                                              chart_type_list=[chartType],
                                              chart_title=chart_title,
                                              column_xAxis_label_var=col,
                                              hover_info_column_list=hover_over_header)
        if outputFiles!=None:
            if isinstance(outputFiles, str):
                filesToOpen.append(outputFiles)
            else:
                filesToOpen.extend(outputFiles)

    # we can now remove the no_hyperlinks file (i.e., inputFilename), since the frequency file has been computed
    if removed_hyperlinks:
        os.remove(inputFilename)
    return filesToOpen # several files with the charts
