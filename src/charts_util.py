# Written by Yuhang Feng November 2019-April 2020
# Written by Yuhang Feng November 2019-April 2020
# Edited by Roberto Franzosi, Tony May 2022


import sys
import GUI_util
import IO_libraries_util

if IO_libraries_util.install_all_Python_packages(GUI_util.window, "charts_util",
                                          ['csv', 'os','collections','openpyxl', 'pandas', 'numpy',  'plotly', 're', 'tkinter']) == False:
    sys.exit(0)

import plotly
from plotly.subplots import make_subplots
plotly.offline.init_notebook_mode(connected=True)
#import warnings
#warnings.filterwarnings("ignore")

import numpy as np
import re

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import tkinter.messagebox as mb
from collections import Counter
import pandas as pd
import os

import IO_csv_util
import IO_user_interface_util
import charts_plotly_util
import charts_Excel_util
import statistics_csv_util

# Prepare the data (data_to_be_plotted) to be used in charts_Excel_util.create_excel_chart with the format:
#   the variable has this format:
# (['little, pig', 22])
#   one serie: [[['Name1','Frequency'], ['A', 7]]]
#   two series: [[['Name1','Frequency'], ['A', 7]], [['Name2','Frequency'], ['B', 4]]]
#   three series: [[['Name1','Frequency'], ['A', 7]], [['Name2','Frequency'], ['B', 4]], [['Name3','Frequency'], ['C', 9]]]
#   more series: ..........
# inputFilename has the full path
# columns_to_be_plotted is a double list [[0, 1], [0, 2], [0, 3]]
# TODO HOW DOES THIS DIFFER FROM def prepare_csv_data_for_chart in statistics_csv_util?
# TODO ROBY
def prepare_data_to_be_plotted_inExcel(inputFilename, columns_to_be_plotted, chart_type_list,
                               count_var=0, column_yAxis_field_list = []):
    # TODO change to pandas half of this function relies on csv half on pandas, reading in data twice!
    # TODO temporary to measure process time
    # startTime=IO_user_interface_util.timed_alert(GUI_util.window,2000,'Analysis start', 'Started running Excel prepare_data_to_be_plotted_inExcel at',
    #                                              True, '', True, '', True)
    withHeader_var = IO_csv_util.csvFile_has_header(inputFilename) # check if the file has header
    data, headers = IO_csv_util.get_csv_data(inputFilename,withHeader_var) # get the data and header
    if len(data)==0:
        return None
    headers=list(headers)
    count_msg, withHeader_msg = build_timed_alert_message(chart_type_list[0],withHeader_var,count_var)
    if count_var == 1:
        dataRange = get_dataRange(columns_to_be_plotted, data)
        # TODO hover_over_values not being passed, neither are any potential aggregate columns
        #   get_data_to_be_plotted_with_counts is less general than
        data_to_be_plotted = get_data_to_be_plotted_with_counts(inputFilename,withHeader_var,headers,columns_to_be_plotted,column_yAxis_field_list,dataRange)
    else:
        try:
            data = pd.read_csv(inputFilename,encoding='utf-8',on_bad_lines='skip')
        except:
            try:
                data = pd.read_csv(inputFilename,encoding='ISO-8859-1', on_bad_lines='skip')
                IO_user_interface_util.timed_alert(GUI_util.window, 2000, 'Warning',
                                                   'Excel-util encountered errors with utf-8 encoding and switched to ISO-8859-1 in reading into pandas the csv file ' + inputFilename)
                print("Excel-util encountered errors with utf-8 encoding and switched to ISO-8859-1 encoding in reading into pandas the csv file " + inputFilename)
            except ValueError as err:
                if 'codec' in str(err):
                    err=str(err) + '\n\nExcel-util encountered errors with both utf-8 and ISO-8859-1 encoding in the function \'prepare_data_to_be_plotted_inExcel\' while reading into pandas the csv file\n\n' + inputFilename + '\n\nPlease, check carefully the data in the csv file; it may contain filenames with non-utf-8/ISO-8859-1 characters; less likely, the data in the txt files that generated the csv file may also contain non-compliant characters. Run the utf-8 compliance algorithm and, perhaps, run the cleaning algorithm that converts apostrophes.\n\nNO EXCEL CHART PRODUCED.'
                mb.showwarning(title='Input file read error',
                       message=str(err))
                return
        data_to_be_plotted = get_data_to_be_plotted_NO_counts(inputFilename,withHeader_var,headers,columns_to_be_plotted,data)
    # TODO temporary to measure process time
    # IO_user_interface_util.timed_alert(GUI_util.window,2000,'Analysis end', 'Finished running Excel prepare_data_to_be_plotted_inExcel at',
    #                                    True, '', True, startTime, True)
    return data_to_be_plotted


# bar chart aggregated by group  -----------------------------------------------------------------
#         plotList = ['Frequency']
# plot the words contained in each groupBy field values (e.g, the word 'Rome' in POS tag PPN)
# must first run compute_csv_column_frequencies_with_aggregation
# columns_to_be_plotted_yAxis=['Form']
def visualize_chart_byGroup(inputFilename, outputDir, createCharts, chartPackage, filesToOpen,
                            columns_to_be_plotted_byGroup, groupByList,
                            chart_title, columns_to_be_plotted_xAxis, columns_to_be_plotted_yAxis):

    pivot=False
    filesToOpen=[]

    # the function compute_csv_column_frequencies produces plots
    outputFiles = statistics_csv_util.compute_csv_column_frequencies(GUI_util.window,
                                                  inputFilename, None, outputDir, False,
                                                  createCharts, chartPackage,
                                                  # selected_col=columns_to_be_plotted_numeric,
                                                  selected_col=columns_to_be_plotted_yAxis,
                                                  hover_col=[],
                                                  group_col=groupByList,
                                                  complete_sid=False,
                                                  chart_title=chart_title,
                                                  fileNameType=
                                                  columns_to_be_plotted_yAxis[0],
                                                  chartType='',
                                                  pivot=pivot)
    if outputFiles!=None:
        if isinstance(outputFiles, str):
            filesToOpen.append(outputFiles)
        else:
            filesToOpen.extend(outputFiles)

    # new_inputFilename = chart_outputFilename[0]

    # temp_outputFilename[0] is the frequency filename (with no hyperlinks)
    # count_var = 0
    # remove_hyperlinks = False  # already removed in compute frequencies
    # headers = IO_csv_util.get_csvfile_headers_pandas(new_inputFilename)

    # 0 is the groupBy field with no-hyperlinks (e.g., NER)
    # 1 is the column plotted (e.g., Form)
    # 2 is the Document ID
    # 3 is the Document
    # 4 is Frequency
    # sel_column_name = IO_csv_util.get_headerValue_from_columnNumber(headers, 1)
    columns_to_be_plotted_byGroup = [[2, 0, 3]]  # will give different bars for each value
    # columns_to_be_plotted_byGroup = [[1, 4, 0, 2, 3]] # will give different bars for each value
    # outputFileLabel='by_' + str(groupByList[0])
    # chart_title='Frequency Distribution of ' + str(columns_to_be_plotted_yAxis[0]) + ' by ' + str(groupByList[0])
    # hover_label=[]
    column_yAxis_label = 'Frequencies'
    # if chartPackage == "Excel":
    #     column_name = IO_csv_util.get_headerValue_from_columnNumber(headers, 1)
        # chart is visualized in compute_csv_column_frequencies
        # number_column_entries = len(IO_csv_util.get_csv_field_values(new_inputFilename, column_name))
        # # in visualize_chart_byGroup
        # outputFiles = run_all(columns_to_be_plotted_byGroup, new_inputFilename, outputDir,
        #                                           outputFileLabel=outputFileLabel, # outputFileNameType + 'byDoc', #outputFileLabel,
        #                                           chartPackage=chartPackage,
        #                                           chart_type_list=['bar'],
        #                                           chart_title=chart_title,
        #                                           column_xAxis_label_var='',
        #                                           column_yAxis_label_var=column_yAxis_label,
        #                                           hover_info_column_list=hover_label,
        #                                           # count_var is set in the calling function
        #                                           #     0 for numeric fields;
        #                                           #     1 for non-numeric fields
        #                                           count_var=count_var,
        #                                           remove_hyperlinks=remove_hyperlinks)
        # if outputFiles!=None:
        #     if len(chart_outputFilename) > 0:
        #         filesToOpen.append(chart_outputFilename)
    return filesToOpen

