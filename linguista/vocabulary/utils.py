def slugify_text_author_fields(self):
    without_spaces = self.text.replace(' ', '-')
    return f'{without_spaces}-{self.author.id}'
