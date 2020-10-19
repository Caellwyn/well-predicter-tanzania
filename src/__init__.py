import math 

def graph_categorical(df, column_array):
    """
    Graphs the categorical columns of df specified in column_array.
    Plots the given categorical columns against the column in df labelled 'target'
    Prints those plots
    Returns nothing.
    Returns an error if 'target' is not a column in df, or if all columns are not categorical.
    """
    try:
        assert('target' in df.columns)
    except:
        print("'target' not found in df.columns")
        return None
        
    try: 
        for col in column_array:
            assert(df[col].dtype == 'O')
    except:
        print('numeric type column passed to graph_categorical')
        return None
        
    fig, axes = plt.subplots(math.ceil(len(cols)/2),2, figsize = (10,15), sharey = True)
    axes = axes.reshape(-1)
    print(axes)
    for i in range(len(cols)):
        ax = axes[i]
        df_grouped = pd.DataFrame(df.groupby(cols[i])['target'].value_counts(normalize=True)).unstack()
        df_grouped.plot.bar(ax = ax)
        ax.get_legend().remove()
        ax.set_title(cols[i].title().replace('_'," "),fontdict = {'fontsize':15}, y = .9)
        ax.set_xlabel('')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper right', fontsize = 'small', fancybox = True)
    plt.tight_layout()
    plt.subplots_adjust(top = .95)
    plt.suptitle('Percentages of Categories in Each Target', fontsize = 15)