# def visualize_chart_byDoc(inputFilename, outputDir, outputFileNameType, createCharts, chartPackage, filesToOpen,
#                         columns_to_be_plotted_byDoc, columns_to_be_plotted_yAxis,
#                         count_var, pivot, chart_title, hover_label):
#     column_yAxis_label = 'Frequencies'
#     remove_hyperlinks = True
#     # by DOCUMENT counting the qualitative values ---------------------------------------------------------------------------
#     if count_var == 1:  # for alphabetic fields that need to be counted for display in a chart
#         # TODO TONY using this function, the resulting output file is in the wrong format and would need to be pivoted to be used
#         # temp_outputFilename = statistics_csv_util.compute_csv_column_frequencies(inputFilename, ["Document ID",'Document'], ['POS'], outputDir, chart_title, graph=False,
#         #                              complete_sid=False,  chartPackage='Excel')
#
#         # TODO TONY the compute_csv_column_frequencies_with_aggregation should export the distinct values of a column
#         #   in separate columns so that they will be plotted with different colors as separate series
#
#         # in visualize_chart_byDoc
#         temp_outputFilename = statistics_csv_util.compute_csv_column_frequencies(
#             GUI_util.window,
#             inputFilename, None, outputDir,
#             False, createCharts, chartPackage,
#             # selected_col=columns_to_be_plotted_numeric,
#             selected_col=columns_to_be_plotted_yAxis,
#             hover_col=[],
#             chart_title=chart_title + ' by Document',
#             group_col=['Document ID', 'Document'],
#             complete_sid=False,
#             fileNameType=columns_to_be_plotted_yAxis[0], chartType='', pivot=pivot)
#         new_inputFilename = temp_outputFilename[0]
#         # temp_outputFilename[0] is the frequency filename (with no hyperlinks)
#         remove_hyperlinks = False  # already removed in compute frequencies
#         # 2,3 are the Document and Frequency columns in temp_outputFilename
#         # columns_to_be_plotted_byDoc = [[2,3]] # document 2, first item; frequencies 3 second item
#         # columns_to_be_plotted_byDoc = [[1,2],[1,3]]
#         # pivot = True
#
#         headers = IO_csv_util.get_csvfile_headers_pandas(new_inputFilename)
#
#         if pivot == True:
#             columns_to_be_plotted_byDoc_len = len(columns_to_be_plotted_byDoc[0])
#             columns_to_be_plotted_byDoc = []
#             for i in range(columns_to_be_plotted_byDoc_len, len(headers)):
#                 columns_to_be_plotted_byDoc.append([columns_to_be_plotted_byDoc_len - 1, i])
#         else:
#             # 1 is the Document with no-hyperlinks,
#             # 2 is the column plotted (e.g., Gender) in temp_outputFilename
#             # 3 is Frequency,
#             # TODO TONY we should ask the same type of question for columns that are already in quantitative form if we want to compute a single MEAN value
#             sel_column_name = IO_csv_util.get_headerValue_from_columnNumber(headers, 2)
#             # item 1 is the column of Document with no-hyperlinks,
#             # item 2 is the column plotted (e.g., Gender) in temp_outputFilename
#             # item 3 is the column of Frequency,
#             columns_to_be_plotted_byDoc = [[2, 0, 3]]  # will give different bars for each value
#             # TODO temporarily disconnected until we figure out a way to not repeat this questions several times
#             # if chartPackage == "Excel":
#                 # column_name = IO_csv_util.get_headerValue_from_columnNumber(headers, 1)
#                 # number_column_entries = len(
#                 #     IO_csv_util.get_csv_field_values(new_inputFilename, column_name))
#                 # if number_column_entries > 1:
#                 #     answer = tk.messagebox.askyesno("Warning", "For the chart of '" + sel_column_name + "' by document, do you want to:\n\n  (Y) sum the values across all " + str(number_column_entries) + " '" + column_name + "';\n  (N) use all " + str(number_column_entries) + " distinct column values.")
#                 #     if answer:
#                 #         # [[1, 3]] will give one bar for each doc, the sum of all values in selected_column to be plotted
#                 #         columns_to_be_plotted_byDoc = [[1, 3]]
#                 #     else:
#                 #         # [[1, 3, 2]] will give different bars for each value
#                 #         # Document, Field to be plotted (e.g., POS), Sentence ID
#                 #         columns_to_be_plotted_byDoc = [[1, 3, 2]]
#                 # reset the original value to be used in charts by sentence index
#
#     # by DOCUMENT NOT counting; quantitative values ---------------------------------------------------------------------------
#     else:
#         new_inputFilename = inputFilename
#
#     if outputFileNameType != '':
#         outputFileLabel = 'byDoc_' + outputFileNameType
#     else:
#         outputFileLabel = 'byDoc'
#
#     # TODO Tony when plotting bar charts in Plotly with documents in the X-axis we need to remove the path and just keep the tail
#     #   or the display is too messy; it works like that in Excel
#
#     # in visualize_chart_byDoc
#     outputFiles = run_all(columns_to_be_plotted_byDoc, new_inputFilename, outputDir,
#                                    outputFileLabel=outputFileLabel,
#                                    # outputFileNameType + 'byDoc', #outputFileLabel,
#                                    chartPackage=chartPackage,
#                                    chart_type_list=['bar'],
#                                    chart_title=chart_title + ' by Document',
#                                    column_xAxis_label_var='',
#                                    column_yAxis_label_var=column_yAxis_label,
#                                    hover_info_column_list=hover_label,
#                                    # count_var is set in the calling function
#                                    #     0 for numeric fields;
#                                    #     1 for non-numeric fields
#                                    count_var=0,
#                                    remove_hyperlinks=remove_hyperlinks)
#     if outputFiles!=None:
#         if len(chart_outputFilename) > 0:
#             filesToOpen.append(chart_outputFilename)
#     return filesToOpen

def visualize_chart_bySent(inputFilename, outputDir, createCharts, chartPackage, filesToOpen, n_documents,
                              columns_to_be_plotted_byDoc, columns_to_be_plotted_yAxis, count_var, pivot):

    # TODO temporary to measure process time
    startTime = IO_user_interface_util.timed_alert(GUI_util.window, 2000, 'Analysis start',
                                                   'Started running Excel bySent at',
                                                   True, '', True, '', True)
    # inputFilename = data_pivot(inputFilename, 'Sentence ID', 'Yngve score')
    # columns_to_be_plotted_bySent = [[columns_to_be_plotted_bySent[0][0]]]
    if count_var == 1:  # for alphabetic fields that need to be counted for display in a chart
        temp_outputFilename = statistics_csv_util.compute_csv_column_frequencies(
            GUI_util.window,
            inputFilename,
            None, outputDir,
            False,
            createCharts,
            chartPackage,
            selected_col=columns_to_be_plotted_numeric,
            hover_col=[],
            group_col=[['Document ID', 'Document', 'Sentence ID']],
            complete_sid=True,
            fileNameType='CSV',
            chartType='',
            pivot=pivot)
        inputFilename = temp_outputFilename[0]
        if pivot:
            inputFilename = statistics_csv_util.csv_data_pivot(temp_outputFilename[0], 'Sentence ID',
                                                               'Gender', no_hyperlinks=True)
        else:
            # Using the output from statistics_csv_util.compute_csv_column_frequencies
            #   Document, Frequency, Sentence ID, Field to be plotted (e.g., POS)
            # columns_to_be_plotted_bySent = [[1, 4, 2, 3]]
            columns_to_be_plotted_bySent = [[2, 4]]
    else:  # numeric values of field(s) to be plotted
        columns_to_be_plotted_bySent = []
        if n_documents > 1:
            for i in range(0, len(columns_to_be_plotted_numeric)):
                # For multiple series, by document & sentence IDs any combinations of Document, Frequency, Sentence ID, Field to be plotted
                #       does not work
                # Only the following works:
                #   YES [[Document, Column 1 to be plotted], [Document, Column 2 to be plotted], ...]
                # NO [[Document, Column 1 to be plotted, Sentence ID], [Document, Column 2 to be plotted, Sentence ID], ...]
                #   sentence IDs are repeated on X-axis rather than Docs
                # NO [[Document, Sentence ID, Column 1 to be plotted], [Document, Sentence ID, Column 2 to be plotted], ...]
                #   frequencies or scores on X-axis
                # NO [[Document, Column 1 to be plotted, Column 2 to be plotted, Sentence ID]]
                #   only one series plotted with Docs on X-axis
                columns_to_be_plotted_bySent.append([docCol + 1, columns_to_be_plotted_numeric[i][0]])
        else:
            # Sentence ID, Frequency
            columns_to_be_plotted_bySent.append([sentCol, columns_to_be_plotted_numeric[i][0]])

    if n_documents > 1:
        chart_title = chart_title + ' by Document & Sentence Index'
        xAxis_label = ''
    else:
        chart_title = chart_title + ' by Sentence Index'
        xAxis_label = 'Sentence index'

    if outputFileNameType != '':
        outputFileLabel = 'bySent_' + outputFileNameType
    else:
        outputFileLabel = 'bySent'

    outputFiles = run_all(columns_to_be_plotted_bySent, inputFilename, outputDir,
                                   outputFileLabel=outputFileLabel,
                                   chartPackage=chartPackage,
                                   chart_type_list=['line'],
                                   chart_title=chart_title,
                                   column_xAxis_label_var=xAxis_label,
                                   column_yAxis_label_var=column_yAxis_label,
                                   hover_info_column_list=hover_label,
                                   count_var=0,  # always 0 when plotting by sentence index
                                   complete_sid=True,
                                   remove_hyperlinks=True)

    if outputFiles!=None:
        if isinstance(outputFiles, str):
            filesToOpen.append(outputFiles)
        else:
            filesToOpen.extend(outputFiles)

    # TODO temporary to measure process time
    IO_user_interface_util.timed_alert(GUI_util.window, 2000, 'Analysis end',
                                       'Finished running Excel bySent at',
                                       True, '', True, startTime, True)


# TODO columns_to_be_plotted comes in a single list to be exported to run_all as double list
# columns_to_be_plotted, columns_to_be_plotted_bySent, columns_to_be_plotted_byDoc
#   all double lists [[]]
#   BUT they are passed by calling functions as single lists []
#       and converted to double lists for run_all
#       e.g., columns_to_be_plotted_xAxis=[], columns_to_be_plotted_yAxis=['Sentiment score (Median)', 'Arousal score (Median)', 'Dominance score (Median)']
#       e.g., columns_to_be_plotted_xAxis=[], columns_to_be_plotted_yAxis=['Yngve score', 'Frazier score']
#       e.g., columns_to_be_plotted_xAxis=[], columns_to_be_plotted_yAxis=['Yngve score']
# the variable groupByList,plotList, chart_title_label are used to compute column statistics
#   groupByList is typically the list ['Document ID', 'Document']
#   plotList is the list of fields that want to be plotted
#   chart_title_label is used as part of the chart_title when plotting the fields statistics
# X-axis

