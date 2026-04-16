from .block import (
    map_actions,
    map_fields,
    map_heading,
    map_kv,
    map_list,
    map_paragraph,
    map_rule,
    map_section,
    map_spacer,
)
from .core import Mapper
from .inline import (
    map_br,
    map_cmd,
    map_code,
    map_em,
    map_link,
    map_mark,
    map_select,
    map_strong,
    map_underline,
)


def create_mapper() -> Mapper:
    mapper = Mapper()

    # -------- INLINE --------
    mapper.register_inline("cmd", map_cmd)
    mapper.register_inline("code", map_code)
    mapper.register_inline("link", map_link)
    mapper.register_inline("select", map_select)
    mapper.register_inline("em", map_em)
    mapper.register_inline("strong", map_strong)
    mapper.register_inline("u", map_underline)
    mapper.register_inline("mark", map_mark)
    mapper.register_inline("br", map_br)

    # -------- BLOCKS --------
    mapper.register_block("kv", map_kv)
    mapper.register_block("list", map_list)
    mapper.register_block("rule", map_rule)
    mapper.register_block("spacer", map_spacer)
    mapper.register_block("actions", map_actions)
    mapper.register_block("fields", map_fields)
    mapper.register_block("p", map_paragraph)
    mapper.register_block("h1", map_heading(1))
    mapper.register_block("h2", map_heading(2))
    mapper.register_block("h3", map_heading(3))
    mapper.register_block("section", map_section)

    return mapper
