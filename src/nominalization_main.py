#written by Catherine Xiao, Apr 2018
#edited by Elaine Dong, Dec 04 2019
#edited by Roberto Franzosi, Nov 2019, October 2020

# https://stackoverflow.com/questions/2836959/adjective-nominalization-in-python-nltk
# https://stackoverflow.com/questions/45109767/get-verb-from-noun-wordnet-python

# https://github.com/topics/nominalization
# https://pypi.org/project/qanom/0.0.1/

import sys
import GUI_util
import IO_libraries_util

if IO_libraries_util.install_all_Python_packages(GUI_util.window,"Nominalization",['tkinter','nltk','pywsd','wn','csv','re','os','collections'])==False:
    sys.exit(0)

import os
import tkinter as tk
import tkinter.messagebox as mb
import nltk

# check averaged_perceptron_tagger
#IO_libraries_util.import_nltk_resource(GUI_util.window,'taggers/averaged_perceptron_tagger','averaged_perceptron_tagger')
# check punkt
#IO_libraries_util.import_nltk_resource(GUI_util.window,'tokenizers/punkt','punkt')
# check WordNet
IO_libraries_util.import_nltk_resource(GUI_util.window,'corpora/WordNet','WordNet')

# from Stanza_functions_util import stanzaPipeLine, sent_tokenize_stanza
# MUST use this version or code will break no longer true; pywsd~=1.2.4 pip install pywsd~=1.2.4; even try pip install pywsd=1.2.2
#   or this version pip install pywsd==1.0.2
# https://github.com/alvations/pywsd/issues/65
# pywsd depends upon wn below; if the code breaks reinstall wn
# pywsd Python word sense disambiguation
#   https://pypi.org/project/pywsd/
from pywsd import disambiguate
from nltk.corpus import wordnet as wn
# pip install wn==0.0.23
import string
import re
from collections import Counter


import IO_files_util
import IO_csv_util
import IO_user_interface_util
import charts_util
import GUI_IO_util

# RUN section ______________________________________________________________________________________________________________________________________________________

#first_section is to extract the word from "syns".
# syns.name() of "intention" is "purpose.n.01". So "first_section" gets everything before the first period: "purpose"