def visualize_chart(createCharts,chartPackage,inputFilename,outputDir,
                    columns_to_be_plotted_xAxis,columns_to_be_plotted_yAxis,
                    chart_title, count_var, hover_label, outputFileNameType, column_xAxis_label,
                    groupByList, plotList, chart_title_label, column_yAxis_label='Frequencies', pivot = False):
    filesToOpen=[]
    columns_to_be_plotted_numeric=[]
    columns_to_be_plotted_byDoc=[]
    columns_to_be_plotted_bySent=[]

    if createCharts == True:
        chart_outputFilenameSV=''
    else:
        return

        # the run_all always expects a double list with 2 values, e.g., [[0,0], [1,1]
        #   so, when only one field is passed, we add the same field twice
        # TODO
        # columns_to_be_plotted_numeric = [[1, 1], [3, 3]]  # for complexity scores; duplicates columns gives right plot
        # columns_to_be_plotted_numeric = [[1, 3]]  # for complexity scores; duplicates columns gives right plot
        # columns_to_be_plotted_numeric = [[0, 2], [0, 3]]  # for ngrams

# pivot = True will list for every document all the separate values of the selected item to be plotted
#       = False will sum all the individual values
# count_var should always be TRUE to get frequency distributions

    # in the bar charts columns_to_be_plotted, when numeric data are passed,
    #   the first item is the column of numeric values
    #   the second item is the X-axis
    #   see the example of call in get_ngramlist
    # if we
    headers = IO_csv_util.get_csvfile_headers_pandas(inputFilename)
    if len(headers)==0:
        IO_user_interface_util.timed_alert(GUI_util.window, 2000, 'Empty csv file',
                                                       'The file\n\n' + inputFilename + '\n\nis empty. No charts can be produced using this csv file.\n\nPlease, check the file and try again.',
                                                       True, '', True, '', False)
        # mb.showwarning(title='Empty file', message='The file\n\n' + inputFilename + '\n\nis empty. No charts can be produced using this csv file.\n\nPlease, check the file and try again.')
        print('The file\n\n' + inputFilename + '\n\nis empty. No charts can be produced using this csv file.\n\nPlease, check the file and try again.')
        return filesToOpen
    field_number_xAxis = None
    if len(columns_to_be_plotted_xAxis) == 1:
        field_number_xAxis = IO_csv_util.get_columnNumber_from_headerValue(headers, columns_to_be_plotted_xAxis[0],
                                                                          inputFilename)

    # if "Document ID" in headers:
    if "Document" in str(groupByList):
        docCol = IO_csv_util.get_columnNumber_from_headerValue(headers, 'Document', inputFilename)
        # docCol = docCol +1 # we need to visualize the doc filename
        byDoc = True
    else:
        byDoc = False
    if "Sentence ID" in headers:
        sentCol = IO_csv_util.get_columnNumber_from_headerValue(headers, 'Sentence ID', inputFilename)
        bySent = True
    else:
        bySent = False

    # in visualize_chart
    for i in range(0,len(columns_to_be_plotted_yAxis)):
        # get numeric value of header, necessary for run_all
        field_number_yAxis = IO_csv_util.get_columnNumber_from_headerValue(headers, columns_to_be_plotted_yAxis[i], inputFilename)
        if field_number_yAxis==None:
            return filesToOpen

        if len(columns_to_be_plotted_xAxis)==0: # no x-Axis field
            columns_to_be_plotted_numeric.append([field_number_yAxis,field_number_yAxis])
        else: # there is an X-Axis (e.g., ngrams values)
            columns_to_be_plotted_numeric.append([field_number_xAxis, field_number_yAxis])

        if byDoc:
            columns_to_be_plotted_byDoc.append([docCol, field_number_yAxis])
        if bySent:
            columns_to_be_plotted_bySent.append([sentCol, field_number_yAxis])

        # remove first item in list, the X-axis label substituted by doc
        # columns_to_be_plotted_numeric[0].pop(0)
        # columns_to_be_plotted_numeric[0].insert(0, docCol + 1)
        # columns_to_be_plotted_byDoc = columns_to_be_plotted_numeric

        # TODO Naman for numeric data build classes of values, rather than individual values, to be displayed in the X-axis
        # https://stackoverflow.com/questions/49382207/how-to-map-numeric-data-into-categories-bins-in-pandas-dataframe
        # if count_var == 0: # numeric variable
        #     import pandas as pd
        #     df = pd.read_csv(inputFilename)
        #     # column_data =df[columns_to_be_plotted_yAxis[0].tolist()]
        #     column_data =df[columns_to_be_plotted_yAxis[0]].tolist()
        #     print("len(column_data)", len(column_data), "column_data",column_data)
        #     bins = list(set(column_data))
        #     bins.sort()
        #     x_axis_labels = []
        #     # create classes of values
        #     for j in range(1,len(bins)):
        #         # x_axis_labels.append(f"Bin(j)")
        #         x_axis_labels.append("Bin-" + str(j))
        #     print("Bins",pd.cut(column_data, bins, labels=x_axis_labels))

    # when pivoting data
    # columns_to_be_plotted_bySent = []
    # for i in range(1, n_documents):
    #     columns_to_be_plotted_bySent.append([0, i])
    count_var_SV = count_var

    nRecords, nColumns = IO_csv_util.GetNumberOf_Records_Columns_inCSVFile(inputFilename)

    print("\n\n\nRecords in inputfile (in charts_util)",nRecords, '  ', inputFilename)

# standard bar chart ------------------------------------------------------------------------------
    if len(columns_to_be_plotted_numeric[0])>0: # compute only if the double list is not empty
        outputFiles = run_all(columns_to_be_plotted_numeric, inputFilename, outputDir,
                                                  outputFileLabel=outputFileNameType,
                                                  chartPackage=chartPackage,
                                                  chart_type_list=['bar'],
                                                  chart_title=chart_title,
                                                  column_xAxis_label_var=column_xAxis_label,
                                                  column_yAxis_label_var=column_yAxis_label,
                                                  hover_info_column_list=hover_label,
                                                  count_var=count_var) #always 1 to get frequencies of values, except for n-grams where we already pass stats

        if outputFiles!=None:
            chart_outputFilenameSV=outputFiles
            if isinstance(outputFiles, str):
                filesToOpen.append(outputFiles)
            else:
                filesToOpen.extend(outputFiles)
        else:
            # no point continuing to process more charts if an error was encountered and None was returned
            #   typically because of too many rows for Excel to handle, when Excel is used
            return

# by DOCUMENT
    if byDoc:
        # TODO depends on how many documents we have;
        #   no point charting one document since these charts would be the same as no document
        n_documents = IO_csv_util.GetMaxValueInCSVField(inputFilename, 'visualize_charts_util', 'Document ID')
        if n_documents>1:
            column_yAxis_label = 'Frequencies'
            columns_to_be_plotted_byGroup = []
            chart_title = chart_title + ' by Document'
            for header in groupByList:
                groupCol = IO_csv_util.get_columnNumber_from_headerValue(headers, header, inputFilename)
                columns_to_be_plotted_byGroup.append([groupCol, field_number_yAxis])
            # by DOCUMENT
            outputFiles = visualize_chart_byGroup(inputFilename, outputDir,
                                       createCharts, chartPackage,
                                       filesToOpen,
                                       columns_to_be_plotted_byGroup, groupByList,
                                       chart_title,
                                       columns_to_be_plotted_xAxis,
                                       columns_to_be_plotted_yAxis)

            if outputFiles!=None:
                chart_outputFilenameSV = outputFiles
                if isinstance(outputFiles, str):
                    filesToOpen.append(outputFiles)
                else:
                    filesToOpen.extend(outputFiles)

    # bar chart aggregated by group  (e.g., form values by POS tags) -----------------------------------------------------------------
    #   avoid plotting by ['Document ID', 'Document'] as groupBy; done in chart byDoc
    if len(groupByList) > 0 and groupByList != ['Document ID', 'Document']:
        columns_to_be_plotted_byGroup = []
        for header in groupByList:
            groupCol = IO_csv_util.get_columnNumber_from_headerValue(headers, header, inputFilename)
            # [POS, Form]
            columns_to_be_plotted_byGroup.append([groupCol, field_number_yAxis])
        outputFiles = visualize_chart_byGroup(inputFilename, outputDir, createCharts, chartPackage,
                                                       filesToOpen,
                                                       columns_to_be_plotted_byGroup, groupByList, chart_title,
                                                       columns_to_be_plotted_xAxis, columns_to_be_plotted_yAxis)

        if outputFiles!=None:
            chart_outputFilenameSV = outputFiles
            if isinstance(outputFiles, str):
                filesToOpen.append(outputFiles)
            else:
                filesToOpen.extend(outputFiles)

    # line plots by SENTENCE index -----------------------------------------------------------------------
# sentence index value are the first item in the list [[7,2]] i.e. 7
#   plot values are the second item in the list [[7,2]] i.e. 2
    count_var = count_var_SV
    # not all csv output contain the Sentence ID (e.g., line length function)
    # TODO Samir; to test the add_missing_IDs you must change bySent=False to bySent=True
    bySent = False
    if bySent:
        fileToOpen=visualize_chart_bySent(inputFilename, outputDir, createCharts, chartPackage, filesToOpen, n_documents, columns_to_be_plotted_byDoc, columns_to_be_plotted_yAxis, count_var, pivot)

