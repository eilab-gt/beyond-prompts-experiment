from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req

from CreativeWand.Utils.UniqueSentences.UniqueSentences import HighlighterInterface
from StorytellingDomain.Application.Instances.CreativeContext.StoryCreativeContext import StoryContextQuery


class HighlighterComm(BaseCommunication):
    """
    (re)Generate using information gathered.
    """

    def __init__(self):
        super(HighlighterComm, self).__init__()
        self.description = "Point out a sentence that stands out in the story for further exploration."

    def can_activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        text = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="get_document"))
        return len("".join(text)) > 0

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        text = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="get_document"))
        # outlier = HighlighterInterface.highlight_with_embeddings(text)
        exp_manager.frontend.send_information(Req("Loading..."))
        outlier, word = HighlighterInterface.highlight_with_entities(text)
        exp_manager.frontend.send_information(Req("Sentence [" + str(
            outlier) + "] stands out the most from the rest of the story in terms of content because of the word '" + word + ".' Maybe edit it or elaborate on it further!"))

        return True
