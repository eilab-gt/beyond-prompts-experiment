"""
StoryCreativeContext.py

This file contains interface to connect with the story generator.
"""

from StorytellingDomain.Application.Utils.APICalls import default_connection_profile, call_generation_interface, \
    call_carp_interface
from StorytellingDomain.Application.Utils.StorySketch import StorySketchManager
from CreativeWand.Framework.CreativeContext.BaseCreativeContext import BaseCreativeContext, ContextQuery


class StoryContextQuery(ContextQuery):
    """
    Context query specific to story creative context.
    """

    def __init__(self,
                 prompt: str = None,
                 q_type: object = None,
                 content: object = None,
                 description: str = None,
                 range_start=0,
                 range_end=0):
        """
        Create a new story context query.
        :param range_start: start of range to apply this query to
        :param q_type: type of this query.
        :param range_end: end of range to apply this query to
        :param content: Topic to be used, or exact sentence.
        :param description:
        """
        super(StoryContextQuery, self).__init__()

        # Defines range to apply this query to
        self.range_start = range_start
        self.range_end = range_end

        # Topic to be used
        self.type = q_type
        self.content = content

        self.prompt = prompt

        # Additional messages (human readable, for debugging)
        self.description = description


class StoryCreativeContext(BaseCreativeContext):
    """
    Story generator context.
    """

    def __init__(self,
                 sentence_count=10,
                 initial_prompt="Story for kids: Once upon a time, ",
                 suggested_topics=None,
                 api_profile=None,
                 ):
        """
        Initialize this story generator.
        :param sentence_count: Count of sentence to be generated per each story.
        """
        super(StoryCreativeContext, self).__init__()

        if suggested_topics is None:
            self.suggested_topics = ["Business", "Science", "World", "Sports"]
        else:
            self.suggested_topics = suggested_topics
        self.gaussian_var = 1

        if api_profile is None:
            self.gen_api_profile = default_connection_profile
            self.api_profile = {}
        else:
            self.api_profile = api_profile
            self.gen_api_profile = api_profile["gen"]

        """
        Internal variables for interpreting sketches.
        """

        self.sentence_count = sentence_count
        """
        Count of sentence to be generated per each story.
        """

        self.document = []
        self.freeze_mask = [False] * self.sentence_count
        """
        Generated sentences cached. Can be invalidated.
        """
        self.reset_document()

        self.initial_prompt = initial_prompt
        self.bad_generation_keyword = ["{","}","_","(",")","[","]"]
        """
        Initial prompt used in the story generation routine (generate()).
        """

        # Internal switch used to indicate whether we need to regenerate,
        # because the parameters used to generate story had changed.
        self.should_regenerate = True

        # Information we need to collect to generate sentences for this context
        # self.prompt = "Prompt stub"
        self.topic_weight = {}

        self.sketch_manager = StorySketchManager(sentence_count=self.sentence_count, gaussian_var=self.gaussian_var)

    @property
    def document(self):
        return self.get_state("document")

    @document.setter
    def document(self, value):
        self.set_state("document", value)

    @property
    def freeze_mask(self):
        return self.get_state("freeze_mask")

    @freeze_mask.setter
    def freeze_mask(self, value):
        self.set_state("freeze_mask", value)

    @property
    def topic_weight(self):
        return self.get_state("topic_weight")

    @topic_weight.setter
    def topic_weight(self, value):
        self.set_state("topic_weight", value)

    def execute_query(self, query: StoryContextQuery) -> object:
        """
        Execute a query so as to update internal information,
        :param query: Query.
        :return: Query result.
        """
        if type(query) is not StoryContextQuery:
            raise RuntimeError("Query is %s, not StoryContextQuery" % str(type(query)))
        if query.type == "sketch":
            self.apply_sketches(
                start=query.range_start,
                end=query.range_end,
                topic=str(query.content),
            )
            self.should_regenerate = True
            return None
        elif query.type == "remove_sketch":
            self.remove_sketches(
                start=query.range_start,
                end=query.range_end,
                topic=str(query.content),
            )
            self.should_regenerate = True
            return None
        elif query.type == "reset_area":
            self.reset_area(
                start=query.range_start,
                end=query.range_end,
                params=query.content,
            )
        elif query.type == "topic_weights":
            return self.get_all_topic_weights()
        elif query.type == "set_freeze_after":
            start = query.range_start
            self.should_regenerate = True
            return self.set_freeze_mask(start)
        elif query.type == "generated_contents":
            return self.get_generated_content()
        elif query.type == "generate_step_by_step":
            return self.generate_step_by_step()
        elif query.type == "generate_one":
            return self.generate_single_sentence(
                prompt=query.content["prompt"],
                topics=query.content["topics"],
            )
        elif query.type == "force_one":
            return self.force_one_sentence(
                sentence=query.content["sentence"],
                index=query.content["index"],
            )
        elif query.type == "get_document":
            return self.document
        elif query.type == "get_all_sketches":
            return self.sketch_manager.get_all_sketches()
        elif query.type == "get_should_regenerate":
            return self.should_regenerate
        elif query.type == "reset_should_regenerate":
            self.should_regenerate = True
            return None
        elif query.type == "carp":
            if query.content is None:
                # type 2
                return self.get_carp_scores()
            else:
                return self.get_carp_suggestions(
                    critics=query.content,
                )
        elif query.type == "carp_highlight":
            return self.get_carp_scores(reviews=query.content, threshold=0)
        elif query.type == "get_document_filled":
            return self.is_document_filled()

    def set_freeze_mask(self, start):
        """
        Set the "freeze mask" for the generation.
        After this function is called all sentence up to and including sentence [start] are set to freezed
        so that generation does not touch them anymore.
        :param start: start point (included) to set freeze.
        :return: Whether the operation is successful.
        """
        self.freeze_mask = [False] * self.sentence_count
        if start in range(self.sentence_count - 1):
            for idx in range(start + 1):
                self.freeze_mask[idx] = True
            return True
        else:
            print("Freeze mask resetted.")
            return False

    def get_generated_content(self, report_progress: bool = False) -> object:
        """
        Get generated sentences, using the info we already have.
        If no cache is available, we will generate fresh.
        If cache is still valid we just return the cache.
        :param report_progress: Whether to report to frontend the new sentence just generated.
        :return: Generated sentences.
        """
        next_sentence = self.initial_prompt
        if self.should_regenerate:
            old_document = self.document
            # old_document_exists = (len(old_document) == self.sentence_count)
            self.reset_document()
            self.topic_weight = self.sketch_manager.generate_weights()
            for index in range(self.sentence_count):
                self.generate_one_in_story(index)
            self.should_regenerate = False
        return self.document

    def generate_step_by_step(self):
        """
        Generate the next sentence up for generation.
        """
        next_step = self.get_state("gen_next_step")
        if next_step is None:
            # Just starting
            result = self.generate_one_in_story(0)
            self.set_state("gen_next_step",1)
            return {"done":False,"index":0,"sentence":result}
        elif next_step == self.sentence_count:
            self.set_state("gen_next_step",None)
            return {"done":True,"index":next_step,"sentence":None}
        else:
            result = self.generate_one_in_story(next_step)
            self.set_state("gen_next_step",next_step + 1)
            return {"done":False,"index":next_step,"sentence":result}


    def generate_one_in_story(self, index, max_horizon = 2):
        """
        Generate a single sentence in a story.
        :param index: current index this helper is working on.
        :param max_horizon: maximum previous sentences to append.
        """
        old_document = self.document
        old_document_exists = (len(old_document) == self.sentence_count)
        # Compose topic list for each index position of the story.
        topic_this_sentence = {}
        for key, value in self.topic_weight.items():
            topic_this_sentence[key] = value[index]
        total_weight_this_sentence = sum(topic_this_sentence.values())
        for key, value in topic_this_sentence.items():
            if total_weight_this_sentence > 0:
                normalized_value = value / total_weight_this_sentence
                # Filtering weights that are too small - They do not really change the sentence but incur computation.
                if normalized_value < 0.01 / self.sentence_count:
                    normalized_value = 0
                topic_this_sentence[key] = normalized_value
        # Remove all keys that has weight = 0
        topic_this_sentence = {k: v for k, v in topic_this_sentence.items() if v > 0}
        # print("DEBUG: %s"%topic_this_sentence)
        # Attach one previous sentence (if we have at least two sentences) as the context (from original P&B work)

        def get_previous(idx):
            """
            Get a previous sentence in the document. If not exist, return "".
            :param idx: index of *current* sentence position.
            """
            if idx in range(len(self.document)):
                return self.document[idx]
            else:
                return ""

        prompt = f"{self.initial_prompt}"
        for delta_idx in range(max_horizon):
            # becasue delta_idx is from 0 to max_horizon-1 we need to subtract one extra.
            prompt = f"{prompt} {get_previous(index-delta_idx-1)}"

        # if index >= 2:
        #     prompt = "Here is a story from a story book for children. %s %s " % (
        #         self.document[index - 2], self.document[index - 1])
        #     # prompt = "Continue this story: %s" % (self.document[index - 1])
        # elif index == 1:
        #     prompt = "Here is a story from a story book for children. %s " % self.document[
        #         0]  # Add the "0th" prompt back in
        # else:
        #     prompt = next_sentence  # Do nothing, use the last sentence / prompt.

        # If sentence is frozen masked we do not get the next sentence, instead take the one we have
        if not (old_document_exists and self.freeze_mask[index]):
            for i in range(5): #max 5 attempts
                next_sentence = call_generation_interface(prompt, topic=topic_this_sentence,
                                                          connection_profile=self.gen_api_profile)
                for item in self.bad_generation_keyword:
                    if item in next_sentence:
                        print(f"Found a bad generation: {next_sentence}. Regenerating...")
                        continue
                break
            self.document[index] = next_sentence
            return next_sentence
        else:
            self.document[index] = old_document[index]
            return None

    def generate_single_sentence(self, prompt, topics):
        """
        Generate a single sentence based on the prompt and topic(s) supplied.
        This function does not affect the context in any way.
        :param prompt: Prompt to continue on.
        :param topics: Topic weights.
        :return: Generated sentence.
        """
        next_sentence = call_generation_interface(prompt, topic=topics, connection_profile=self.gen_api_profile)
        return next_sentence

    def reset_document(self):
        """
        Reset document so that it contains nothing.
        :return: None.
        """
        self.document = [""] * self.sentence_count

    def force_one_sentence(self, sentence, index):
        """
        Override a sentence with the given "sentence" parameter.
        :param index: Which location of the document is to override.
        :param sentence: sentence to override.
        :return: None
        """
        self.document[index] = sentence

    # region internals

    def apply_sketches(self, start: int, end: int, topic: str) -> None:
        """
        Apply a sketch to the topic weights.
        :param start: Start for this sketch.
        :param end: end for this sketch.
        :param topic: topic related to this sketch.
        :return: None.
        """
        self.should_regenerate = True
        self.sketch_manager.append(topic=topic, start=start, end=end)

    def remove_sketches(self, start: int, end: int, topic: str) -> None:
        """
        Remove a sketch to the topic weights.
        :param start: Start for this sketch.
        :param end: end for this sketch.
        :param topic: topic related to this sketch.
        :return: None.
        """
        self.should_regenerate = True
        self.sketch_manager.remove(topic=topic, start=start, end=end)

    def reset_area(self, start: int, end: int, params: object) -> None:
        """
        Reset an area to start fresh, making it free of any control parameters provided before.
        :param start: start point
        :param end: end point
        :param params: reserved.
        :return: None
        """
        print("Resetting area from %s to %s." % (start, end))
        self.should_regenerate = True
        for sketch in self.sketch_manager.get_all_sketches():
            # remove all sketches that overlaps with this area.
            s0 = sketch['start']
            s1 = sketch['end']
            if s0 > end or s1 < start:
                pass  # no change
            else:
                self.sketch_manager.remove(sketch['topic'], s0, s1)
        for i in range(start, end + 1):
            self.freeze_mask[i] = False

    def get_carp_suggestions(self, critics):
        """
        Gives CARP some critics and a story, let it find which line matches best to that story.
        :param critics: list of `str`, each represents a critic review.
        :return: for each `str` in critics, the line in current document that best matches it.
        """
        # print("Requesting CARP...")
        result = call_carp_interface(
            stories=self.document,
            reviews=critics,
            connection_profile=None if 'carp' not in self.api_profile else self.api_profile[
                'carp'],
            version=1,
        )
        return result

    def get_carp_scores(self, reviews=None, threshold=0.2):
        """
        Ask CARP and see whether we have a review that is suitable for one sentence in current document.

        `Threshold` can be used to filter weakly related pairs.
        As "0.3 is the average cosine similarity", here we set default values based on it.

        :param reviews: if not None, used as custom reviews used to call CARP api.
        :param threshold: When higher than this threshold sentence will be included in the return.
        :return:
        """
        print("Requesting CARP v2...")
        if reviews is None:
            reviews_raw = ["This is too dark.", "This is too specific.", "This is too vague."]
        else:
            reviews_raw = reviews
        reviews = {}
        for item in reviews_raw:
            reviews[item] = threshold
        result = call_carp_interface(
            stories=self.document,
            reviews=reviews,
            connection_profile=None if 'carp' not in self.api_profile else self.api_profile[
                'carp'],
            version=2,
        )
        return result

    def get_all_topic_weights(self):
        """
        Get all topic weights.
        :return: topic weights dictionary.
        """
        self.topic_weight = self.sketch_manager.generate_weights()
        return self.topic_weight

    def is_document_filled(self):
        """
        Does document contain anything that can be shown?
        :return: Whether we have generated sentences ready.
        """
        if type(self.document) is not list:
            return False
        else:
            if len(self.document) > 0:
                for line in self.document:
                    if len(line) > 0:
                        return True
            return False

    def is_generation_ready(self):
        """
        Can we start generating things?
        :return: Whether we have enough information to start generating sentences.
        """
        return len(self.topic_weight) > 0

    # endregion

    def get_state_for_checkpoint(self) -> dict:
        self.set_state("sketch_manager_state", self.sketch_manager.get_all_sketches())
        return super().get_state_for_checkpoint()

    def set_state_from_checkpoint(self, state: dict) -> bool:
        result = super(StoryCreativeContext, self).set_state_from_checkpoint(state)
        if not result: return False

        # Now we rebuild the sketch manager
        sketch_manager_state = self.get_state("sketch_manager_state")
        self.sketch_manager = StorySketchManager(list_of_sketches=sketch_manager_state)

        # Just in case, reset this flag
        self.should_regenerate = True
        return True


if __name__ == '__main__':
    o = StoryCreativeContext()
    o.document = ["It's a great day.", "I'm working in the office.", "I won a jackpot!"]
    o.get_carp_suggestions()
    o.get_carp_scores(threshold=-10000)