# compute field STATISTICS (mean, median, skeweness, kurtosis...)--------------------------------------------------------------
    # TODO THE FIELD MUST CONTAIN NUMERIC VALUES
    # plotList (a list []) contains the columns headers to be used to compute their stats
    if len(groupByList) > 0 and not isinstance(outputFiles, str):  # compute only if list is not empty
        if count_var == 1:
            temp_inputFilename = outputFiles[0]
        else:
            temp_inputFilename = inputFilename
        if plotList == ['Frequency']:
            plotList = ['Frequency_' + str(columns_to_be_plotted_yAxis[0])]
        outputFiles = statistics_csv_util.compute_csv_column_statistics(GUI_util.window, temp_inputFilename,
                                                   outputDir,
                                                   outputFileNameType, groupByList,
                                                   plotList, chart_title_label,
                                                   createCharts,
                                                   chartPackage)

        if outputFiles!=None:
            if isinstance(outputFiles, str):
                filesToOpen.append(outputFiles)
            else:
                filesToOpen.extend(outputFiles)

    return filesToOpen

# best approach when all the columns to be plotted are already in the file
#   otherwise, use statistics_csv_util.compute_csv_column_frequencies
# only one hover-over column per series can be selected
# each series plotted has its own hover-over column
#   if the column is the same (e.g., sentence), this must be repeated as many times as there are series

# columns_to_be_plotted is a double list of 2 items for each list [[0, 1], [0, 2], [0, 3]] where
#   the first number refers to the x-axis value and the second to the y-axis value (i.e., a frequency field)
# when count_var=1 the second number gets counted (non numeric values MUST be counted)
# the complete sid need to be tested as na would be filled with 0
# if you need to aggregate fields displaying results grouped by a specific field (e.g., words by NER tag, NER tag by Document ID),
#   you need to run first statistics_csv_util.compute_csv_column_frequencies_with_aggregationgroupBy and then run_all
#   Examples of this can be found in parsers_annotators_visualization in parsers_annotators_visualization
#   and in visualize_chart in charts_util
def run_all(columns_to_be_plotted,inputFilename, outputDir, outputFileLabel,
            chartPackage, chart_type_list,chart_title, column_xAxis_label_var,
            hover_info_column_list=[],
            count_var=0,
            column_yAxis_label_var='Frequencies',
            column_yAxis_field_list = [],
            reverse_column_position_for_series_label=False,
            series_label_list=[], second_y_var=0,second_yAxis_label='',
            complete_sid = False, remove_hyperlinks=False):

    use_plotly = 'plotly' in chartPackage.lower()
    # added by Tony, May 2022 for complete sentence index
    # the file should have a column named Sentence ID
    # the extra parameter "complete_sid" is set to True by default to avoid extra code mortification elsewhere
    if complete_sid:
        # TODO Samir
        inputFilename = add_missing_IDs(inputFilename, inputFilename)
        # complete_sentence_index(inputFilename)
    if use_plotly:
        if 'static' in chartPackage.lower():
            static_flag=True
        else:
            static_flag = False
        # TODO Tony when plotting bar charts with documents in the X-axis we need to remove the path and just keep the tail
        #   or the display is too messy; it works well with Excel
        Plotly_outputFilename = charts_plotly_util.create_plotly_chart(inputFilename = inputFilename,
                                                                        outputDir = outputDir,
                                                                        chart_title = chart_title,
                                                                        chart_type_list = chart_type_list,
                                                                        cols_to_plot = columns_to_be_plotted,
                                                                        column_xAxis_label = column_xAxis_label_var,
                                                                        column_yAxis_label = column_yAxis_label_var,
                                                                        remove_hyperlinks = remove_hyperlinks,
                                                                        static_flag = static_flag)
        return Plotly_outputFilename
    data_to_be_plotted = prepare_data_to_be_plotted_inExcel(inputFilename,
                                columns_to_be_plotted,
                                chart_type_list,count_var,
                                column_yAxis_field_list)
    if data_to_be_plotted==None:
            return

    transform_list = []
    # the following is deciding which type of data is returned from prepare_data_to_be_plotted_inExcel
    # for the function prepare_data_to_be_plotted_inExcel branch into two different data handling functions which retruns different data type
    # and due to complexity reasons, we keep them in this way:
    # check the data type for the return value and decide which step to take next
    if not(isinstance(data_to_be_plotted[0], list)):
        for df in data_to_be_plotted:
            header = list(df.columns)
            data = df.values.tolist()
            data.insert(0,header)
            transform_list.append(data)
            data_to_be_plotted=transform_list
    if data_to_be_plotted==None:
            return
    else:
        # the lines below handle specifically the "Form-Lemma" annotator because "form-lemma" is not processed in statistics_csv_util.py
        withHeader_var = IO_csv_util.csvFile_has_header(inputFilename)  # check if the file has header
        data, headers = IO_csv_util.get_csv_data(inputFilename, withHeader_var)  # get the data and header
        def double_level_grouping_and_frequency(data, selected_col, group_col):
            # Calculate the counts for each column
            group_col_count = data[group_col[0]].value_counts().reset_index()
            group_col_count.columns = [group_col[0], f'Frequency_{group_col[0]}']

            selected_col_count = data.groupby(group_col)[selected_col[0]].value_counts().reset_index(
                name=f'Frequency_{selected_col[0]}')

            # Merge the counts back into the original dataframe
            data_final = pd.merge(group_col_count, selected_col_count, how='inner', on=group_col[0])

            data_final = data_final.drop_duplicates()  # Remove potential duplicate rows

            # Convert DataFrame into list of lists
            data_list = data_final.values.tolist()

            # Extract 2nd and 3rd column into one list of lists and 4th and 5th into another
            list_1 = [[row[2], row[3]] for row in data_list]
            list_2 = [[row[0], row[1]] for row in data_list]
            list_1.insert(0, ['Form values', 'Frequencies of Form'])
            list_2.insert(0, ['Lemma values', 'Frequencies of Lemma'])
            return [list_1, list_2]
        if len(data_to_be_plotted)==2 and data_to_be_plotted[0][0]==['Form values','Frequencies of Form'] and data_to_be_plotted[1][0]==['Lemma values','Frequencies of Lemma']:
            data = pd.DataFrame(data, columns=headers)
            data_to_be_plotted=double_level_grouping_and_frequency(data,['Form'],['Lemma'])
        chart_title = chart_title
        outputFiles = charts_Excel_util.create_excel_chart(GUI_util.window, data_to_be_plotted,
                                                  inputFilename, outputDir,
                                                  outputFileLabel, chart_title, chart_type_list,
                                                  column_xAxis_label_var, column_yAxis_label_var,
                                                  hover_info_column_list,
                                                  reverse_column_position_for_series_label,
                                                  series_label_list, second_y_var, second_yAxis_label)

    return outputFiles

def build_timed_alert_message(chart_type,withHeader_var,count_var):
    if withHeader_var==1:
        withHeader_msg='WITH HEADERS'
    else:
        withHeader_msg='WITHOUT HEADERS'
    if count_var==1:
        count_msg='WITH COUNTS'
    else:
        count_msg='WITHOUT COUNTS'
    return withHeader_msg, count_msg


# split the pairs of gui x y values into two separate lists of x axis values and y axis value
def get_xaxis_yaxis_values(columns_to_be_plotted):
    x = [a[0] for a in columns_to_be_plotted] # select all the x axis number and put them in a list
    y = [a[1] for a in columns_to_be_plotted] # select all the y axis number and put them in a list
    x1 = [ int(b) for b in x ]  # convert them into int type
    y1 = [ int(b) for b in y]  # convert them into int type
    return x1, y1

def get_dataRange(columns_to_be_plotted, data):
    dataRange = []
    for i in range(len(columns_to_be_plotted)):
        for row in data:
            try:
                rowValues = list(row[w] for w in columns_to_be_plotted[i])
                dataRange.append(rowValues)
            except IndexError:
                continue
    dataRange = [ dataRange [i:i + len(data)] for i in range(0, len(dataRange), len(data)) ]
    return dataRange

# TODO if hover_over columns are passed, it should concatenate all values, instead of displaying the first one only
#   (e.g. an example run the going UP function in WordNet)
# this function seems to be less general than def compute_csv_column_frequencies; that function handl;es aggregation and hover over effects
# we should consolidate the two and use the most general one under the heading get_data_to_be_plotted_with_counts

# def get_data_to_be_plotted_with_counts(inputFileName,withHeader_var,headers,columns_to_be_plotted,column_yAxis_field_list,dataRange):
#     CALL compute_column_frequencies(columns_to_be_plotted, dataRange, headers,column_yAxis_field_list)
#
#     CALLED compute_column_frequencies(columns_to_be_plotted, data_list, headers,specific_column_value_list=[]):


# -----------------------------------------------------------------
# MUST COMPUTE HOVER OVER VALUES!!! see below

# create a list of unique words to be displayed in hover over
# result = IO_files_util.openCSVFile(outputFilenameCSV1, 'r', 'utf-8')
# DataCaptured = csv.reader(result)
# words = set()
# for row in DataCaptured:
#     words.add(row[0])
# also IO_csv_util.get_csv_field_values(inputfile_name, column_name)


