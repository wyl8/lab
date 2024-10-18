
class Card1Agent:
    def __init__(self, prompt_file = "card1_prompt.md"):
        print("Init Card1Agent")

        with open(prompt_file, "r", encoding='utf-8') as f:
            self.card1_prompt_template = f.read()

    
    def make_prompt(self,query):
        # 把json数据拼成prompt文本
        card_prompt = self.card1_prompt_template.format(
            user_question=query
            )
        
        # print("card_prompt:\n", card_prompt)

        return card_prompt
 