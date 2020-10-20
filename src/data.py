import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.metrics import recall_score
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import make_scorer
import warnings
warnings.filterwarnings("ignore")

def well_recall(y_true,y_pred):
    return recall_score(y_true,y_pred,average=None)[0]

def run_model(X , y, estimator, param_grid={}):

    # Instantiate the KFold object
    kf = StratifiedKFold(n_splits=5,random_state=42)
    pipe = Pipeline([('wellprocessor',WellProcessor()),
                     ('estimator',estimator)])
    
    gridsearch = GridSearchCV(estimator = pipe, 
                              param_grid = param_grid, 
                              cv = kf, 
                              scoring = make_scorer(well_recall))
    gridsearch.fit(X,y)
    
    print(gridsearch.best_score_)
    
    return gridsearch

def load_data():
    """
    Load data into DataFrame, 
    Set index to `id`
    Drop categorical columns with too many values to one-hot
    Set y to numeric classes
    Returns X (features) and y (labels)
    """
    X = pd.read_csv('../data/training_set_values.csv', index_col = 'id')
    y = pd.read_csv('../data/training_set_labels.csv', index_col = 'id')
    X.drop(columns = ['funder','installer','wpt_name','subvillage','ward',
                      'recorded_by','scheme_name','public_meeting','scheme_management'], inplace = True)
    y.replace(to_replace = ['non functional','functional needs repair','functional'],
             value = [0,1,2], inplace = True)
    return X, y

class WellProcessor:
    """
    Takes data from the Tanzanian well dataset and processes it for modeling.  This includes: 
    2. Imputing missing data for 'permit' and 'construction_date' 
        as well as transforming 'date_recorded' into a float.
    2. Scaling numeric data
    3. One-hot-encoding categorical data
    
    Methods:
    fit(X): Fit all transformers on a dataset.  Returns None.
    transform(X): Use fitted transformers to transform data.  Returns a dataframe.
    fit_transform(X): Fit and transform data using transformers.  Returns a dataframe.
    """
    
    def __init__(self):
        pass
    
    def fit(self,X,y=None):
        #fit tranformer on data.
        
        #impute missing values in 'permit' or 'construction_year' if those columns are present in dataframe
        self.cat_imputer = SimpleImputer(missing_values = np.nan, strategy = 'most_frequent')
        self.num_imputer = SimpleImputer(missing_values = 0, strategy = 'median')
        self.ohe = OneHotEncoder(categories = 'auto', sparse = False, dtype = int, handle_unknown = 'ignore')
        self.scaler = StandardScaler()
        cleanX = X.copy()
        if 'date_recorded' in cleanX.columns:
            cleanX['date_recorded'] = cleanX[['date_recorded']].applymap(lambda year: round(int(year.split(sep='-')[0]) + int(year.split(sep='-')[1])/12,2))
            
        if 'permit' in X.columns:
            self.cat_imputer.fit(X[['permit']])
            cleanX['permit'] = self.cat_imputer.transform(cleanX[['permit']])
            
        if 'construction_year' in X.columns:
            self.num_imputer.fit(cleanX[['construction_year']])
            
        self.scaler.fit(cleanX.select_dtypes(include = 'number'))
        self.ohe.fit(cleanX.select_dtypes(include = 'object'))
        
    def transform(self,X,y=None):
        if 'permit' in X.columns:
            X['permit'] = self.cat_imputer.transform(X[['permit']])
        if 'construction_year' in X.columns:
            X['construction_year'] = self.num_imputer.transform(X[['construction_year']])
        if 'date_recorded' in X.columns:
            X['date_recorded'] = X[['date_recorded']].applymap(lambda year: round(int(year.split(sep='-')[0])  + int(year.split(sep='-')[1])/12,2))
# One-hot encode categorical variables
        X_cat = X.select_dtypes(include = 'object')
        
        X_hot = pd.DataFrame(self.ohe.transform(X_cat), 
                            index = X_cat.index, 
                            #columns = ohe.get_feature_names(X_cat.columns)
                            )
        
#scale numeric
        X_num = X.select_dtypes(include = 'number')
        X_num_ss = pd.DataFrame(self.scaler.transform(X_num), 
                                index = X_num.index, 
                                columns = X_num.columns)
    
        return pd.concat([X_num_ss, X_hot], axis = 1)
    
    def fit_transform(self,X,y=None):
        #fit
        self.cat_imputer = SimpleImputer(missing_values = np.nan, strategy = 'most_frequent')
        self.num_imputer = SimpleImputer(missing_values = 0, strategy = 'median')
        self.ohe = OneHotEncoder(categories = 'auto', sparse = False, dtype = int, handle_unknown = 'ignore')
        self.scaler = StandardScaler()
    
    #impute
        if 'permit' in X.columns:
            X['permit'] = self.cat_imputer.fit_transform(X[['permit']])
        if 'construction_year' in X.columns:
            X['construction_year'] = self.num_imputer.fit_transform(X[['construction_year']])
            
    #process dates
        if 'date_recorded' in X.columns:
            X['date_recorded'] = X[['date_recorded']].applymap(lambda year: round(int(year.split(sep='-')[0]) + \
                                                            int(year.split(sep='-')[1])/12,2))

# One-hot encode categorical variables
        X_cat = X.select_dtypes(include = 'object')

        X_hot = pd.DataFrame(self.ohe.fit_transform(X_cat), 
                            index = X_cat.index, 
                            columns = self.ohe.get_feature_names(X_cat.columns)
                            )
# Scale numeric
        X_num = X.select_dtypes(include = 'number')
        X_num_ss = pd.DataFrame(self.scaler.fit_transform(X_num), 
                                index = X_num.index, 
                                columns = X_num.columns)
        
        return pd.concat([X_num_ss, X_hot], axis = 1)
        