#params: sent > string
#result #includes word='NO NOMINALIZATION'
#count #includes word='NO NOMINALIZATION'
#count1 #excludes word='NO NOMINALIZATION'
def nominalized_verb_detection(docID,doc,sent):
    # sentences = tokenize.sent_tokenize(sent)
    from Stanza_functions_util import stanzaPipeLine, sent_tokenize_stanza
    sentences = sent_tokenize_stanza(stanzaPipeLine(sent))

    result = []
    result1 = []
    verbs = []
    true_word = []
    false_word = []
    # word count for the sentence
    word_count = []
    # number of nominalization in the sentence
    nomi_count = []
    sen_id = -1
    # to print the sentence in output
    sentence = []
    # to print the nominalizations in each sentence
    nomi_sen = []
    nomi_sen_ = ""
    def is_pos(s, pos):
        # print(s)
        return s.split('.')[1] == pos
    for each_sen in sentences:
        sen_id += 1
        nomi_count.append(0)
        word_count.append(0)
        sentence.append(each_sen)
        words_with_tags = disambiguate(each_sen)
        for tup in words_with_tags:
            word, syns = tup
            if (word in string.punctuation) or (word == "\"") or (word[0] == "\'") or (word[0] == "`"):
                continue
            word_count[sen_id] += 1
            derivationals = []
            word = word.lower()
            if word in true_word:
                nomi_count[sen_id] += 1
                if nomi_sen_ == "":
                    nomi_sen_ = word
                else:
                    nomi_sen_ = nomi_sen_ + "; " + word
                noun_cnt[word] += 1
                nominalized_cnt[word] += 1
                continue
            if word in false_word:
                noun_cnt[word] += 1
                continue
            if syns:
                #look at only nouns
                if not is_pos(syns.name(), 'n'):
                    # TODO do not save; leads to huge file
                    # result.append([word, '', False])
                    false_word.append(word)
                    noun_cnt[word] += 1
                    continue
                if wn.lemmas(word):
                    for lemma in wn.lemmas(word):
                        derive = lemma.derivationally_related_forms()
                        if derive not in derivationals and derive:
                            derivationals.append(derive)
                else:
                    try:
                        derivationals = syns.lemmas()[0].derivationally_related_forms()
                    except:
                        pass
                stem = first_section.match(str(syns.name())).group(1)
                found = False
                for deriv in derivationals:
                    if is_pos(str(deriv), 'v'):
                        # original deriv_str = str(deriv)[7:-3].split('.')[3]
                        # deriv is a list with typically one item
                        #   [Lemma('construct.v.01.construct)
                        # sometimes the list can have multiple items
                        #   deriv [Lemma('dramatize.v.02.dramatize), Lemma('dramatize.v.02.dramatise')]
                        #   when multiple items are given taken the first in the list
                        #   deriv[0]
                        try:
                            deriv_str = str(deriv[0])[7:-2].split('.')[3]
                        except:
                            deriv_str = str([deriv][0])[7:-2].split('.')[3]
                        if word=='lights':
                            print('wrong')
                        print('   NOUN:', word, ' VERB:',deriv_str)
                        # deriv_str = str(deriv[0])[7:-2].split('.')[3]
                        # deriv_str is now the verb that is being lemmatized
                        result.append([word, deriv_str, True])
                        verbs.append(deriv_str)
                        true_word.append(word)
                        noun_cnt[word] += 1
                        if nomi_sen_ == "":
                            nomi_sen_ = word
                        else:
                            nomi_sen_ = nomi_sen_ + "; " + word
                        nominalized_cnt[word] += 1
                        found = True
                        break
                if found:
                    nomi_count[sen_id] += 1
                    continue
                else:
                    # TODO do not save; leads to a huge file
                    # result.append([word, '', False]) #includes word='NO NOMINALIZATION'
                    noun_cnt[word] += 1
        nomi_sen.append(nomi_sen_)
        nomi_sen_ = ""
    for i in range(sen_id+1):
        #['Document ID', 'Document', 'Sentence ID', 'Sentence', 'Number of words in sentence', 'Nominalized verbs','Number of nominalizations in sentence', 'Percentage of nominalizations in sentence'])
        if word_count[i]>0:
            # result1.append([docID, IO_csv_util.dressFilenameForCSVHyperlink(doc), i+1, sentence[i], word_count[i], nomi_sen[i], nomi_count[i],
                              #                  100.0*nomi_count[i]/word_count[i]])
            result1.append([word_count[i], nomi_sen[i], nomi_count[i], 100.0 * nomi_count[i] / word_count[i],
                       i + 1, sentence[i], docID, IO_csv_util.dressFilenameForCSVHyperlink(doc)])
        else:
            # result1.append([docID, IO_csv_util.dressFilenameForCSVHyperlink(doc), i+1, sentence[i], word_count[i], nomi_sen[i], nomi_count[i]])
            result1.append(
                [word_count[i], nomi_sen[i], nomi_count[i], sentence[i], docID, IO_csv_util.dressFilenameForCSVHyperlink(doc) ])
    # print(result1)
    # result contains a list of each word TRUE/FALSE values for nominalization
    # result1 contains a list of docID, docName, sentence...
    return result, result1

def list_to_csv(outputFilename, lists):
    """
    for list_ in lists:
        word, bool = tup_
        bool = str(bool)
        outputFilename.write(word)
        outputFilename.write(',')
        outputFilename.write(bool)
        outputFilename.write('\n')
        """
    IO_csv_util.list_to_csv(GUI_util.window,lists,outputFilename,colnum=0)

def write_dir_csv(outputFilename, lists, file_name):
    parts = file_name.split(os.path.sep)
    file_name = parts[-1]
    for list_ in lists:
        list_.append(file_name)
    IO_csv_util.list_to_csv(GUI_util.window,lists,outputFilename,colnum=0)

