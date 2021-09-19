from contextualized_topic_models.models.ctm import ZeroShotTM
from contextualized_topic_models.utils.preprocessing import WhiteSpacePreprocessing
from contextualized_topic_models.utils.data_preparation import TopicModelDataPreparation
import numpy as np
import pickle
import ipywidgets as widgets
from IPython.display import display


class Kitty:
    """
    Kitty is a utility to generate a simple classifiers from a topic model. It first run
    a CTM instance on the data for you and you can then select a set of topics of interest. Once
    this is done, you can apply this selection to a wider range of documents.
    """
    def __init__(self):

        self._assigned_classes = {}
        self.ctm = None
        self.qt = None
        self.topics_num = 0
        self.widget_holder = None

    def train(self, documents,
              language,
              embedding_model,
              topics=10,
              epochs=10,
              contextual_size=768,
              n_words=2000):
        """
        :param documents: list of documents to train the topic model
        :param language: language for stopwords removal
        :param embedding_model: the embedding model used to create the embeddings
        :param topics: number of topics to use to fit the topic model
        :param epochs: number of epochs used to train the model
        :param contextual_size: size of the embeddings generated by the embedding model
        :param n_words: maximum number of words to take into consideration
        """
        self.topics_num = topics
        self._assigned_classes = {k: "other" for k in range(0, self.topics_num)}

        sp = WhiteSpacePreprocessing(documents, language, n_words)
        preprocessed_documents, unpreprocessed_documents, vocab = sp.preprocess()

        self.qt = TopicModelDataPreparation(embedding_model, show_warning=False)
        training_dataset = self.qt.fit(text_for_contextual=unpreprocessed_documents,
                                       text_for_bow=preprocessed_documents)

        self.ctm = ZeroShotTM(bow_size=len(vocab),
                              contextual_size=contextual_size,
                              n_components=topics,
                              num_epochs=epochs)

        self.ctm.fit(training_dataset)  # run the model

    def get_word_classes(self) -> list:
        return self.ctm.get_topic_lists(5)

    def pretty_print_word_classes(self):
        return "\n".join(str(a) + "\t" + ", ".join(b) for a, b in enumerate(self.get_word_classes()))

    @property
    def assigned_classes(self):
        return self._assigned_classes

    @assigned_classes.setter
    def assigned_classes(self, classes):
        """
        :param classes: a dictionary with the manually mapped topics to the classes e.g., {0 : "nature", 1 : "news"}
        """
        self._assigned_classes = {k: "other" for k in range(0, self.topics_num)}
        self._assigned_classes.update(classes)

    def predict(self, texts):
        """
        :param texts: a list of texts to be classified
        """

        if set(self._assigned_classes.values()) == set("other"):
            raise Exception("Only ``other'' classes are present, did you assign the topics to the assigned_class "
                            "property?")

        data = self.qt.transform(texts)
        topic_ids = np.argmax(self.ctm.get_doc_topic_distribution(data), axis=1)

        return [self._assigned_classes[k] for k in topic_ids]

    def save(self, path):
        """
        :param path:  path to the file to save
        """
        with open(path, "wb") as filino:
            pickle.dump(self, filino)

    @classmethod
    def load(cls, path):
        """
        :param path: path to the file to load
        """
        with open(path, "rb") as filino:
            return pickle.load(filino)

    def widget_annotation(self):
        """
        Displays a widget that can be used to define the mapping between the topics and the labels
        """
        style = {'description_width': 'initial'}
        self.widget_holder = []
        for idx, topic in enumerate(self.ctm.get_topic_lists()):
            description = str(idx) + " -  " + ", ".join(topic)
            a = widgets.Text(value='',
                             placeholder='Topic',
                             description=description,
                             display='flex',
                             flex_flow='column',
                             align_items='stretch',
                             disabled=False, layout={'width': 'max-content', }, style=style)
            self.widget_holder.append(a)
            display(a)

        button = widgets.Button(description="Save")
        button.style.button_color = 'lightgreen'
        display(button)

        def on_button_clicked(b):
            """
            saves the assigned classes
            """
            self._assigned_classes = {k: "other" for k in range(0, self.topics_num)}
            for idx in range(0, self.topics_num):
                if self.widget_holder[idx].value != "":
                    self._assigned_classes[idx] = self.widget_holder[idx].value

        button.on_click(on_button_clicked)








