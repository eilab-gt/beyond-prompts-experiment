"""
InspirationCommunication.py

Communication that sends the user some examples based of their work as further inspiration.

This message displays whenever the user hits enter to "submit" their work.
"""
from typing import List
import re

from CreativeWand.Framework.Communications.BaseCommunication import BaseCommunication
from CreativeWand.Framework.Frontend.BaseFrontEnd import BaseRequest as Req
from StorytellingDomain.Application.Instances.CreativeContext.StoryCreativeContext import StoryContextQuery


class InspirationComm(BaseCommunication):
    def __init__(self):
        super(InspirationComm, self).__init__()
        self.description = "Send some examples as inspiration."

    def can_activate(self) -> bool:
        exp_manager = self.get_experience_manager()
        text = exp_manager.creative_context.execute_query(StoryContextQuery(q_type="get_document"))
        return len("".join(text)) > 0

    def activate(self) -> bool:
        exp_manager = self.get_experience_manager()

        lines = exp_manager.creative_context.execute_query(
            StoryContextQuery(
                q_type="get_document"
            )
        )
        text = ""
        for line in lines:
            text += line + " "

        # count top words in user work minus stop words
        sorted_words = self.get_sorted_topics(text)

        # set up story sketch using user work and then random topic from top words (one sketch for top topic, one for least frequent)
        for i in range(2):
            topic = sorted_words[0] if i == 0 else sorted_words[-1]
            print(topic)
            return
            exp_manager.creative_context.execute_query(
                StoryContextQuery(
                    q_type="sketch",
                    range_start=int(0),
                    range_end=int(9),
                    content=topic,
                    prompt=text
                )
            )

            # get generations
            exp_manager.creative_context.get_generated_content()
            generated_cache = exp_manager.creative_context.document  # generated_cache

            # send to frontend
            if i == 0:
                exp_manager.frontend.send_information(Req("An idea based on what you're NOT writing a lot about:"))
            elif i == 1:
                exp_manager.frontend.send_information(Req("An idea based on what you're writing a lot about:"))
            for item in generated_cache:
                exp_manager.frontend.send_information(Req("%s" % item))

            exp_manager.frontend.send_information(Req("------------"))

    def get_sorted_topics(self, text: str) -> List[str]:
        regex = re.compile('[^a-zA-Z]')
        words = {}
        for word in text.split():
            word = regex.sub('', word)
            if word.lower() not in self.skipWords:
                if word in words:
                    words[word] += 1
                else:
                    words[word] = 1

        sorted_words = sorted(words, key=words.get)
        return sorted_words

    skipWords = set(["a", "able", "about", "above", "abst", "accordance",
                     "according", "accordingly", "across", "act", "actually", "added", "adj",
                     "affected", "affecting", "affects", "after", "afterwards", "again", "against",
                     "ah", "all", "almost", "alone", "along", "already", "also", "although",
                     "always", "am", "among", "amongst", "an", "and", "announce", "another",
                     "any", "anybody", "anyhow", "anymore", "anyone", "anything", "anyway",
                     "anyways", "anywhere", "apparently", "approximately", "are", "aren", "arent",
                     "arise", "around", "as", "aside", "ask", "asking", "at", "auth", "available",
                     "away", "awfully", "b", "back", "be", "became", "because", "become", "becomes",
                     "becoming", "been", "before", "beforehand", "begin", "beginning", "beginnings",
                     "begins", "behind", "being", "believe", "below", "beside", "besides", "between",
                     "beyond", "biol", "both", "brief", "briefly", "but", "by", "c", "ca", "came",
                     "can", "cannot", "cant", "cause", "causes", "certain", "certainly", "co", "com",
                     "come", "comes", "contain", "containing", "contains", "cool", "could", "couldnt", "d",
                     "date", "definitely", "did", "didnt", "different", "do", "does", "doesnt", "doing", "done", "dont",
                     "dont", "down", "downwards", "due", "during", "e", "each", "ed", "edu",
                     "effect", "eg", "eight", "eighty", "either", "else", "elsewhere", "end",
                     "ending", "enough", "especially", "et", "et-al", "etc", "even", "ever", "every",
                     "everybody", "everyone", "everything", "everywhere", "ex", "except", "f", "far",
                     "few", "ff", "fifth", "first", "five", "fix", "followed", "following", "follows",
                     "for", "former", "formerly", "forth", "found", "four", "from", "further",
                     "furthermore", "g", "gave", "get", "gets", "getting", "give", "given",
                     "gives", "giving", "go", "goes", "gone", "got", "gotten", "h", "had",
                     "happens", "hardly", "has", "hasnt", "have", "havent", "having", "he", "hed",
                     "hence", "her", "here", "hereafter", "hereby", "herein", "heres", "hereupon",
                     "hers", "herself", "hes", "hi", "hid", "him", "himself", "his", "hither", "home",
                     "how", "howbeit", "however", "hundred", "i", "id", "ie", "if", "ill", "in", "im",
                     "immediate", "immediately", "importance", "important", "in", "inc", "indeed",
                     "index", "information", "instead", "interesting", "into", "invention", "inward", "is", "isnt",
                     "it", "itd", "itll", "its", "itself", "ive", "j", "just", "k", "keep keeps",
                     "kept", "kg", "km", "know", "known", "knows", "l", "largely", "last", "lately",
                     "later", "latter", "latterly", "least", "less", "lest", "let", "lets", "like",
                     "liked", "likely", "line", "little", "ll", "look", "looking", "looks", "ltd",
                     "m", "made", "mainly", "make", "makes", "many", "may", "maybe", "me", "mean",
                     "means", "meantime", "meanwhile", "merely", "mg", "might", "million", "miss", "ml",
                     "more", "moreover", "most", "mostly", "mr", "mrs", "much", "mug", "must", "my",
                     "myself", "n", "na", "name", "namely", "nay", "nd", "near", "nearly",
                     "necessarily", "necessary", "need", "needs", "neither", "never", "nevertheless",
                     "new", "next", "nine", "ninety", "no", "nobody", "non", "none", "nonetheless",
                     "noone", "nor", "normally", "nos", "not", "noted", "nothing", "now", "nowhere",
                     "o", "obtain", "obtained", "obviously", "of", "off", "often", "oh", "ok", "okay",
                     "old", "omitted", "on", "once", "one", "ones", "only", "onto", "or", "ord", "other",
                     "others", "otherwise", "ought", "our", "ours", "ourselves", "out", "outside", "over",
                     "overall", "owing", "own", "p", "page", "pages", "part", "particular", "particularly",
                     "past", "per", "perhaps", "placed", "please", "plus", "poorly", "possible", "possibly",
                     "potentially", "pp", "predominantly", "present", "previously", "primarily", "probably",
                     "promptly", "proud", "provides", "put", "q", "que", "quickly", "quite", "qv", "r",
                     "ran", "rather", "rd", "re", "readily", "really", "recent", "recently", "ref", "refs",
                     "regarding", "regardless", "regards", "related", "relatively", "research", "respectively",
                     "resulted", "resulting", "results", "right", "run", "s", "said", "same", "saw", "say",
                     "saying", "says", "sec", "section", "see", "seeing", "seem", "seemed", "seeming", "seems",
                     "seen", "self", "selves", "sent", "seven", "several", "shall", "she", "shed", "shell",
                     "shes", "should", "shouldnt", "show", "showed", "shown", "showns", "shows",
                     "significant", "significantly", "similar", "similarly", "since", "six",
                     "slightly", "so", "some", "somebody", "somehow", "someone", "somethan",
                     "something", "sometime", "sometimes", "somewhat", "somewhere", "soon", "sorry",
                     "specifically", "specified", "specify", "specifying", "still", "stop", "strongly",
                     "sub", "substantially", "successfully", "such", "sufficiently", "suggest", "sup",
                     "sure", "take", "taken", "taking", "tell", "tends", "th", "than", "thank",
                     "thanks", "thanx", "that", "thatll", "thats", "thatve", "the", "their",
                     "theirs", "them", "themselves", "then", "thence", "there", "thereafter",
                     "thereby", "thered", "therefore", "therein", "therell", "thereof", "therere",
                     "theres", "thereto", "thereupon", "thereve", "these", "they", "theyd", "theyll",
                     "theyre", "theyve", "think", "this", "those", "thou", "though", "thoughh",
                     "thousand", "throug", "through", "throughout", "thru", "thus", "til", "tip",
                     "to", "together", "too", "took", "toward", "towards", "tried", "tries", "truly",
                     "try", "trying", "ts", "twice", "two", "u", "un", "under", "unfortunately",
                     "unless", "unlike", "unlikely", "until", "unto", "up", "upon", "ups", "us",
                     "use", "used", "useful", "usefully", "usefulness", "uses", "using", "usually",
                     "v", "value", "various", "ve", "very", "via", "viz", "vol", "vols", "vs", "w",
                     "want", "wants", "was", "wasnt", "way", "we", "wed", "welcome", "well", "went",
                     "were", "werent", "weve", "what", "whatever", "whatll", "whats", "when", "whence",
                     "whenever", "where", "whereafter", "whereas", "whereby", "wherein", "wheres",
                     "whereupon", "wherever", "whether", "which", "while", "whim", "whither", "who",
                     "whod", "whoever", "whole", "wholl", "whom", "whomever", "whos", "whose", "why",
                     "widely", "willing", "wish", "with", "within", "without", "wont", "words",
                     "world", "would", "wouldnt", "www", "x", "y", "yeah", "yes", "yet", "you", "youd",
                     "youll", "your", "youre", "yours", "yourself", "yourselves", "youve", "z", "zero"])
