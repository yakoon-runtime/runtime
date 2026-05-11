def command_not_found_de(data):

    command = data["command"]
    suggestions = data["suggestions"]

    msg = f'Befehl "{command}" wurde nicht gefunden'
    if suggestions:

        if len(suggestions) == 1:
            msg += f"\n\nMeintest du " f'"{suggestions[0]}"?'

        else:
            joined = "\n".join(f"  {x}" for x in suggestions)

            msg += "\n\nMeintest du:\n\n" f"{joined}"

    return msg
