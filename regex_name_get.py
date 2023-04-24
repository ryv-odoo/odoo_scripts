


# [(batch.id, f'{batch.name} ({state_values.get(batch.state)})') for batch in self]

for batch in self:
    batch.display_name = f'{batch.name} ({state_values.get(batch.state)})'

list_comprehension = r"( +)(?:return)?[\s\n]*\[[\s\n]*\([\s\n]*.+,[\s\n]*(.+)[\s\n]*\)[\s\n]*for[\s\n]*(\w+)[\s\n]*in[\s\n]*self\]"
list_comprehension_into = r"""$1for $3 in self:
\n$1    $3.display_name = $2"
"""