def get_data_to_be_plotted_with_counts(inputFilename,withHeader_var,headers,columns_to_be_plotted,
                                       specific_column_value_list,data_list):
    data_to_be_plotted=[]
    # data_to_be_plotted = compute_column_frequencies_4Excel(columns_to_be_plotted, dataRange, headers, column_yAxis_field_list)

    column_list=[]
    column_frequencies=[]
    column_stats=[]
    specific_column_value=''
    complete_column_frequencies=[]
    if len(data_list) != 0:
        for k in range(len(columns_to_be_plotted)):
            res=[]
            if len(specific_column_value_list)>0:
                specific_column_value=specific_column_value_list[k]
            #get all the values in the selected column
            try:
                #  TODO the datalist is like [['NN','NN'], ...] so the code produces bad results
                #       when multiple series side-by-side (e.g., form and lemma values) need to be plotted
                column_list = [i[1] for i in data_list[k]]
            except IndexError:
                continue
            counts = Counter(column_list).most_common()
            if len(headers) > 0:
                id_name_num = columns_to_be_plotted[k][0]
                id_name = headers[id_name_num]
                column_name_num = columns_to_be_plotted[k][1]
                column_name = headers[column_name_num]
                if len(specific_column_value_list)==0:
                    column_frequencies = [[column_name + " values", "Frequencies of " + column_name]]
                else:
                    for y in range(len(specific_column_value_list)):
                        column_frequencies = [[id_name, "Frequencies of " + str(specific_column_value) + " in Column " + str(column_name)]]
            else:
                id_name_num = columns_to_be_plotted[k][0]
                id_name = "column_" + str(id_name_num+1)
                column_name_num = columns_to_be_plotted[k][1]
                column_name = "column_" + str(column_name_num+1)
                if len(specific_column_value)==0:
                    column_frequencies = [[column_name + " values", "Frequencies of " + column_name]]
                else:
                    for y in range(len(specific_column_value_list)):
                        column_frequencies = [[id_name, "Frequencies of " + str(specific_column_value) + " in Column_" + str(column_name_num+1)]]
            if len(specific_column_value) == 0:
                for value, count in counts:
                    column_frequencies.append([value, count])
            else:
                for i in range(len(column_list)):
                    if column_list[i] == specific_column_value:
                        res.append(1)
                    else:
                        res.append(0)
                for j in range(len(data_list[k])):
                    column_frequencies.append([data_list[k][j][0], res[j]])
            data_to_be_plotted.append(column_frequencies)

    return data_to_be_plotted

# [[0,2]], [0], [2]
def get_data_to_be_plotted_NO_counts(inputFilename,withHeader_var,headers,columns_to_be_plotted,data):
    data_to_be_plotted=[]
    for gp in columns_to_be_plotted:
        data.iloc[:, gp[1]].replace('N/A', 0)
        # data.iloc[:, gp[1]].astype('float')
        tempData=data.iloc[:,gp]
        data_to_be_plotted.append(data.iloc[:,gp])
    return data_to_be_plotted

def header_check(inputFile):
    sentenceID_pos=''
    docCol_pos=''
    docName_pos=''
    frequency_pos = []

    if isinstance(inputFile, pd.DataFrame):
        header = list(inputFile.columns)
    else:
        header = IO_csv_util.get_csvfile_headers(inputFile)
    if 'Sentence ID' in header:
        sentenceID_pos = header.index('Sentence ID')
    else:
        pass

    if 'Document ID' in header:
        docCol_pos = header.index('Document ID')
    else:
        pass

    if 'Document' in header:
        docName_pos = header.index('Document')
    else:
        pass

    # Frequenc to capture Frequency and Frequencies
    # str added since the header may contain several instances of the searched item (e.g., Mean score, Median score)
    #   in which case it would not be found
    str_header=str(', '.join(header))
    if 'Frequenc' in str_header or 'Number of' in str_header or 'score' in str_header or 'Score' in str_header:
        # the code would break with the wrong header item (e.g., no Frequency in header to get the index
        # We do 2 things here:
        #   1. get the right header value (e.g., Number of words, or Score, instead of Frequency)
        #   2. Loop through the header containing a specific value (e.g., score) and get all its positions (e.g., Mean score, Median score)
        #   frequency_pos needs to be a list [] rather than a string to accommodate for multiple instances
        # https://stackoverflow.com/questions/64127075/how-to-retrieve-partial-matches-from-a-list-of-strings
            result = list(filter(lambda x: 'Frequenc' in x or 'Number of' in x or 'Score' in x or 'score' in x, header))
            try:
                for i in range(0,len(result)):
                    frequency_pos.append(header.index(result[i]))
            except:
                pass
    else:
        pass
    return sentenceID_pos, docCol_pos, docName_pos, frequency_pos, header

# TODO Samir very slow
def process_sentenceID_record(Row_list, Row_list_new, index,
                              start_sentence, end_sentence,
                              header, sentenceID_pos, docCol_pos, docName_pos, frequency_pos,
                              save_current):
    # TODO temporary to measure process time
    startTime=IO_user_interface_util.timed_alert(GUI_util.window,2000,'Analysis start', 'Started running Excel process_sentenceID_record at',
                                                 True, '', True, '', True)
    # range(start, stop, step)
    # end_sentence is always skipped; the range of integers end at end_sentence – 1
    for i in range(start_sentence, end_sentence, 1):
        temp = [''] * len(header)
        # loop through headers for Sentence ID, Document ID, and Document to insert missing values
        for j in range(len(header)):
            if j == sentenceID_pos:
                # insert Sentence ID
                temp[j] = i
                # when adding a new Sentence ID, insert a frequency value of 0,
                #   in every occurrence of a frequency column, whatever the name may be (Frequency, Frequencies, Number of, Score)
                for k in range (0,len(frequency_pos)):
                    if frequency_pos[k]!='':
                        temp[frequency_pos[i]] = 0
            elif j == docCol_pos:
                # insert Document ID
                temp[j] = Row_list[index][docCol_pos]
            elif j == docName_pos:
                # insert Document
                temp[j] = Row_list[index][docName_pos]
        Row_list_new.append(temp)

    if save_current:
        Row_list_new.append(Row_list[index])
    # TODO temporary to measure process time
    IO_user_interface_util.timed_alert(GUI_util.window,2000,'Analysis end', 'Finished running Excel process_sentenceID_record at',
                                       True, '', True, startTime, True)

    return Row_list_new

# written by Yi Wang
# rewritten by Roberto July 2022

# input can be a csv filename or a dataFrame
# output is a csv file
# TODO Samir very slow
def add_missing_IDs(input, outputFilename):
    from Stanza_functions_util import stanzaPipeLine, sent_tokenize_stanza
    # TODO temporary to measure process time
    startTime=IO_user_interface_util.timed_alert(GUI_util.window,2000,'Analysis start', 'Started running Excel Add missing IDs at',
                                                 True, '', True, '', True)
    if isinstance(input, pd.DataFrame):
        df = input
    else:
        df = pd.read_csv(input, encoding='utf-8', on_bad_lines='skip')
    # define variables
    start_sentence = 1 # first sentence in loop
    end_sentence = 1 # last sentence in loop
    number_sentences = []
    Row_list_new = []
    sentenceID_pos, docCol_pos, docName_pos, frequency_pos, header = header_check(input)
    Row_list = IO_csv_util.df_to_list(df)
    len_Row_list = len(Row_list)
    for index, row in enumerate(Row_list):
        newDoc = False
        if index == 0: # first record
            newDoc = True
        else: # index > 0; all successive records
            if Row_list[index][docCol_pos] - Row_list[index - 1][docCol_pos] > 0:
                newDoc = True

        if newDoc:
            start_sentence = 1
            end_sentence = Row_list[index][sentenceID_pos]
            inputFilename=Row_list[index][docName_pos]
            inputFilename=IO_csv_util.undressFilenameForCSVHyperlink(inputFilename)
            text = (open(inputFilename, "r", encoding="utf-8", errors='ignore').read())
            sentences = sent_tokenize_stanza(stanzaPipeLine(text))
            number_sentences.append([inputFilename,len(sentences)])

            # check whether the last sentence for the previous doc was less than number of sentences
            if index==0: # first record in df
                Row_list_new = process_sentenceID_record(Row_list, Row_list_new, index,
                                                         start_sentence,
                                                         end_sentence,
                                                         header, sentenceID_pos, docCol_pos, docName_pos, frequency_pos,
                                                         save_current=True)
            else: # index>0 all other records
                # select the number of sentences for the right document
                for i in range(len(number_sentences)):
                    # TODO hyperlinks should be removed in file before passing it to add_missing_IDs
                    if IO_csv_util.undressFilenameForCSVHyperlink(Row_list[index-1][docName_pos])==number_sentences[i][0]:
                        n_sentences=number_sentences[i][1]
                if Row_list[index-1][sentenceID_pos]<n_sentences:
                    start_sentence=Row_list[index-1][sentenceID_pos]+1
                    end_sentence = n_sentences+1
                    # pass index-1 as argument since we are adding sentence IDs to the previous document
                    Row_list_new=process_sentenceID_record(Row_list,Row_list_new,index-1,
                                              start_sentence, end_sentence,
                                              header,sentenceID_pos, docCol_pos, docName_pos, frequency_pos,
                                              save_current=False)
                    # do NOT save current; already saved when first processing the record
                # now process the current record
                start_sentence = 1
                end_sentence = Row_list[index][sentenceID_pos]
                Row_list_new = process_sentenceID_record(Row_list, Row_list_new, index,
                                                         start_sentence,
                                                         end_sentence,
                                                         header, sentenceID_pos, docCol_pos, docName_pos, frequency_pos,
                                                         save_current=True)
        else: # same document
            # check that current sentence is not just one sentence greater than previous one
            #   in which case start and end are the same
            if Row_list[index][sentenceID_pos] == Row_list[index - 1][sentenceID_pos] +1:
                start_sentence = Row_list[index][sentenceID_pos]
                end_sentence = Row_list[index][sentenceID_pos]
            else:
                start_sentence = Row_list[index-1][sentenceID_pos]
                end_sentence = Row_list[index][sentenceID_pos]
            Row_list_new = process_sentenceID_record(Row_list, Row_list_new, index,
                                                     start_sentence, end_sentence,
                                                     header, sentenceID_pos, docCol_pos, docName_pos, frequency_pos,
                                                     save_current=True)

    df = pd.DataFrame(Row_list_new,columns=header)
    df.sort_values(by=['Document ID', 'Sentence ID'], ascending=True, inplace=True)
    df.to_csv(outputFilename, encoding='utf-8', index = False)
    # TODO temporary to measure process time
    IO_user_interface_util.timed_alert(GUI_util.window,2000,'Analysis end', 'Finished running Excel Add missing IDs at',
                                       True, '', True, startTime, True)
    return outputFilename