def run(inputFilename,inputDir, outputDir,openOutputFiles,createCharts,chartPackage,doNotListIndividualFiles):
    global first_section, noun_cnt, nominalized_cnt

    first_section = re.compile("^(.+?)\.")
    noun_cnt = Counter()
    nominalized_cnt = Counter()
    filesToOpen = []  # Store all files that are to be opened once finished

    if __name__ == '__main__':
        nltk.data.path.append('./nltk_data')

        inputDocs = []
        if os.path.isdir(inputDir):
            for f in os.listdir(inputDir):
                if f[:2] != '~$' and f[-4:] == '.txt':
                    inputDocs.append(os.path.join(inputDir, f))
            if len(inputDocs) == 0:
                print("There are no txt files in the input path. The program will exit.")
                mb.showwarning(title='No txt files found',
                               message='There are no txt files in the selected input directory.\n\nPlease, select a different input directory and try again.')
                return
        else:
            inputDocs = [inputFilename]

        nDocs=len(inputDocs)

        startTime=IO_user_interface_util.timed_alert(GUI_util.window,2000,'Analysis start', 'Started running Nominalization at',
                                           True, '', True, '', False)

        #add all into a sum
        result_dir = []
        docID=0
        result2 = []
        result_dir2=[]
        counter_nominalized_list = []
        counter_nominalized_list.append(['Nominalized verb', 'Frequency'])
        counter_noun_list = []
        counter_noun_list.append(['Noun', 'Frequency'])

        for doc in inputDocs:

            docID=docID+1
            head, tail = os.path.split(doc)
            print("Processing file " + str(docID) + "/" + str(nDocs) + ' ' + tail)
            #open the doc and create the list of result (words, T/F)
            fin = open(doc, 'r',encoding='utf-8',errors='ignore')
            # result1 contains the sentence and nominalized values for a specific document
            result, result1 = nominalized_verb_detection(docID,doc,fin.read())
            # result2 contains the sentence and nominalized values for all documents
            result2.extend(result1)
            fin.close()

            # list all verbs as TRUE/FALSE if nominalized
            for word, verb, boolean in result:
                result_dir.append([word, verb, boolean, docID, IO_csv_util.dressFilenameForCSVHyperlink(doc)])

            result_dir2.append(result_dir)

            if len(inputDir) > 0:
                fname = os.path.basename(os.path.normpath(inputDir))+"_dir"
            else:
                fname=doc

            # used for both individual files and directories
            # outputFilename_bySentenceIndex = IO_files_util.generate_output_file_name(fname, '', outputDir,
            #                                                                           '.csv', 'NOM', 'sent', '', '',
            #                                                                           '', False, True)
            #
            outputFilename_bySentenceIndex = IO_files_util.generate_output_file_name(fname, '', outputDir,
                                                                                      '.csv', 'NOM', 'sent')
            if len(inputDir) == 0 or doNotListIndividualFiles == False:
                counter_nominalized_list = []
                counter_noun_list = []
                # refresh the headers
                counter_nominalized_list.insert(0,['Nominalized verb', 'Frequency'])
                counter_noun_list.insert(0,['Noun', 'Frequency'])

                result1.insert(0, ['Number of words in sentence', 'Nominalized verbs',
                                   'Number of nominalizations in sentence',
                                   'Percentage of nominalizations in sentence',
                                   'Sentence ID', 'Sentence', 'Document ID', 'Document'])

                # compute frequency of most common nominalized verbs
                for word, freq in nominalized_cnt.most_common():
                    counter_nominalized_list.append([word, freq])

                # compute frequency of most common nouns
                for word, freq in noun_cnt.most_common():
                    counter_noun_list.append([word, freq])

                head, fname=os.path.split(doc)
                fname=fname[:-4]

                # outputFilename_noun_frequencies = IO_files_util.generate_output_file_name(fname, '', outputDir, '.csv', 'NOM',
                #                                                                 'noun_freq', '', '', '', False,
                #                                                                            True)
                outputFilename_noun_frequencies = IO_files_util.generate_output_file_name(fname, inputDir, outputDir, '.csv', 'NOM',
                                                                                'noun_freq')
                filesToOpen.append(outputFilename_noun_frequencies)
                # outputFilename_nominalized_frequencies = IO_files_util.generate_output_file_name(fname,
                #                                                                 '', outputDir, '.csv', 'NOM',
                #                                                                  'nominal_freq', '', '', '', False,
                #                                                                                   True)
                outputFilename_nominalized_frequencies = IO_files_util.generate_output_file_name(fname,
                                                                                inputDir, outputDir, '.csv', 'NOM',
                                                                                 'nominal_freq')


                filesToOpen.append(outputFilename_nominalized_frequencies)

                # export nominalized verbs
                list_to_csv(outputFilename_nominalized_frequencies, counter_nominalized_list)

                # export nouns
                list_to_csv(outputFilename_noun_frequencies, counter_noun_list)

                outputFilename_TRUE_FALSE = IO_files_util.generate_output_file_name(fname + '_TRUE_FALSE', '', outputDir,
                                                                               '.csv', 'NOM')

                # TODO this leads to a huge file when processing a directory; comment for now
                # filesToOpen.append(outputFilename_TRUE_FALSE)
                # list_to_csv(outputFilename_TRUE_FALSE, result)

                list_to_csv(outputFilename_bySentenceIndex, result1)
                filesToOpen.append(outputFilename_bySentenceIndex)

        if len(inputDir)>0 and doNotListIndividualFiles == True:
            # outputFilename_TRUE_FALSE_dir = IO_files_util.generate_output_file_name(fname + '_TRUE_FALSE', '', outputDir, '.csv', 'NOM', '', '', '', '', False, True)
            outputFilename_TRUE_FALSE_dir = IO_files_util.generate_output_file_name(fname + '_TRUE_FALSE', '', outputDir, '.csv', 'NOM')
            outputFilename_dir_noun_frequencies=IO_files_util.generate_output_file_name(fname, '', outputDir, '.csv', 'NOM', 'noun_freq', '', '', '', False, True)
            # outputFilename_dir_nominalized_frequencies=IO_files_util.generate_output_file_name(fname, '', outputDir, '.csv', 'NOM', 'nominal_freq', '', '', '', False, True)
            outputFilename_dir_nominalized_frequencies=IO_files_util.generate_output_file_name(fname, '', outputDir, '.csv', 'NOM', 'nominal_freq')

            result2.insert(0, ['Number of words in sentence', 'Nominalized verbs',
                               'Number of nominalizations in sentence', 'Percentage of nominalizations in sentence','Sentence ID', 'Sentence', 'Document ID', 'Document'])
            list_to_csv(outputFilename_bySentenceIndex, result2)
            filesToOpen.append(outputFilename_bySentenceIndex)

            # list all verbs as TRUE/FALSE if nominalized
            # TODO  this leads to a huge file when processing a directory; comment for now
            # result_dir2.insert(0, ["Word", "Verb", "Is nominalized", "Document ID", "Document"])
            # list_to_csv(outputFilename_TRUE_FALSE_dir, result_dir2)
            # filesToOpen.append(outputFilename_TRUE_FALSE_dir)

            counter_noun_list = []
            counter_noun_list.append(['Noun','Frequency'])
            for word, freq in noun_cnt.most_common():
                counter_noun_list.append([word, freq])
            list_to_csv(outputFilename_dir_noun_frequencies, counter_noun_list)
            filesToOpen.append(outputFilename_dir_noun_frequencies)

            counter_nominalized_list = []
            counter_nominalized_list.append(['Nominalized verb','Frequency'])
            for word, freq in nominalized_cnt.most_common():
                counter_nominalized_list.append([word, freq])
            list_to_csv(outputFilename_dir_nominalized_frequencies, counter_nominalized_list)
            filesToOpen.append(outputFilename_dir_nominalized_frequencies)

            if createCharts == True:
                # bar chart of nominalized verbs

                inputFilename = outputFilename_dir_nominalized_frequencies
                columns_to_be_plotted_xAxis=[]
                columns_to_be_plotted_yAxis=[[0, 1]]

                outputFiles = charts_util.run_all(columns_to_be_plotted_yAxis, inputFilename, outputDir,
                                                                 outputFileLabel='NOM_verb',
                                                                 chartPackage=chartPackage,
                                                                 chart_type_list=['bar'],
                                                                 chart_title='Nominalized Verbs',
                                                                 column_xAxis_label_var='column_xAxis_label',
                                                                 hover_info_column_list=[],
                                                                 count_var=0)
                if outputFiles!=None:
                    if isinstance(outputFiles, str):
                        filesToOpen.append(outputFiles)
                    else:
                        filesToOpen.extend(outputFiles)

                # chart_outputFilename=charts_Excel_util.create_excel_chart(GUI_util.window, [counter_nominalized_list], outputFilename_dir_nominalized_frequencies,
                #                             outputDir,'NOM_verb',
                #                             "Nominalized verbs", ["bar"])
                # if len(chart_outputFilename) > 0:
                #     filesToOpen.append(chart_outputFilename)

                # bar chart of nouns

                inputFilename = outputFilename_dir_noun_frequencies
                columns_to_be_plotted_xAxis=[]
                columns_to_be_plotted_yAxis=[[0, 1]]

                outputFiles = charts_util.run_all(columns_to_be_plotted_yAxis, inputFilename, outputDir,
                                                                 outputFileLabel='NOM_noun',
                                                                 chartPackage=chartPackage,
                                                                 chart_type_list=['bar'],
                                                                 chart_title='Nouns',
                                                                 column_xAxis_label_var='column_xAxis_label',
                                                                 hover_info_column_list=[],
                                                                 count_var=0)

                # chart_outputFilename=charts_Excel_util.create_excel_chart(GUI_util.window, [counter_noun_list], outputFilename_dir_noun_frequencies,
                #                             outputDir,'NOM_noun',
                #                             "Nouns", ["bar"])
                if outputFiles!=None:
                    if isinstance(outputFiles, str):
                        filesToOpen.append(outputFiles)
                    else:
                        filesToOpen.extend(outputFiles)

    IO_user_interface_util.timed_alert(GUI_util.window,2000,'Analysis end', 'Finished running Nominalization at', True, '', True, startTime)

    if openOutputFiles == 1:
        IO_files_util.OpenOutputFiles(GUI_util.window, openOutputFiles, filesToOpen, outputDir, scriptName)


