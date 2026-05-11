def command_not_found_en(data):

    command = data["command"]
    suggestions = data["suggestions"]

    msg = f'Command "{command}" not found'

    if suggestions:

        if len(suggestions) == 1:
            msg += f"\n\nDid you mean " f'"{suggestions[0]}"?'

        else:
            joined = "\n".join(f"  {x}" for x in suggestions)

            msg += "\n\nDid you mean:\n\n" f"{joined}"

    return msg
