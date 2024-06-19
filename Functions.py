# -*- coding: utf-8 -*-
"""
Created on Fri Feb 18 09:45:40 2022

@author: pstehlik

This file contains functions used during wrangling and analysis of the ENHANCE Survey data



"""


# LOAD LIBRARIES

import regex as re

import pandas as pd

import numpy as np






#create list of columns to extract

def getColumns(letter,number):
    
    """
    This is a function to create a list of columns for projects needed without defining each time
    
    number = which number loop of Q9
    letter = which sub question of Q9
    
    e.g. e, 2 will create the values 1_Q9e, 2_Q9e
    
    """
    
    columns = []
    
    for i in range (1, number + 1):
        
        question = str(i) + "_Q9" + letter
        columns.append(question)
    return  columns




# get vaues for a single column





"""
Participants who stated that they conducted a project during their training were asked quetsions about 
their experiece for each project.

"""






def reorder(dataFrame, categories, col = 'Answer'):
    
    """"
    Function to reorder rows to give specific order
    
    """
    
    #reorder rows
    dataFrame = dataFrame.set_index(col)
    
    dataFrame = dataFrame.reindex(categories)
    
    dataFrame.reset_index(level=0, inplace=True)
    
    return dataFrame
















def create4colDF(df, col, question, categories, eligible):
    
    """
    This is a function that creates a df with 4 columns by extracting answers from Q9 of survey
    
    df = data 
    
    col = which column e.g. Q9a or Q9b - only need the letter as Q9 is assumed
    
    question = question asked in survey. Will be put in column 1 of table
    
    numberCols = number of columns extracted e.g. 3 = 1_Q9_a, 2_Q9_a, 3_Q9_a
    
    eligible = number of participants eligible to answer the question
    
    STRUCTURE:
        
        Question | Answer | Number of participants | Prop. participants
        ---------|--------|------------------------
        Question from survey |  answers from survey | number | Prop.
        e.g.SR done?  |  Yes  | 25 | 0.08
        
        
    
    
    """
    
        
    headings = list(df)

    #find the max number of projects that had the question answered

    r = re.compile("^\d+\_Q9" + col)
    newlist = list(filter(r.match, headings)) # Read Note below

    numbers = []

    for i in newlist:
        i = int(i.split('_', 1)[0].replace('.', '').upper())
        numbers.append(i)


    numberCols = max(numbers)

    #choose questions of interest
    questions = getColumns(col, numberCols) #CHANGE TO NUMBER

    #get those who completed a project
    df_1 = df[df.Q6 == "Yes"][["Q3_1","Q3_2"]+ questions]



    df_1 = pd.melt(df_1,
                   id_vars=['Q3_1',
                            'Q3_2',],
                   value_vars = questions)


    df_2 = pd.DataFrame(df_1.value.value_counts())


    df_2.reset_index(inplace=True)

    df_2.rename(columns={"index": 'Answer',
                         "value": 'Number of projects'}, inplace=True) #rename column

    #reorder columns
    df_2 = reorder(df_2, categories)


    #add question column

    newCol = [" "] * len(df_2)
    #   newCol[0] = question


    #add to df
    df_2.insert(loc= 0, 
                column='Question', 
                value=newCol)


    df_2 = df_2[['Question','Answer', 'Number of projects']]



    df_3 = pd.DataFrame(df_1.value.value_counts(normalize=True))

    df_3["value"] =(df_3["value"]*100).round(0).astype(int) # round to 2 dec places
    df_3.reset_index(inplace=True)



    df_3.rename(columns={"index": 'Answer',
                         "value": 'Prop. of projects'}, inplace=True) #rename column


    #reorder columns

    df_3 = reorder(df_3, categories)

    #reorder columns

    df_3 = reorder(df_3, categories)


    #add question column   
    newCol = [" "] * len(df_3)
    # newCol[0] = question


    #add to df
    df_3.insert(loc= 0, 
                column='Question', 
                value=newCol)


    df_3 = df_3[['Question','Answer', 'Prop. of projects']]



    #merge dfs
    df_4 = df_2.merge(df_3['Prop. of projects'], how='outer', left_index=True, right_index=True)



    #fill missing values with 0 as these were missing categories

    df_4 = df_4.fillna(0)
    df_4['Prop. of projects'] = df_4['Prop. of projects'].astype(int).astype(str) + '%' 

    #find the % response rate for the question

    responseRate = ((df_4['Number of projects'].sum()/eligible).round(2)*100).astype(int)


    #add total row - total number of participants who answered the question
    df_4.loc[-1] = ["", "Total answered", df_4['Number of projects'].sum(),str(responseRate) + "% *"]

    df_4.sort_index(inplace=True) 

    df_4.reset_index(inplace=True, drop = True)

    #add number of eligible projects row - total number of participants that were eligible to respond
    df_4.loc[-1] = ["", "Eligible", eligible,"-"]

    df_4.sort_index(inplace=True) 

    df_4.reset_index(inplace=True, drop = True)


    #add row with the question row
    df_4.loc[-1] = [question, "", "",""]

    df_4.sort_index(inplace=True) 

    df_4.reset_index(inplace=True, drop = True)


    
    return df_4
        
        