#the values of the GUI widgets MUST be entered in the command otherwise they will not be updated
run_script_command=lambda: run(GUI_util.inputFilename.get(),
                                GUI_util.input_main_dir_path.get(),
                                GUI_util.output_dir_path.get(),
                                GUI_util.open_csv_output_checkbox.get(),
                                GUI_util.create_chart_output_checkbox.get(),
                                GUI_util.charts_package_options_widget.get(),
                                doNotCreateIntermediateFiles_var.get())

GUI_util.run_button.configure(command=run_script_command)

# GUI section ______________________________________________________________________________________________________________________________________________________

# the GUIs are all setup to run with a brief I/O display or full display (with filename, inputDir, outputDir)
#   just change the next statement to True or False IO_setup_display_brief=True
IO_setup_display_brief=True
GUI_size, y_multiplier_integer, increment = GUI_IO_util.GUI_settings(IO_setup_display_brief,
                             GUI_width=GUI_IO_util.get_GUI_width(3),
                             GUI_height_brief=280, # height at brief display
                             GUI_height_full=360, # height at full display
                             y_multiplier_integer=GUI_util.y_multiplier_integer,
                             y_multiplier_integer_add=2, # to be added for full display
                             increment=2)  # to be added for full display

GUI_label='Graphical User Interface (GUI) for Nominalization'
head, scriptName = os.path.split(os.path.basename(__file__))
config_filename = scriptName.replace('_main.py', '_config.csv')

