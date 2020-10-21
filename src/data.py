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

def add_age(X):
    """
    Adds a column indicating the age of the pump.
    Takes a dataframe as an argument.  
    Dataframe MUST include 'date_recorded' and 'construction_year' columns.
    """
    if ('date_recorded' in X.columns):
        if ('construction_year' in X.columns):
            if X['date_recorded'].dtype == ('object'):
                X['date_recorded'] = X[['date_recorded']].applymap(
                    lambda year: round(int(year.split(sep='-')[0]) + int(year.split(sep='-')[1])/12,2))
            X.loc[X['construction_year'] == 0, 'construction_year'] = X['construction_year'].median()
            X['age_of_pump'] = X['date_recorded'] - X['construction_year']
            return X
        else:
            print("'construction_year' not found in dataframe")
            return X
    else:
        print("'date_recorded' not found in dataframe")
        return X

def well_recall(y_true,y_pred):
    """
    uses sklearn.metrics.recall_score() to return the recall score of
    non functioning wells.
    Takes single column array or dataframe of true labels
    and one of predictions 
    returns recall score of class 0.
    """
    
    return recall_score(y_true,y_pred,average=None)[0]

def run_model(X , y, estimator, param_grid={}):
    """
    Takes a feature array, X, a label array, y, an estimator, and an optional parameter grid.
    
    !!!Make sure, to use the following format in your paramgrid: 
    {'estimator__<parameter>':parameter}
    
    Runs a particular model using unprocessed X features and y labels using 
    a pipeline with WellProcessor (specific to the Tanzanian Well dataset) to
    process data, and the passed estimator to fit and predict.
    using imputation of missing values in 'permit' and 'construction_date,
    scaling of numeric data,
    and one-hot encoding of categorical data.  
    Also transforms 'date_recorded' to a float instead of string.
    
    Uses a StratifiedKFold object to make splits specific to our group's specified number of folds
    and random state to create reproduceable results and compare the same splits across models.
    
    Finally uses an optional passed param_grid to run a GridSearchCV using the pipeline and folds that fits on
    the specified metric, recall on class 0 (non functional wells), to optimize the model.
    
    Returns a GridSearchCV object and prints the output of the .cv_results_ attribute of fitted model, showing 
    scores across all folds.
    """


    kf = StratifiedKFold(n_splits=5,random_state=42)
    pipe = Pipeline([('wellprocessor',WellProcessor()),
                     ('estimator',estimator)])
    gridsearch = GridSearchCV(estimator = pipe, 
                              param_grid = param_grid, 
                              cv = kf, 
                              scoring = make_scorer(well_recall))
    
    gridsearch.fit(X,y)
    
    print(gridsearch.cv_results_)
    
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
        """
        fit tranformer on data.  Does not transform data.
        """
        self.cat_imputer = SimpleImputer(missing_values = np.nan, strategy = 'most_frequent')
        self.num_imputer = SimpleImputer(missing_values = 0, strategy = 'median')
        self.ohe = OneHotEncoder(categories = 'auto', sparse = False, dtype = int, handle_unknown = 'ignore')
        self.scaler = StandardScaler()
        
        #create a dummy dataframe to fit correctly (date_recorded will be a float instead of a string in the
        #transform, so it needs to be that way in the fit.  Does NOT change the original dataframe passed.
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
        """
        transforms data by imputing missing values, scaling numeric features, and one-hot encoding categorical
        feature.  Returns a transformed dataframe using the previously fitted transformers.
        """
        #impute missing data
        if 'permit' in X.columns:
            X['permit'] = self.cat_imputer.transform(X[['permit']])
        if 'construction_year' in X.columns:
            X['construction_year'] = self.num_imputer.transform(X[['construction_year']])
            
        #Change 'date_recorded' to a float
        if 'date_recorded' in X.columns:
            X['date_recorded'] = X[['date_recorded']].applymap(lambda year: round(int(year.split(sep='-')[0])  + int(year.split(sep='-')[1])/12,2))
            
        # One-hot encode categorical variables
        X_cat = X.select_dtypes(include = 'object')
        
        X_hot = pd.DataFrame(self.ohe.transform(X_cat), 
                            index = X_cat.index, 
                            #columns = ohe.get_feature_names(X_cat.columns) #this does not seem to work.
                            )
        
        #scale numeric
        X_num = X.select_dtypes(include = 'number')
        X_num_ss = pd.DataFrame(self.scaler.transform(X_num), 
                                index = X_num.index, 
                                columns = X_num.columns)
    
        #return transformed dataframe
        return pd.concat([X_num_ss, X_hot], axis = 1)
    
    def fit_transform(self,X,y=None):
        """
        Fits tranformer to data AND returns transformed dataframe.  DO NOT USE ON TESTING OR VALIDATION DATA! 
        """
        #create transformer objects
        self.cat_imputer = SimpleImputer(missing_values = np.nan, strategy = 'most_frequent')
        self.num_imputer = SimpleImputer(missing_values = 0, strategy = 'median')
        self.ohe = OneHotEncoder(categories = 'auto', sparse = False, dtype = int, handle_unknown = 'ignore')
        self.scaler = StandardScaler()
    
        #impute missing data
        if 'permit' in X.columns:
            X['permit'] = self.cat_imputer.fit_transform(X[['permit']])
        if 'construction_year' in X.columns:
            X['construction_year'] = self.num_imputer.fit_transform(X[['construction_year']])
            
        #process dates into floats
        if 'date_recorded' in X.columns:
            X['date_recorded'] = X[['date_recorded']].applymap(lambda year: round(int(year.split(sep='-')[0]) + \
                                                            int(year.split(sep='-')[1])/12,2))

        # One-hot encode categorical variables
        X_cat = X.select_dtypes(include = 'object')

        X_hot = pd.DataFrame(self.ohe.fit_transform(X_cat), 
                            index = X_cat.index, 
                            columns = self.ohe.get_feature_names(X_cat.columns)
                            )
        # Scale numeric variables
        X_num = X.select_dtypes(include = 'number')
        X_num_ss = pd.DataFrame(self.scaler.fit_transform(X_num), 
                                index = X_num.index, 
                                columns = X_num.columns)
        
        # Return tranformed dataframe
        return pd.concat([X_num_ss, X_hot], axis = 1)
        