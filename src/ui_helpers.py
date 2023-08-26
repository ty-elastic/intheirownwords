import re
from pathlib import Path
import streamlit as st

def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()

def highlight_sentence(sentences, i):
    text = "### _\""
    for n, sentence in enumerate(sentences):
        escaped = escape_markdown(sentence)
        if n > 0:
            text = text + " "
        if i == n:
            text = text + ":orange[" + escaped + "]"
        else:
            text = text + escaped
    text = text + "\"_"
    return text

def highlight_passage(context, start, stop):
    text = "### _\""
    escaped = escape_markdown(context[:start])
    text = text + escaped
    escaped = escape_markdown(context[start:stop])
    text = text + ":orange[" + escaped + "]"
    escaped = escape_markdown(context[stop:])
    text = text + escaped
    text = text + "\"_"
    return text

def escape_markdown(text: str, version: int = 1, entity_type: str = None) -> str:
    """
    Helper function to escape telegram markup symbols.

    Args:
        text (:obj:`str`): The text.
        version (:obj:`int` | :obj:`str`): Use to specify the version of telegrams Markdown.
            Either ``1`` or ``2``. Defaults to ``1``.
        entity_type (:obj:`str`, optional): For the entity types ``PRE``, ``CODE`` and the link
            part of ``TEXT_LINKS``, only certain characters need to be escaped in ``MarkdownV2``.
            See the official API documentation for details. Only valid in combination with
            ``version=2``, will be ignored else.
    """
    if int(version) == 1:
        escape_chars = r'_*`['
    elif int(version) == 2:
        if entity_type in ['pre', 'code']:
            escape_chars = r'\`'
        elif entity_type == 'text_link':
            escape_chars = r'\)'
        else:
            escape_chars = r'_*[]()~`>#+-=|{}.!'
    else:
        raise ValueError('Markdown version must be either 1 or 2!')

    text = text.replace("$", "")

    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)
