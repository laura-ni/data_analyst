
# coding: utf-8

import numpy as np
import pandas as pd
import sys
import pickle

sys.path.append("../tools/")

from feature_format import featureFormat, targetFeatureSplit
from tester import dump_classifier_and_data

### Task 1: Select what features you'll use.
### features_list is a list of strings, each of which is a feature name.
### The first feature must be "poi".
features_list = ['poi',] # You will need to use more features

### Load the dictionary containing the dataset
with open("final_project_dataset.pkl", "rb") as data_file:
    data_dict = pickle.load(data_file)


#Read data into data frame
df = (pd.DataFrame
      .from_dict(data_dict, orient='index')
      .reset_index()
      .replace('NaN', np.nan)
     )
#Fill the nan value with 0
df.fillna(0, inplace=True)
df[df['poi'] == True].shape


# There're 18 persons of interest in the dataset.

# ### Remove outlers
df = df[df['index'] != 'TOTAL']

# Create new feature
df['total_messages'] = df['to_messages'] + df['from_messages']

# ### Save my dataset
df_new = df.set_index('index')
df_new.index.name = None
my_dataset = df_new.to_dict(orient= 'index')


# ### Feature Selection

#features and labels
X = df.drop(columns = ['index','poi','email_address'], axis=1)
y = df['poi']


# # Naive_bayes
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV

kbest = SelectKBest(f_classif)
pipeline = Pipeline([('kbest', kbest), ('nb', GaussianNB())])
param_grid={'kbest__k': [i for i in range(1, 21)]}
grid_search = GridSearchCV(pipeline, param_grid = param_grid)
grid_search.fit(X, y)

clf = grid_search.best_estimator_

#rechieve selected features from the best estimator
features_list = ['poi']
idxs_selected = clf.named_steps.kbest.get_support(indices=True)
for i in idxs_selected:
    features_list.append(X.columns[i])

dump_classifier_and_data(clf, my_dataset, features_list)

get_ipython().magic('run tester.py')
