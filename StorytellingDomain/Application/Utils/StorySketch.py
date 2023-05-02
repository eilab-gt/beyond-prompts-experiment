"""
StorySketch.py

This file contains helper functions to assist StoryCreativeContext to manage
sketches.
"""
from abc import ABCMeta, abstractmethod

from scipy.stats import norm


class SketchManagerBase(metaclass=ABCMeta):
    def __init__(self, sentence_count=10, gaussian_var=1, list_of_sketches=None):
        """
        Initial this sketch manager with no sketches preset.
        :param sentence_count: sentence count used when generating control weights.
        :param gaussian_var: larger means weights are more centered (higher peak strength).
        :param list_of_sketches: if not None, use these sketches to init this class.
        """
        # Cache for weights calculated last time. No guarantee that it's newest.
        self.topic_weight = None

        self.gaussian_var = gaussian_var
        """
        Internal hyperparameter.
        """

        self.sentence_count = sentence_count
        if list_of_sketches is None:
            self.list_of_sketches = []
        else:
            self.list_of_sketches = list_of_sketches

    def reset_sketches(self):
        """
        Remove all sketches.
        :return: None
        """
        self.list_of_sketches = []

    @abstractmethod
    def append(self, topic, start, end):
        """
        Append a sketch to the end of list of sketches.
        :param topic: topic of the sketch.
        :param start: starting point for the sketch.
        :param end: end point of the sketch.
        :return: whether operation is successful.
        """
        pass

    @abstractmethod
    def remove(self, topic, start, end):
        """
        Remove a sketch fitting all of these criteria.
        :param topic: topic of the sketch.
        :param start: starting point for the sketch.
        :param end: end point of the sketch.
        :return: Whether operation is successful.
        """
        pass

    @abstractmethod
    def get_all_sketches(self):
        """
        Get all sketches.
        :return: All sketches saved in this sketch manager.
        """
        pass

    @abstractmethod
    def generate_weights(self):
        """
        Generate control weight array based on the sketches in this manager.
        :return: just-calculated topic weights.
        """
        pass


class StorySketchManager(SketchManagerBase):

    def remove(self, topic, start, end):
        # This will always success or fail with an exception from index().
        idx = self.index(topic, start, end)
        del self.list_of_sketches[idx]

    def append(self, topic, start, end):
        """
        Append a sketch to the end of list of sketches.
        :param topic: topic of the sketch.
        :param start: starting point for the sketch.
        :param end: end point of the sketch.
        :return: whether operation is successful.
        """

        self.list_of_sketches.append(
            {
                "topic": topic,
                "start": start,
                "end": end,
            }
        )
        return True

    def get_all_sketches(self):
        """
        Get all sketches.
        :return: All sketches saved in this sketch manager.
        """
        return self.list_of_sketches

    def index(self, topic=None, start=None, end=None):
        """
        Find the first item in the sketch list meeting conditions.
        If not found raise ValueError.
        :param topic: topic to match (can be None)
        :param start: start position to match (can be None)
        :param end: end position to match (can be None)
        :return: index of item.
        """
        for index in range(len(self.list_of_sketches)):
            item = self.list_of_sketches[index]
            if topic is None or topic == item['topic']:
                if start is None or start == item['start']:
                    if end is None or end == item['end']:
                        return index
        raise ValueError("Sketch not found with given condition.")

    def __getitem__(self, index):
        """
        Get sketch by index.
        :param index: index
        :return: sketch in list_of_sketches.
        """
        return self.list_of_sketches[index]

    def change_sketch_at_index(self, index, topic, start, end):
        """
        Change a given sketch at given index.
        :param index: index of existing sketch (IndexError if not exist)
        :param topic: topic to assign.
        :param start: start point to assign.
        :param end: end point to assign.
        :return: None
        """
        if index not in range(len(self.list_of_sketches)):
            raise IndexError("change_sketch_at_index() encountered out of bounds index.")
        self.list_of_sketches[index] = {
            "topic": topic, "start": start, "end": end,
        }

    def generate_weights(self):
        """
        Generate control weight array based on the sketches in this manager.
        :return: just-calculated topic weights.
        """
        self.topic_weight = {}
        for item in self.list_of_sketches:
            topic = item['topic']
            start = item['start']
            end = item['end']
            if topic not in self.topic_weight:
                self.topic_weight[topic] = [0] * self.sentence_count
            epsilon = 1e-6
            end += epsilon  # so that we support single sentence "areas"
            center = (start + end) / 2
            total_summary_values = 0
            for i in range(self.sentence_count):
                # Convert absolute position to where we look into in PDF
                relative_pdf_pos = 1.0 * (i - center) / (end - center)  # end = 1, start = -1
                pdf_position = self.gaussian_var * relative_pdf_pos
                pdf_value = norm.pdf(pdf_position)
                # Apply weights
                self.topic_weight[topic][i] += pdf_value
                total_summary_values += self.topic_weight[topic][i]
            for i in range(self.sentence_count):
                # Normalize it if multiple summary of the same type is provided.
                self.topic_weight[topic][i] /= total_summary_values
        return self.topic_weight