# The 4 values of config_option refer to:
#   input file
        # 1 for CoNLL file
        # 2 for TXT file
        # 3 for csv file
        # 4 for any type of file
        # 5 for txt or html
        # 6 for txt or csv
#   input dir
#   input secondary dir
#   output dir
config_input_output_numeric_options=[2,1,0,1]

GUI_util.set_window(GUI_size, GUI_label, config_filename, config_input_output_numeric_options)

window=GUI_util.window
config_input_output_numeric_options=GUI_util.config_input_output_numeric_options
config_filename=GUI_util.config_filename
inputFilename=GUI_util.inputFilename
input_main_dir_path=GUI_util.input_main_dir_path

GUI_util.GUI_top(config_input_output_numeric_options, config_filename, IO_setup_display_brief, scriptName)

doNotCreateIntermediateFiles_var = tk.IntVar() #when an entire directory is processed; could lead to an enourmus number of output files
doNotCreateIntermediateFiles_var.set(1)

doNotCreateIntermediateFiles_checkbox = tk.Checkbutton(window, variable=doNotCreateIntermediateFiles_var, onvalue=1, offvalue=0)
doNotCreateIntermediateFiles_checkbox.config(text="Do NOT produce intermediate csv files when processing all txt files in a directory")
y_multiplier_integer=GUI_IO_util.placeWidget(window,GUI_IO_util.labels_x_coordinate,y_multiplier_integer,doNotCreateIntermediateFiles_checkbox)

