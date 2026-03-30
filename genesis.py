from openai import OpenAI

client = OpenAI()

class GenesisAI:
    def __init__(self):
        self.identity = """
        You are GENESISAI, the operating intelligence behind Prosperous Collection.
        You prioritize discipline, quality over quantity, and brand doctrine.
        """

    def think(self, prompt):
        response = client.chat.completions.create(
            model="gpt-5.3",
            messages=[
                {"role": "system", "content": self.identity},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    