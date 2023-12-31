"""Pure Python Naive Bayes classifier

Simple nb_classifier.

Initial Author: Kevin Molloy, Chris Simmons & David Nguyen
Received some technical help from Garen Dorsey & Ben Saupp
"""


import numpy as np


class NBClassifier:
    """
    A naive bayes classifier for use with categorical and real-valued
    attributes/features.

    Attributes:
        classes (list): The set of integer classes this tree can classify.
        smoothing_flag (boolean): Indicator whether or not to perform
                                  Laplace smoothing
        feature_dists (list):  A placeholder for each feature/column in X
                               that holds the distributions for that feature.
    """

    def __init__(self, smoothing_flag=False):
        """
        NBClassifier constructor.

        :param smoothing: for discrete elements only
        """
        if smoothing_flag:
            self.smoothing = 1
        else:
            self.smoothing = 0

        """
        feature_dists is a list of dictionaries, one for each feature in X.
        The dictionary is envisioned to be for each class label, and
       the key might be:
          -- for continuous features, a tuple with the distribution
          parameters for a Gaussian (mu, std)
          -- for discrete features, another dictionary where the keys
             are the individual domain values for the feature
             and the value is the computed probability from the training data
        """
        self.feature_dists = []

    def get_smoothing(self):
        if self.smoothing:
            return True
        else:
            return False

    def fit(self, X, X_categorical, y):
        """
        Construct the NB using the provided data and labels.

        :param X: Numpy array with shape (num_samples, num_features).
                  This is the training data.
        :param X_categorical: numpy boolean array with length num_features.
                        True values indicate that the feature is discrete.
                        False values indicate that the feature is continuous.
        :param y: Numpy integer array with length num_samples
                  These are the training labels.

        :return: Stores results in class variables, nothing returned.

        An example of how my dictionary looked after running fit on the
        loan classification problem in the textbook without smoothing:
        [{0: {'No': 0.5714285714285714, 'Yes': 0.42857142857142855},
         1: {'No': 1.0}   },
        {0: {'Divorced': 0.14285714285714285, 'Married': 0.5714285714285714,
             'Single': 0.2857142857142857},
         1: {'Divorced': 0.3333333333333333, 'Single': 0.6666666666666666}   },
        {0: (110.0, 54.543560573178574, 2975.0000000000005),
         1: (90.0, 5.0, 25.0)}]
        """

        # Need a category for each column in X
        assert (X.shape[1] == X_categorical.shape[0])

        # each row in training data needs a label
        assert (X.shape[0] == y.shape[0])

        self.X_categorical = X_categorical
        self.classes = list(set(y))
        self.priors = dict()

        # this populates the priors
        unique, counts = np.unique(y, return_counts=True)
        counts_dict = dict(zip(unique, counts))
        for label in counts_dict:
            self.priors[label] = counts_dict[label] / y.shape[0]

        for feature in range(X.shape[1]):
            feature_info = dict()
            for label in self.classes:
                has_label = X[y == label, feature]
                if not X_categorical[feature]:
                    x_as_float = has_label.astype(float)
                    feature_info[label] = (np.mean(x_as_float),
                                           np.std(x_as_float, ddof=1),
                                           np.var(x_as_float, ddof=1))
                elif X_categorical[feature]:
                    cat_dict = dict()
                    for category in np.unique(X[:, feature]):
                        conditional_probability = (len(has_label[has_label == category]) +
                                                   self.smoothing) / (len(has_label) + (
                                                       self.smoothing * np.unique(X[:, feature]).shape[0]))
                        if conditional_probability != 0:
                            # Special case for zero probability
                            cat_dict[category] = conditional_probability
                    feature_info[label] = cat_dict
            self.feature_dists.append(feature_info)

    def get_prior(self, class_label):
        return self.priors[class_label]

    def feature_class_prob(self, feature_index, class_label, x):
        """
        Compute a single conditional probability.  You can call
        this function in your predict function if you wish.

        Example: For the loan default problem:
            feature_class_prob(1, 0, 'Single') returns 0.5714

        :param feature_index:  index into the feature set (column of X)
        :param class_label: the label used in the probability
            (see return below)
        :param x: the data value

        :return: P(class_label | feature(fi) = x) the probability
        """

        # validate feature_index
        assert feature_index < self.X_categorical.shape[0], \
            'Invalid feature index passed to feature_class_prob'

        # validate class_label
        assert class_label < len(self.classes), \
            'invalid class label passed to feature_class_prob'

        feature_dist = self.feature_dists[feature_index]
        if self.X_categorical[feature_index]:
            return feature_dist[class_label].get(x, 0)
        else:
            # Still not enitrely sure why we need variance.
            mean, st_dev, variance = feature_dist[class_label]
            probability_density = (1 / (st_dev * np.sqrt(2 * np.pi))) * np.exp(
                - (np.power((x.astype(float) - mean), 2)) / (2 * np.power(st_dev ** 2)))
            if probability_density == 0:
                probability_density = 10 ** -9
            return probability_density

    def predict(self, X):
        """
        Predict labels for test matrix X


        Parameters/returns
        ----------
        :param X:  Numpy array with shape (num_samples, num_features)
        :return: Numpy array with shape (num_samples, )
            Predicted labels for each entry/row in X.
        """

        # validate that x contains exactly the number of features
        assert (X.shape[1] == self.X_categorical.shape[0])

        probabilities = np.empty(X.shape[0])

        for attribute in range(X.shape[0]):
            probs_as_logs = np.zeros(self.classes.shape[0])
            for index_label, class_label in enumerate(self.classes):
                probs_as_logs[index_label] = np.log(self.priors[class_label])
                for index_feature, feature in enumerate(X[attribute]):
                    if self.X_categorical[index_feature] and self.feature_dists[index_feature][class_label][1] == 0:
                        val = self.feature_class_prob(
                            index_feature, class_label, feature)
                        if val != 0:
                            probs_as_logs[index_label] += np.log(val)
            probabilities[attribute] = self.classes[np.argmax(probs_as_logs)]

        return probabilities


def nb_demo():
    # data from table Figure 4.8 in the textbook

    X = np.array([['Yes', 'Single', 125],
                  ['No', 'Married', 100],
                  ['No', 'Single', 70],
                  ['Yes', 'Married', 120],
                  ['No', 'Divorced', 95],
                  ['No', 'Married', 60],
                  ['Yes', 'Divorced', 220],
                  ['No', 'Single', 85],
                  ['No', 'Married', 75],
                  ['No', 'Single', 90]])

    # first two features are categorical and 3rd is continuous
    X_categorical = np.array([True, True, False])

    # class labels (default borrower)
    y = np.array([0, 0, 0, 0, 1, 0, 0, 1, 0, 1])

    nb = NBClassifier(smoothing_flag=False)

    nb.fit(X, X_categorical, y)

    test_pt = np.array([['No', 'Married', 120]])
    yhat = nb.predict(test_pt)

    # the book computes this as 0.0016 * alpha
    print('Predicted value for someone who does not a homeowner,')
    print('is married, and earns 120K a year is:', yhat)


def main():
    nb_demo()


if __name__ == "__main__":
    main()