# Tony Chen Gu written at April 2022 mortified at May 2022
# edited by Roberto June 2022 for sorting df
# function no longer used since it does not insert sentences in the right document
# use instead add_missing_IDs

def complete_sentence_index(file_path):
    data = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip')
    if not 'Sentence ID' in data:
        head, tail = os.path.split(file_path)
        IO_user_interface_util.timed_alert(GUI_util.window, 2000, 'Wrong csv file',
                                                       'The csv file\n' + tail + '\n does not contain a "Sentence ID" header. A sentence ID value cannot be added.',
                                                       True, '', True, '', False)
        return
    if(len(data) == 1):
        return data
    max_sid = max(data["Sentence ID"])+1
    sid_list = list(range(1, max_sid))
    df_sid = pd.DataFrame (sid_list, columns = ['Sentence ID'])
    # use merge to accelerate the process
    data = data.merge(right = df_sid, how = "right", on = "Sentence ID")
    data = data.fillna(0)
    # headers=IO_csv_util.get_csvfile_headers_pandas(file_path)
    data.sort_values(by=['Document ID','Sentence ID'], ascending=True, inplace=True)
    data.to_csv(file_path, encoding='utf-8', index = False)
    return

#data_to_be_plotted contains the values to be plotted
#   the variable has this format:
#   this includes both headers AND data
#   one series: [[['Name1','Frequency'], ['A', 7]]]
#   two series: [[['Name1','Frequency'], ['A', 7]], [['Name2','Frequency'], ['B', 4]]]
#   three series: [[['Name1','Frequency'], ['A', 7]], [['Name2','Frequency'], ['B', 4]], [['Name3','Frequency'], ['C', 9]]]
#   more series: ..........
#chart_title is the name of the sheet
#num_label number of bars, for instance, that will be displayed in a bar chart
#second_y_var is a boolean that tells the function whether a second y axis is needed
#   because it has a different scale and plotted values would otherwise be "masked"
#   ONLY 2 y-axes in a single chart are allowed by openpyxl
#chart_type_list is in form ['line', 'line','bar']... one for each of n series plotted
#when called from scripts other than Excel_charts, the list can be of length 1 although more series may be plotted
#   in which case values are filled below
#output_file_name MUST be of xlsx type, rather tan csv

# when NO hover-over data are displayed the Excel filename extension MUST be xlsx and NOT xlsm (becauuse no macro VBA is enabled in this case)

# def df_to_list_w_header(df):
#     res = []
#     header = list(df.columns)
#     res.append(header)
#     for index, row in df.iterrows():
#         temp = [row[tag] for tag in header]
#         res.append(temp)
#     return res
#
#
# def df_to_list(df):
#     res = []
#     header = list(df.columns)
#     for index, row in df.iterrows():
#         temp = [row[tag] for tag in header]
#         res.append(temp)
#     return res
#
#
# def list_to_df(tag_list):
#     header = tag_list[0]
#     df = pd.DataFrame(tag_list[1:], columns=header)
#     return df
#
#
# def header_check(inputFile):
#     sentenceID_pos=''
#     docCol_pos=''
#     docName_pos=''
#
#     if isinstance(inputFile, pd.DataFrame):
#         header = list(inputFile.columns)
#     else:
#         header = IO_csv_util.get_csvfile_headers(inputFile)
#     if 'Sentence ID' in header:
#         sentenceID_pos = header.index('Sentence ID')
#     else:
#         pass
#
#     if 'Document ID' in header:
#         docCol_pos = header.index('Document ID')
#     else:
#         pass
#
#     if 'Document' in header:
#         docName_pos = header.index('Document')
#     else:
#         pass
#     return sentenceID_pos, docCol_pos, docName_pos, header
#


#Returns a grid of barcharts for each algorithm.
#Algorithms are horizontally organized based on the order on which they are inputted
#datalist is list of algorithms
#var is variable of choice
#ntopchoices is the n max values
def multiple_barchart(datalist,outputFilename,var,ntopchoices):
    tempdatalist=[]
    for i in datalist:
        tempdatalist.append(pd.read_csv(i))
    newDatalist=[]
    for i in tempdatalist:
        newDatalist.append(pd.DataFrame(i[var].value_counts()).reset_index().rename(columns={'index':var,var:'Frequency'}).head(ntopchoices))
    fig=make_subplots(rows=2,cols=int(len(datalist)/2)+len(datalist)%2)
    cols=1
    for i in range(0,len(newDatalist)):
        if i<int(len(datalist)/2)+len(datalist)%2:
            fig.add_trace(go.Bar(x=newDatalist[i][var],y=newDatalist[i]['Frequency'],name='Algorithm '+str(i+1)),row=1,col=cols)
            cols=cols+1
    cols=1
    for i in range(0,len(newDatalist)):
        if i>=int(len(datalist)/2)+len(datalist)%2:
            fig.add_trace(go.Bar(x=newDatalist[i][var],y=newDatalist[i]['Frequency'],name='Algorithm '+str(i+1)),row=2,col=cols)
            cols=cols+1
    fig.write_html(outputFilename)
    return outputFilename


#var is the variable of choice to apply the boxplot on
#bycategory is a boolean that chooses whether we want to split it by category along a categorical variable, determined by the following category argument
#points is the choice to represent all points of data, the outliers, or none of them, it should be given through a dropdown menu
#color is another choice of categorical variable to split the data along
def boxplot(data,outputFilename,var,points,bycategory=None,category=None,color=None):
    if points=='All points':
        points='all'
    elif points=='no points':
        points = False
    elif points=='outliers only':
        points = 'outliers'
    if color=='':
        color = None

    if type(data)==str:
        data=pd.read_csv(data)
    if bycategory==False:
        fig=px.box(data,y=var,points=points)
    else:
        fig=px.box(data,x=category,y=var,points=points,color=color)
    fig.write_html(outputFilename)
    return outputFilename


#var1 is the first categorical variable, lengthvar1 is the amount of var 1: should take values of 5 or 10
#var2 is the second categorical variable, lengthvar2 is the amount of var 2: should take values of 5,10 or 20
#var3 is the third categorical variable, lengthvar3 is the amount of var 3: should take values of 5,10, 20 or 30
#All these recommendations are for performance
#three_way_Sankey is a boolean variable that dictates whether the returned Sankey is 2way or 3way. True for 3 variables, false for 2 variables
def Sankey(data,outputFilename,var1,lengthvar1,var2,lengthvar2,three_way_Sankey,var3=None,lengthvar3=None):
    if type(data)==str:
        data=pd.read_csv(data)
    if type(data[var1][0])!=str and type(data[var2][0])!=str:
        mb.showwarning("Warning",
                   "The csv file field(s) selected should be categorical.\n\nYou should select categorical field(s), rather than continuous numeric field(s), and try again.")

    if three_way_Sankey==False:

        data[var1]=data[var1].str.lower()
        tempframe=pd.DataFrame(data[var1].value_counts().head(lengthvar1)).reset_index()
        finalframe=data[data[var1].isin(list(set(tempframe['index'])))]
        tempframe2=pd.DataFrame(finalframe[var2]).value_counts().head(lengthvar2).reset_index()
        finalframe=finalframe[finalframe[var2].isin(list(set(tempframe2[var2])))]
        finalframe=finalframe.reset_index(drop=True)
        sourcelist=list(range(0,len(set(finalframe[var1]))))
        source=[item for item in sourcelist for _ in range(len(set(finalframe[var2])))]

        target1=list(range(0,len(set(finalframe[var2]))))
        target2 = [x+len(set(finalframe[var1])) for x in target1]
        target=target2*len(set(finalframe[var1]))

        valuevector=[]
        for i in sorted(list(set(finalframe[var1]))):
            tempdata=pd.DataFrame(finalframe[finalframe[var1]==i][var2].value_counts()).reset_index().rename(columns={'index':var2,var2:'Frequency'})
            for j in sorted(list(set(tempdata[var2]))):
                if j not in list(tempdata[var2]):
                    valuevector.append(0)
                else:
                    valuevector.append(list(tempdata[tempdata[var2]==j]['Frequency'])[0])

        labelvector=sorted(list(set(finalframe[var1])))+sorted(list(set(finalframe[var2])))

    else:
        data[var1]=data[var1].str.lower()
        tempframe=pd.DataFrame(data[var1].value_counts().head(lengthvar1)).reset_index()
        finalframe=data[data[var1].isin(list(set(tempframe['index'])))]
        tempframe2=pd.DataFrame(finalframe[var2]).value_counts().head(lengthvar2).reset_index()
        finalframe=finalframe[finalframe[var2].isin(list(set(tempframe2[var2])))]
        finalframe=finalframe.reset_index(drop=True)
        source1=list(range(0,len(set(finalframe[var1]))+len(set(finalframe[var2]))))
        source=[item for item in source1 for _ in range(len(set(finalframe[var2])))]
        target1=list(range(0,len(set(finalframe[var2]))))
        target2=[x+len(set(finalframe[var1])) for x in target1]
        target=target2*len(source1)
        labelvector=sorted(set(finalframe[var1]))+sorted(set(finalframe[var2]))
        valuevector=[]
        for i in sorted(list(set(finalframe[var1]))):
            tempvec=[]
            tempframe=finalframe[finalframe[var1]==i]
            wantedframe=pd.DataFrame(tempframe[var2].value_counts()).reset_index().rename(columns={'index':var2,var2:'Frequency'})
            for j in sorted(list(set(finalframe[var2]))):
                if j not in list(wantedframe[var2]):
                    tempvec.append(0)
                else:
                    tempvec.append(list(wantedframe[wantedframe[var2]==j]['Frequency'])[0])
            tempvec=tempvec+list(np.repeat(0,len(target2)-len(tempvec)))
            valuevector=valuevector+tempvec
        for i in sorted(list(set(finalframe[var2]))):
            tempvec=[]
            tempframe=finalframe[finalframe[var2]==i]
            wantedframe=pd.DataFrame(tempframe[var2].value_counts()).reset_index().rename(columns={'index':var2,var2:'Frequency'})
            tempvec=list(np.repeat(0,len(set(finalframe[var2]))))
            for j in sorted(list(set(finalframe[var2]))):
                if j not in list(wantedframe[var2]):
                    tempvec.append(0)
                else:
                    tempvec.append(list(wantedframe[wantedframe[var2] == j]['Frequency'])[0])
            valuevector=valuevector+tempvec
    fig=go.Figure(go.Sankey(link=dict(source=source,target=target,value=valuevector),node=dict(label=labelvector,pad=35,thickness=10)))
    fig.write_html(outputFilename)

    return outputFilename