#************************************************************

def createMULTIcolDF(df, col, question, regex, categories, eligible, what = 0, colName = None):
    
    """
    This is a function that creates a df with 4 columns by extracting answers from Q9 of survey.
    It also takes into account multi answers
    
    col = which column e.g. Q9a or Q9b - only need the letter as Q9 is assumed
    
    question = question asked in survey. Will be put in column 1 of table
    
    colName = Name of column
    
    what = returns different dfs
    
        STRUCTURE:
            
            what = 0
            
            Question | Answer | Number of projects | Prop. projects
            ---------|--------|------------------------
            Question from survey |  answers from survey | number | Prop.
            e.g.SR done?  |  Yes  | 25 | 0.08
            
            
            *********
            
            what = 1
            
                                  Number of times category appears | Number of projects           
           colName - e.g. Number of places protocol is registered | Number of projects
            ------------------------------------------------------|--------------------
                                   0                             | 40
                                   1                             | 19
                                                                | 1
            
            
            *********
            
            what = 2
            
            returns long form 
            
            project_number | value
            ---------------|----------
            number given to each project | Category
            e.g. 5     | Yes - Published in a Journal
        
    
    """


     
    
    headings = list(df)
            
        
    #find the max number of projects that had the question answered
    
    r = re.compile("^\d+\_Q9" + col + "$")
    newlist = list(filter(r.match, headings)) # Read Note below
    
    numbers = []
    
    for i in newlist:
        i = int(i.split('_', 1)[0].replace('.', '').upper())
        numbers.append(i)
        
        
    numberCols = max(numbers)
  
    
    
    #choose questions of interest
    questions = getColumns(col, numberCols) #CHANGE TO NUMBER
    
    
    #get those who completed a project
    df_1 = df[df.Q6 == "Yes"][["Q3_1","Q3_2"]+ questions]


        
    
        
    #create empty df for analysis
    df_3 = pd.DataFrame(columns=['project_number', 'value'])
    
    
    start_number = 0
    
    
    #for each project where we have answers
    for i in numbers:
        
        #get the column number
    
        j = str(i)+"_Q9"+col
        
        #print(j)
    
    
        
        #split if there are multiple responses
        
        df_2 = df_1[j].str.split(regex, expand=True) #split on ",Yes" = multiple answers
        
        
        
        
        #if there are multiple answers, need to get them
        
        if df_2.shape[1] > 1:
        
            df_2 = df_2.fillna(value=np.nan) #replace None with Nan
            
            df_2[0] = np.where(~df_2[1].isnull(),df_2[1],df_2[0]) # put extracted value into first column if not Nan (ie answer 1)
            
            
            #drop column 1 as no longer needed
            
            df_2 = df_2.drop([1], axis = 1)
            
        
        
        """
        
        I'VE DONE IT AS NUMBER ANSWERED / NUMBER OF PROJECTS
        
        
        """
        
        #remove all rows with NaN
        df_2.dropna(subset = [0], inplace=True)
        
          
        
        #number projects
        df_2['project_number'] = np.arange(len(df_2)) + start_number + 1
        
        
        start_number = max(df_2['project_number']) #get last number for use in next round
        
        
        
        #create list of columns that are needed
        l = [i for i in range(df_2.shape[1])]
        l.remove(1)
        
        
        #if more than one entry, convert from long to wide data
        if df_2.shape[1] > 2: 
            
            df_2 = pd.melt(df_2,
                           id_vars=['project_number'],
                           value_vars = l)
        
            
            #remove variable column
            df_2  = df_2.drop(["variable"], axis = 1)
            
            #remove rows with NaN
            df_2.dropna(subset = ["value"], inplace=True)
            
        
        #otherwise need to rename column from 0 to value
        else: 
            
            df_2 = df_2.rename(columns={0: "value"})
            
        
        
        #append to df for analysis
        
        df_3 = df_3.append(df_2, 
                           ignore_index = True)
        
        
    
    #demonimator
    maxNumber = max(df_3.project_number)
    
    
    #count number in each category
    df_4 = pd.DataFrame(df_3.value.value_counts())
    
    df_4['Prop. of projects'] = df_4.value/maxNumber
    
    
    df_4['Prop. of projects'] = (df_4['Prop. of projects']*100).round(2).astype(int)
    
    
    
    #rename columns
    df_4.reset_index(inplace=True)
        
    df_4.rename(columns={"index": 'Answer',
                         "value": 'Number of projects'}, inplace=True) #rename column
    
    
    df_4 = reorder(df_4, categories)
    
   
    
    #add question column
    newCol = [" "] * len(df_4)
 #   newCol[0] = question
    
    
    #add to df
    df_4.insert(loc= 0, 
                column='Question', 
                value=newCol)
    
    
    #fill missing values with 0 as these were missing categories
    
    df_4 = df_4.fillna(0)
    df_4['Prop. of projects'] = df_4['Prop. of projects'].astype(int).astype(str) + '%'
    
    #find the % response rate for the question
    
    
    
    #get those who completed a project
    df_1 = df[df.Q6 == "Yes"][["Q3_1","Q3_2"]+ questions]
    
    
    
    df_1 = pd.melt(df_1,
                   id_vars=['Q3_1',
                            'Q3_2',],
                   value_vars = questions)
    
    #number of participants that answered the question
    answered = len(df_1[~df_1["value"].isnull()])
    
    responseRate = int(round((answered/eligible),2)*100)
    
    #add total row - total number of participants who answered the question
    df_4.loc[-1] = ["", "Total answered †", answered, str(responseRate) + "% *"]

    df_4.sort_index(inplace=True) 
    
    df_4.reset_index(inplace=True, drop = True)


    #add total row - total number of participants who answered the question
    df_4.loc[-1] = ["", "Eligible", eligible, "-"]

    df_4.sort_index(inplace=True) 
    
    df_4.reset_index(inplace=True, drop = True)


    #add row with the question row
    df_4.loc[-1] = [question, "", "",""]

    df_4.sort_index(inplace=True) 
    
    df_4.reset_index(inplace=True, drop = True)
 
    
    
    
    
    if what == 1:
        #Filter to only those who did do the thing of interest
        df_4= df_3[~df_3["value"].isin(["No", "No ", "None of the above"])]
        
        df_4 = (df_4['project_number'].value_counts()
                           .value_counts()
                           .rename_axis(colName)
                           .reset_index(name='Number of projects'))
        
        
        #Filter to only those who did NOT did do the thing of interest
        new_row = pd.DataFrame({colName:[0], 
                                'Number of projects':[len(df_3[df_3["value"].isin(["No", "No ", "None of the above"])])]})
        
                                            
        df_4 = new_row.append(df_4)
        
        
        return df_4
    
    if what == 2:
        
        return df_3
    


    else:
        return df_4
    









