from .blocks import map_actions, map_fields, map_kv, map_list, map_rule, map_spacer
from .core import Mapper
from .inline import map_cmd, map_code, map_em, map_link, map_select, map_strong


def create_mapper() -> Mapper:
    mapper = Mapper()

    # -------- INLINE --------
    mapper.register_inline("cmd", map_cmd)
    mapper.register_inline("code", map_code)
    mapper.register_inline("link", map_link)
    mapper.register_inline("select", map_select)
    mapper.register_inline("em", map_em)
    mapper.register_inline("strong", map_strong)

    # -------- BLOCKS --------
    mapper.register_block("kv", map_kv)
    mapper.register_block("list", map_list)
    mapper.register_block("rule", map_rule)
    mapper.register_block("spacer", map_spacer)
    mapper.register_block("actions", map_actions)
    mapper.register_block("fields", map_fields)

    return mapper