# created by Samir Kaddoura, November 2022


# Function creates a new column that identifies the documents based on a specific interest variable
# two inputs taken: data is the dataset in question, interest is a vector that the user will have to define, as it changes depending on the corpus
def separator(data,interest):

    interestvector=[]#empty interest vector
    id_list=[] #empty id list in which we record every entry in the dataset that contains one of the interest inputs

    for i in range(0,len(data)): #check every entry in dataset
        for j in range(0,len(interest)): #check every interest vector
            if re.search('.*'+interest[j]+'[^.]',data['Document'][i]):#if the name of the document contains a word of intersest, we append that word to a vector
                interestvector.append(interest[j])
                id_list.append(i)#append the index of the row that contains the interest value

    finaldata=data.loc[id_list,:] #filter dataset by row with interest values
    finaldata['interest']=interestvector #add interest column

    return finaldata


#Returns sunburst piechart. Input a dataframe provided by the NLP suite as data, interest is a vector including interest separation based on separator (as defined above)
#label is a categorical variable we're interested in
#first_sentences is the n first sentences
#last_sentences is the n last sentences
#half_text is a boolean defining whether to split the text in half or not
#beginning_and_end is a boolean that dictates if its a two-level or three level sunburster
def Sunburster(data, outputFilename, outputDir, case_sensitive, interest, label,beginning_and_end=False,first_sentences=None,last_sentences=None,half_text=None):
    if type(data)==str:
        data=pd.read_csv(data)
    if type(data[label])!=str:
        mb.showwarning("Warning",
                   "The csv file field selected should be categorical.\n\nYou should select a categorical field, rather than a continuous numeric field, and try again.")

    #the last 3 arguments are optional. If first_sentences is specified and last_sentences is not or vice versa, we return a message stating they must both be specified or absent at the same time
    if (first_sentences==None and last_sentences!=None) or (first_sentences!=None and last_sentences==None):
        return 'both number of first sentences and number of last sentences have to be specified or absent at the same time'
    else: #Otherwise, we run the Sunburster

        tempdata=separator(data,interest) #Create "interest" variable
        if beginning_and_end==False:
            if half_text==True or (first_sentences==None and last_sentences==None): #If half text is true or both number of first sentences and last sentences is absent, we split each text in half and attribute a "beginning" half and "end" half

                ogdata=tempdata[tempdata['Document ID']==1] #take the first document

                ogdata1=ogdata[ogdata['Sentence ID']<=len(ogdata)/2] #split the document by first half
                oglist1=list(np.repeat('Beginning',len(ogdata1)))
                ogdata1['Beginning or End']=oglist1 #add list "Beginning" the length of the first half

                ogdata2=ogdata[ogdata['Sentence ID']>len(ogdata)/2] #split the document by first half
                oglist2=list(np.repeat('End',len(ogdata2)))
                ogdata2['Beginning or End']=oglist2 #add list "End" the length of the first half

                finaldata=pd.concat([ogdata1,ogdata2]) #merge dataframes

                for i in range(2,max(data['Document ID'])+1): #iterate same process for each document
                    intermediatedata=tempdata[tempdata['Document ID']==i]

                    intermediatedata1=intermediatedata[intermediatedata['Sentence ID']<=len(intermediatedata)/2]
                    intermediatelist1=list(np.repeat('Beginning',len(intermediatedata1)))
                    intermediatedata1['Beginning or End']=intermediatelist1

                    finaldata=pd.concat([finaldata,intermediatedata1])

                    intermediatedata2=intermediatedata[intermediatedata['Sentence ID']>len(intermediatedata)/2]
                    intermediatelist2=list(np.repeat('End',len(intermediatedata2)))
                    intermediatedata2['Beginning or End']=intermediatelist2

                    finaldata=pd.concat([finaldata,intermediatedata2])

                fig=px.sunburst(finaldata,path=['interest','Beginning or End',label]) #return sunburster

                # return plotly.offline.plot(fig)

            else:
                tempdata1=tempdata[tempdata['Sentence ID']<=first_sentences] #all observations with the first n sentences

                list1=list(np.repeat('Beginning',len(tempdata1))) #List repeating 'Beginning'

                for i in range(1,max(data['Document ID'])+1):
                    intermediatedata1=tempdata[tempdata['Document ID']==i]
                    intermediatedata2=intermediatedata1[intermediatedata1['Sentence ID']>(len(intermediatedata1)-last_sentences)]
                    tempdata1=pd.concat([tempdata1,intermediatedata2]).reset_index().drop(columns={'index'}) #all observations with last n sentences

                list2=list(np.repeat('End',len(tempdata1)-len(list1))) #List repeating 'End'
                finallist=list1+list2 #Create a vector defining if the sentence is at the beginning or the end
                finaldata=tempdata1
                finaldata['Beginning or End']=finallist

                fig=px.sunburst(finaldata,path=['interest','Beginning or End',label]) #create sunburst plot
        else:
            fig=px.sunburst(tempdata,path=['interest',label])
        fig.write_html(outputFilename)

        return outputFilename


# Function creates a new column that identifies the documents based on a specific interest variable
#two inputs taken: data is the dataset in question, interest is a vector that the user will have to define, as it changes depending on the corpus
def separator(data,interest):

    interestvector=[]#empty interest vector
    id_list=[] #empty id list in which we record every entry in the dataset that contains one of the interest inputs

    for i in range(0,len(data)): #check every entry in dataset
        for j in range(0,len(interest)): #check every interest vector
            if re.search('.*'+interest[j]+'[^.]',data['Document'][i]):#if the name of the document contains a word of intersest, we append that word to a vector
                interestvector.append(interest[j])
                id_list.append(i)#append the index of the row that contains the interest value

    finaldata=data.loc[id_list] #filter dataset by row with interest values
    finaldata['interest']=interestvector #add interest column

    return finaldata


# This function takes the data, an interest vector defined the same way as in the sunburster function,
#   a variable of choice (should be categorical) var,
#   a boolean variable to dictate if the user wants to observe an additional variable with "extra_dimension_average",
#   the numerical variable of choice average_variable

#The graph shows the frequencies of each group by default depending on the interest vector and the initial variable of choice. If specified, it shows the average of average_variable per group
def treemaper(data,outputFilename,interest,csv_file_field,extra_dimension_average,average_variable=None):
    if type(data)==str:#convert data to dataframe
        data=pd.read_csv(data)
    if type(data[csv_file_field][0])!=str:
        mb.showwarning("Warning",
                   "The csv file field selected should be categorical.\n\nYou should select a categorical field, rather than a continuous numeric field, and try again.")
    if extra_dimension_average and type(data[average_variable][0])!=np.float64:
        mb.showwarning("Warning",
                   "The csv file field selected should be numeric.\n\nYou should select a numeric field, rather than an alphabetic field, and try again.")

    data=separator(data,interest)#use separator function to create interest vector

    if extra_dimension_average==False:#return regular 2 variable graph if false
        fig=px.treemap(data,path=[px.Constant('Total Frequency'),'interest',csv_file_field])
    else:#return graph with extra variable if true
        fig=px.treemap(data,path=[px.Constant('Total Frequency'),'interest',csv_file_field],color=average_variable,color_continuous_scale='RdBu')
    fig.write_html(outputFilename)
    return outputFilename

#choose a data set, a variable to show the evolution through time, outputFilename to save output, monthly and yearly are boolean variables
#If both are passed as false, return daily graph
#if monthly or yearly is passed as true, return monthly or yearly graph respectively
#Both cannot be simultaneously true

# import pandas as pd
# import re
# import numpy as np
# import plotly.express as px

