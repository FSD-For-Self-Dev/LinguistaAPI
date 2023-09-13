def slugify_text_author_fields(self):
    return f'{self.text}-{self.author.id}'