def answersNOTQ9 (df, question, col, categories, eligible, projectsOnly = "Projects"):
    
    """
    creates 4 column df from non Q9 responses (ie 1 response per person)

    
    col = which column e.g. Q10_1 or Q12 - need to put in FULL question name
    
    question = question asked in survey. Will be put in column 1 of table
    
    categories = order of categories in question
    
    projectsOnly = include all data or only those who have completed projects (default projects only)
    
    eligible = number of participants eligible to answer the question
    
    STRUCTURE:
        
        Question | Answer | Number of participants | Prop. participants
        ---------|--------|------------------------
        Question from survey |  answers from survey | number | Prop.
        e.g.SR done?  |  Yes  | 25 | 0.08
    
    """
    
    questions = [col]
    
    if projectsOnly == "Projects":
    
        #get those who completed a project
        df_1 = df[df.Q6 == "Yes"][["Q3_1","Q3_2"]+ questions]
         
         
         
        
    else:
        df_1 = df
        
        
    df_1 = pd.melt(df_1,
                    id_vars=['Q3_1',
                             'Q3_2',],
                    value_vars = questions)
     
     
    df_2 = pd.DataFrame(df_1.value.value_counts())
     
     
    df_2.reset_index(inplace=True)
     
    df_2.rename(columns={"index": 'Answer',
                          "value": 'Number of projects'}, inplace=True) #rename column
    
    
    df_2 = reorder(df_2, categories)
    
     
    #add question column
     
    
    newCol = [" "] * len(df_2)
  #  newCol[0] = question
     
     
    #add to df
    df_2.insert(loc= 0, 
                 column='Question', 
                 value=newCol)
     
     
    df_2 = df_2[['Question','Answer', 'Number of projects']]
    
    
        
    df_3 = pd.DataFrame(df_1.value.value_counts(normalize=True))
     
    df_3["value"] = (df_3["value"]*100).round(0).astype(int) # round to 2 dec places
      
     
    df_3.reset_index(inplace=True)
     
    df_3.rename(columns={"index": 'Answer',
                          "value": 'Prop. of projects'}, inplace=True) #rename column
     
    
    #reorder columns
    
    df_3 = reorder(df_3, categories)
    
    
    
    #add question column
      
    newCol = [" "] * len(df_3)
 #   newCol[0] = question
     
     
    #add to df
    df_3.insert(loc= 0, 
                column='Question',
                value=newCol)
     
     
    df_3 = df_3[['Question','Answer', 'Prop. of projects']]
     
    df_4 = df_2.merge(df_3['Prop. of projects'], how='outer', left_index=True, right_index=True)
         
    
    #fill missing values with 0 as these were missing categories
    
    df_4 = df_4.fillna(0)
    df_4['Prop. of projects'] = df_4['Prop. of projects'].astype(int).astype(str) + '%' 
    
   #find the % response rate for the question
    
    responseRate = (((df_4['Number of projects'].sum()/eligible)*100).round(0)).astype(int)
    
    #add total row - total number of participants who answered the question
    df_4.loc[-1] = ["", "Total answered", df_4['Number of projects'].sum(),str(responseRate) + "% *"]

    df_4.sort_index(inplace=True) 
    
    df_4.reset_index(inplace=True, drop = True)

        #add eligible row - total number of participants who were eligible to answer the question
    df_4.loc[-1] = ["", "Eligible", eligible, ""]

    df_4.sort_index(inplace=True) 
    
    df_4.reset_index(inplace=True, drop = True)



    #add question row - what was the question asked?
    df_4.loc[-1] = [question, "", "", ""]

    df_4.sort_index(inplace=True) 
    
    df_4.reset_index(inplace=True, drop = True)
  

    
    return df_4
    