def changeLabel_nomin(*args):
    if doNotCreateIntermediateFiles_var.get()==1:
        doNotCreateIntermediateFiles_checkbox.config(text="Do NOT produce intermediate csv files when processing all txt files in a directory")
    else:
        doNotCreateIntermediateFiles_checkbox.config(text="Produce intermediate csv files when processing all txt files in a directory")
doNotCreateIntermediateFiles_var.trace('w',changeLabel_nomin)

def turnOff_doNotCreateIntermediateFiles_checkbox(*args):
    if len(input_main_dir_path.get())>0:
        doNotCreateIntermediateFiles_checkbox.config(state='normal')
    else:
        doNotCreateIntermediateFiles_checkbox.config(state='disabled')
GUI_util.input_main_dir_path.trace('w',turnOff_doNotCreateIntermediateFiles_checkbox)

videos_lookup = {'No videos available':''}
videos_options='No videos available'

TIPS_lookup = {'Nominalization':'TIPS_NLP_Nominalization.pdf'}
TIPS_options='Nominalization'

# add all the lines to the end to every special GUI
# change the last item (message displayed) of each line of the function y_multiplier_integer = help_buttons
# any special message (e.g., msg_anyFile stored in GUI_IO_util) will have to be prefixed by GUI_IO_util.
def help_buttons(window,help_button_x_coordinate,y_multiplier_integer):
    if not IO_setup_display_brief:
        y_multiplier_integer = GUI_IO_util.place_help_button(window,help_button_x_coordinate,y_multiplier_integer,"NLP Suite Help",GUI_IO_util.msg_txtFile)
        y_multiplier_integer = GUI_IO_util.place_help_button(window,help_button_x_coordinate,y_multiplier_integer,"NLP Suite Help",GUI_IO_util.msg_corpusData)
        y_multiplier_integer = GUI_IO_util.place_help_button(window,help_button_x_coordinate,y_multiplier_integer,"NLP Suite Help",GUI_IO_util.msg_outputDirectory)
    else:
        y_multiplier_integer = GUI_IO_util.place_help_button(window, help_button_x_coordinate,y_multiplier_integer,"NLP Suite Help",
                                      GUI_IO_util.msg_IO_setup)

    y_multiplier_integer = GUI_IO_util.place_help_button(window,help_button_x_coordinate,y_multiplier_integer,"NLP Suite Help","Please, untick the checkbox if you want to create intermediate csv files for every txt file in a directory when processing all the txt files in a directory.\n\nWARNING! Unticking the checkbox may result in a very large number of intermediate files (3 csv/xlsx files for every txt file in the directory).")
    y_multiplier_integer = GUI_IO_util.place_help_button(window,help_button_x_coordinate,y_multiplier_integer,"NLP Suite Help",GUI_IO_util.msg_openOutputFiles)

    return y_multiplier_integer -1

y_multiplier_integer = help_buttons(window,GUI_IO_util.help_button_x_coordinate,0)

# change the value of the readMe_message
readMe_message="The Python 3 scripts analyzes a text file for instances of nominaliztion (i.e., the use of nouns instead of verbs, such as 'the lynching' occurred).\n\nNominalization, together with passive verb voices, can be used to deny agency. In fact, in an expression such as 'the lynching occurred' there is no mention of an agent, of who did it."
readMe_command = lambda: GUI_IO_util.display_help_button_info("NLP Suite Help", readMe_message)
GUI_util.GUI_bottom(config_filename, config_input_output_numeric_options, y_multiplier_integer, readMe_command, videos_lookup, videos_options, TIPS_lookup, TIPS_options, IO_setup_display_brief, scriptName)

GUI_util.window.mainloop()