def timechart(data,outputFilename,var,date_format_var,cumulative,monthly=None,yearly=None):
#convert csv to pandas
    if type(data)==str:
        data=pd.read_csv(data)
    date=[]
    year=[]
    month=[]
    day=[]
    if date_format_var=='yyyy':#creates year variable based on yyyy format
        for i in range(0,len(data['Document'])):
            year.append(re.search('\d{4}',data['Document'][i])[0])
            data['year']=year
    elif date_format_var=='mm-yyyy': #creates year and month variable in yyyy-mm format
        for i in range(0,len(data['Document'])):
            date.append(re.search('\d.*\d',data['Document'][i])[0])
        for i in range(0,len(data['Document'])):
            year.append(re.search('\d{4}',date[i])[0])
        for i in range(0,len(data['Document'])):
            month.append(year[i]+'-'+date[i][0:2])
        data['year']=year
        data['month']=month
    elif date_format_var=='yyyy-mm': #creates year and month variable in yyyy-mm format
        for i in range(0,len(data['Document'])):
            date.append(re.search('\d.*\d',data['Document'][i])[0])
        for i in range(0,len(data['Document'])):
            year.append(re.search('\d{4}',date[i])[0])
        for i in range(0,len(data['Document'])):
            month.append(year[i]+'-'+date[i][-2:])
        data['year']=year
        data['month']=month
    elif date_format_var=='dd-mm-yyyy':#creates year,month and day variable in yyyy-mm-dd format
        for i in range(0,len(data['Document'])):
            date.append(re.search('\d.*\d',data['Document'][i])[0])
        for i in range(0,len(data['Document'])):
            year.append(re.search('\d{4}',date[i])[0])
        for i in range(0,en(data['Document'])):
            month.append(year[i]+'-'+date[i][3:5])
        for i in range(0,len(data['Document'])):
            day.append(month[i]+'-'+date[i][0:2])
        data['day']=day
        data['year']=year
        data['month']=month
    elif date_format_var=='mm-dd-yyyy':#creates year,month and day variable in yyyy-mm-dd format
        for i in range(0,len(data['Document'])):
            try:
                date.append(re.search('\d.*\d',data['Document'][i])[0])
            except:
                continue
        for i in range(0,len(data['Document'])):
            try:
                year.append(re.search('\d{4}',date[i])[0])
            except:
                continue
        for i in range(0,len(data['Document'])):
            try:
                month.append(year[i]+'-'+date[i][0:2])
            except:
                continue
        for i in range(0,len(data['Document'])):
            try:
                day.append(month[i]+'-'+date[i][3:5])
            except:
                continue
        data['year']=year
        data['month']=month
        data['day']=day
    elif date_format_var=='yyyy-mm-dd':#creates year,month and day variable in yyyy-mm-dd format
        for i in range(0,len(data['Document'])):
            date.append(re.search('\d.*\d',data['Document'][i])[0])
        for i in range(0,len(data['Document'])):
            year.append(re.search('\d{4}',date[i])[0])
        for i in range(0,len(data['Document'])):
            month.append(year[i]+'-'+date[i][5:7])
        data['year']=year
        data['month']=month
        data['day']=date
    elif date_format_var=='yyyy-dd-mm':#creates year,month and day variable in yyyy-mm-dd format
        for i in range(0,len(data['Document'])):
            date.append(re.search('\d.*\d',data['Document'][i])[0])
        for i in range(0,len(data['Document'])):
            year.append(re.search('\d{4}',date[i])[0])
        for i in range(0,len(data['Document'])):
            month.append(year[i]+'-'+date[i][-2:])
        for i in range(0,len(data['Document'])):
            day.append(month[i]+'-'+date[i][5:7])
        data['year']=year
        data['month']=month
        data['day']=day

#Plot corresponding graph depending on the options
    if cumulative==False:
        if monthly==True and yearly==True:
            return "Choose one of the following: daily graph, monthly graph, yearly graph"
        elif monthly==True:
            data=data.sort_values('month')
            finalframe=pd.DataFrame()
            for i in sorted(set(data['month'])):
                tester=pd.DataFrame(data[data['month']==i][var].value_counts()).reset_index().rename(columns={'index':var,var:'Frequency'})
                for j in set(data[var]):
                    if j not in set(tester[var]):
                        temp=pd.DataFrame([j,0]).T.rename(columns={0:var}).rename(columns={0:var,1:'Frequency'})
                        tester=pd.concat([tester,temp])
                tester=tester.sort_values(var)
                tester
                date=np.repeat(i,len(tester))
                tester['date']=date
                tester=tester.reset_index(drop=True)
                finalframe=pd.concat([finalframe,tester])
                value=[]
                for i in list(set(finalframe[var])):
                    value.append(max(finalframe[finalframe[var]==i]['Frequency']))
            fig=px.bar(finalframe,y=var,x='Frequency',animation_frame='date',orientation='h',range_x=[0,max(value)]).update_yaxes(categoryorder='total ascending')
        elif yearly==True:
            data=data.sort_values('year')
            finalframe=pd.DataFrame()
            for i in sorted(set(data['year'])):
                tester=pd.DataFrame(data[data['year']==i][var].value_counts()).reset_index().rename(columns={'index':var,var:'Frequency'})
                for j in set(data[var]):
                    if j not in set(tester[var]):
                        temp=pd.DataFrame([j,0]).T.rename(columns={0:var}).rename(columns={0:var,1:'Frequency'})
                        tester=pd.concat([tester,temp])
                tester=tester.sort_values(var)
                tester
                date=np.repeat(i,len(tester))
                tester['date']=date
                tester=tester.reset_index(drop=True)
                finalframe=pd.concat([finalframe,tester])
                value=[]
                for i in list(set(finalframe[var])):
                    value.append(max(finalframe[finalframe[var]==i]['Frequency']))
            fig=px.bar(finalframe,y=var,x='Frequency',animation_frame='date',orientation='h',range_x=[0,max(value)]).update_yaxes(categoryorder='total ascending')
        else:
            data=data.sort_values('day')
            finalframe=pd.DataFrame()
            for i in sorted(set(data['day'])):
                tester=pd.DataFrame(data[data['day']==i][var].value_counts()).reset_index().rename(columns={'index':var,var:'Frequency'})
                for j in set(data[var]):
                    if j not in set(tester[var]):
                        temp=pd.DataFrame([j,0]).T.rename(columns={0:var}).rename(columns={0:var,1:'Frequency'})
                        tester=pd.concat([tester,temp])
                tester=tester.sort_values(var)
                tester
                date=np.repeat(i,len(tester))
                tester['date']=date
                tester=tester.reset_index(drop=True)
                finalframe=pd.concat([finalframe,tester])
                value=[]
                for i in list(set(finalframe[var])):
                    value.append(max(finalframe[finalframe[var]==i]['Frequency']))
            fig=px.bar(finalframe,y=var,x='Frequency',animation_frame='date',orientation='h',range_x=[0,max(value)]).update_yaxes(categoryorder='total ascending')
    else:
        if monthly==True and yearly==True:
            return "Choose one of the following: daily graph, monthly graph, yearly graph"
        elif yearly==True:
            data=data.sort_values('year')
            finalframe=pd.DataFrame()
            for i in sorted(set(data['year'])):
                tester=pd.DataFrame(data[data['year']<=i][var].value_counts()).reset_index().rename(columns={'index':var,var:'Frequency'})
                for j in set(data[var]):
                    if j not in set(tester[var]):
                        temp=pd.DataFrame([j,0]).T.rename(columns={0:var}).rename(columns={0:var,1:'Frequency'})
                        tester=pd.concat([tester,temp])
                tester=tester.sort_values(var)
                tester
                date=np.repeat(i,len(tester))
                tester['date']=date
                tester=tester.reset_index(drop=True)
                finalframe=pd.concat([finalframe,tester])
                value=[]
                for i in list(set(finalframe[var])):
                    value.append(max(finalframe[finalframe[var]==i]['Frequency']))
            fig=px.bar(finalframe,y=var,x='Frequency',animation_frame='date',orientation='h',range_x=[0,max(value)]).update_yaxes(categoryorder='total ascending')
        elif monthly==True:
            data=data.sort_values('month')
            finalframe=pd.DataFrame()
            for i in sorted(set(data['month'])):
                tester=pd.DataFrame(data[data['month']<=i][var].value_counts()).reset_index().rename(columns={'index':var,var:'Frequency'})
                for j in set(data[var]):
                    if j not in set(tester[var]):
                        temp=pd.DataFrame([j,0]).T.rename(columns={0:var}).rename(columns={0:var,1:'Frequency'})
                        tester=pd.concat([tester,temp])
                tester=tester.sort_values(var)
                tester
                date=np.repeat(i,len(tester))
                tester['date']=date
                tester=tester.reset_index(drop=True)
                finalframe=pd.concat([finalframe,tester])
                value=[]
                for i in list(set(finalframe[var])):
                    value.append(max(finalframe[finalframe[var]==i]['Frequency']))
            fig=px.bar(finalframe,y=var,x='Frequency',animation_frame='date',orientation='h',range_x=[0,max(value)]).update_yaxes(categoryorder='total ascending')
        else:
            data=data.sort_values('day')
            finalframe=pd.DataFrame()
            for i in sorted(set(data['day'])):
                tester=pd.DataFrame(data[data['day']<=i][var].value_counts()).reset_index().rename(columns={'index':var,var:'Frequency'})
                for j in set(data[var]):
                    if j not in set(tester[var]):
                        temp=pd.DataFrame([j,0]).T.rename(columns={0:var}).rename(columns={0:var,1:'Frequency'})
                        tester=pd.concat([tester,temp])
                tester=tester.sort_values(var)
                tester
                date=np.repeat(i,len(tester))
                tester['date']=date
                tester=tester.reset_index(drop=True)
                finalframe=pd.concat([finalframe,tester])
                value=[]
                for i in list(set(finalframe[var])):
                    value.append(max(finalframe[finalframe[var]==i]['Frequency']))
            fig=px.bar(finalframe,y=var,x='Frequency',animation_frame='date',orientation='h',range_x=[0,max(value)]).update_yaxes(categoryorder='total ascending')
    fig=fig.update_geos(projection_type="equirectangular", visible=True, resolution=110)
    fig.write_html(outputFilename)

    return outputFilename